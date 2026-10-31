"""Bounded parallel Spotter supervision over Blupe's measured-feedback loop.

This is an embodiment port, not a benchmark reproduction. Upstream Spotter's
simulator and its privileged scoring/reset paths are never used on hardware.
"""
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import math
import time

from remote_yam.providers import PolicyComplete
from remote_yam.robocurve_trajectory import NAMES


def number(value):
    return type(value) in (float, int) and math.isfinite(value)


def validate_plan(result):
    steps = result.get('steps')
    if not isinstance(steps, list) or not 1 <= len(steps) <= 8:
        raise ValueError('Spotter repair needs 1–8 steps')
    shapes = {'policy': {}, 'nudge': {'dxyz': 3}, 'lift': {'dz': 1},
              'move_to': {'xyz': 3}, 'rotate': {'yaw': 1}, 'gripper': {'value': 1}}
    for index, step in enumerate(steps):
        if not isinstance(step, dict) or step.get('op') not in shapes:
            raise ValueError('Unknown Spotter repair operation')
        op = step['op']
        fields = shapes[op]
        expected = {'op'} | (set() if op == 'policy' else {'arm'}) | set(fields)
        if set(step) != expected or (op != 'policy' and step.get('arm') not in ('left', 'right')):
            raise ValueError('Spotter repair must explicitly name its arm and fields')
        if op == 'policy' and index != len(steps) - 1:
            raise ValueError('Policy hand-back must end a repair segment')
        for key, count in fields.items():
            values = step[key] if count > 1 else [step[key]]
            if not isinstance(values, list) or len(values) != count or not all(number(v) for v in values):
                raise ValueError('Spotter repair values must be finite numbers')
        if op == 'gripper' and not 0 <= step['value'] <= 1:
            raise ValueError('Spotter gripper must be normalized')
    if not isinstance(result.get('expectation'), str) or not result['expectation'].strip():
        raise ValueError('Spotter repair must state its visual expectation')
    return deepcopy(steps)


class FixedFrames:
    def __init__(self, frames): self.frames = frames
    def capture_for_policy(self, *args, **kwargs): return list(self.frames)


class SpotterAdapter:
    provider_name = 'spotter'
    supports_runtime_steering = False

    def __init__(self, base, supervisor, geometry, *, robot_id, camera_source,
                 max_lead=2, history_windows=10, max_interventions=8, max_plan_rounds=3,
                 preparation=None, grounding=None):
        if type(max_lead) is not int or max_lead < 1 or not 2 <= history_windows <= 20:
            raise ValueError('Invalid Spotter supervision window configuration')
        self.base, self.supervisor, self.geometry = base, supervisor, geometry
        self.model = 'spotter/' + base.model
        self.robot_id, self.camera_source = robot_id, camera_source
        self.max_lead, self.max_interventions = max_lead, max_interventions
        self.max_plan_rounds, self.preparation = max_plan_rounds, preparation
        self.grounding = grounding
        self.history = deque(maxlen=history_windows)
        self.cancelled = lambda: False
        self.refresh_observation = None
        self.interaction_sink = lambda *args, **kwargs: None
        self._pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix='spotter-supervisor')
        self._future = None
        self._checked = 0
        self._chunks = 0
        self._last_kind = None
        self._pending_packet = self._preceding_packet = None
        self._repair = deque()
        self._repair_context = None
        self._verify = False
        self._post_policy_expectation = None
        self._execution_failure = None
        self._interventions = 0
        self._rounds = 0
        self._repair_plans = deque(maxlen=max_plan_rounds)
        self._episode = None
        self._closed = False
        self._prepared = False

    def public_config(self):
        return {'provider': self.provider_name, 'model': self.model,
                'base_model': self.base.model, 'supervisor_model': self.supervisor.model,
                'max_lead_windows': self.max_lead, 'interventions': self._interventions,
                'policy_chunks': self._chunks, 'checked_through': self._checked,
                'warmup': 'ready' if self._prepared else 'warming',
                'phase': 'repair' if self._repair_context else 'policy'}

    def _event(self, phase, note, **details):
        self.interaction_sink('model_progress', 'Spotter ' + phase + ' · ' + str(note)[:500],
                              progress_type='status', spotter_phase=phase,
                              policy_chunks=self._chunks, **details)

    def prepare_before_session(self, prompt):
        self._connect_base()
        self._event('prepare', 'Preparing Spotter before joining the robot queue')
        self.base.start_preparation(self.base.cancelled)
        self.supervisor.ready(self.base.cancelled)
        if self.preparation: self.preparation()
        prepare = getattr(self.base, 'prepare_before_session', None)
        if callable(prepare): prepare(prompt)
        self._check_cancelled()
        self._prepared = True

    def _connect_base(self):
        self.base.cancelled = lambda: self._closed or self.cancelled()
        self.base.interaction_sink = self.interaction_sink
        if hasattr(self.base, 'refresh_observation'):
            self.base.refresh_observation = self.refresh_observation

    def prepare_after_lease(self, cancelled):
        self.cancelled = cancelled
        self._connect_base()
        prepare = getattr(self.base, 'prepare_after_lease', None)
        if callable(prepare): prepare(self.base.cancelled)

    def _check_cancelled(self):
        if self.cancelled() or self._closed:
            raise RuntimeError('Spotter run cancelled')

    def _snapshot(self, observation):
        if observation.get('robot_id', observation.get('jetson_id')) != self.robot_id:
            raise ValueError('Spotter observation belongs to another robot')
        if observation.get('settled') is not True:
            raise ValueError('Spotter requires settled measured feedback')
        episode = observation.get('episode_id')
        if self._episode is not None and episode != self._episode:
            raise ValueError('Spotter cannot reuse supervision across episodes')
        self._episode = episode
        _, state, _ = self.geometry.observe(observation)
        frames = self.camera_source.capture_for_policy(observation, cancelled=self.cancelled)
        if {f.name for f in frames} != {'top', 'left', 'right'} or len(frames) != 3:
            raise ValueError('Spotter requires the three configured YAM cameras')
        measured = {k: deepcopy(observation.get(k)) for k in ('observed_at', 'step_id',
                    'left_joints_deg', 'right_joints_deg', 'left_gripper', 'right_gripper')}
        window = {'chunk': self._chunks, 'measured': measured,
                  'cartesian': dict(zip(NAMES, map(float, state))), 'frames': tuple(frames),
                  'preceding_packet': deepcopy(self._preceding_packet)}
        self.history.append(window)
        return window

    def _review(self, prompt, history):
        screen = self.supervisor.screen(prompt, history)
        self._event('screen', screen.get('why', 'Window screened'), flagged=screen['flag'], risk=screen['risk'])
        if not screen['flag']:
            return {'verdict': 'pass', 'why': screen.get('why', '')}
        self._check_cancelled()
        verdict = self.supervisor.judge(prompt, history, {'screener': screen})
        self._event('judge', verdict.get('why', 'Suspicious window reviewed'), verdict=verdict['verdict'])
        return verdict

    def _start_review(self, prompt):
        self._future = (self._chunks, self._pool.submit(self._review, prompt, list(self.history)))

    def _take_review(self, wait=False):
        if not self._future: return None
        chunk, future = self._future
        while wait and not future.done():
            self._check_cancelled()
            time.sleep(.05)
        if not future.done(): return None
        self._future = None
        result = future.result()  # A failed supervisor never becomes an unwatched pass.
        self._checked = chunk
        return result

    def _plan(self, prompt, context):
        self._check_cancelled()
        if self._rounds >= self.max_plan_rounds:
            raise RuntimeError('Spotter repair did not verify within its configured plan budget')
        bounds = {name: [float(lo), float(hi)] for name, lo, hi in zip(NAMES, self.geometry.low, self.geometry.high)}
        history = list(self.history)
        if self.grounding:
            history, measured, points = self.grounding.capture(prompt, history, self.supervisor, self.cancelled)
            context = {**context, 'grounding': measured}
            self._event('grounding', 'Repair targets measured from paired overhead RGB-D', grounding=measured)
        context = {**context, 'bounds': bounds, 'previous_repairs': deepcopy(list(self._repair_plans)),
                   'remaining_plan_rounds': self.max_plan_rounds-self._rounds}
        for attempt in range(2):
            result = self.supervisor.repair(prompt, history, context)
            if self.grounding:
                result = self.grounding.resolve(result, points)
                if getattr(self.grounding, 'last_refresh', None):
                    self._event('grounding', 'Selected surfaces remeasured after planning; scene unchanged',
                                grounding_refresh=self.grounding.last_refresh)
            steps = validate_plan(result)
            if not context.get('failed_policy_handback') or self._restages(steps, history[-1]['cartesian']):
                break
            self._check_cancelled()
            context = {**context, 'planner_feedback':
                'The previous policy handback failed. Actual restaging is required before another '
                'handback: use a measured positional or orientation correction, not only gripper '
                'open/close or an unchanged policy step. No rejected steps were executed.'}
            self._event('repair_validation', context['planner_feedback'])
        else:
            raise RuntimeError('Spotter repair did not propose restaging after a failed policy handback')
        self._check_cancelled()
        self._repair = deque(steps)
        self._repair_context = {'why': str(result.get('why', ''))[:500],
                                'expectation': result['expectation'][:2000], 'steps': deepcopy(steps)}
        self._repair_plans.append({**deepcopy(self._repair_context), 'status': 'planned'})
        intervention = getattr(self.base, 'supervisor_intervention', None)
        if callable(intervention): intervention()
        self._rounds += 1
        self._event('repair', self._repair_context['why'], expectation=self._repair_context['expectation'])

    @staticmethod
    def _restages(steps, current):
        for step in steps:
            op, arm = step['op'], step.get('arm')
            if op == 'nudge' and math.sqrt(sum(v*v for v in step['dxyz'])) >= .01: return True
            if op == 'lift' and abs(step['dz']) >= .01: return True
            if op == 'move_to' and math.sqrt(sum((v-current[arm+'_'+axis])**2
                    for axis, v in zip('xyz', step['xyz']))) >= .01: return True
            if op == 'rotate':
                delta = step['yaw']-current[arm+'_yaw']
                if abs(math.atan2(math.sin(delta), math.cos(delta))) >= .05: return True
        return False

    def _primitive(self, step, observation, first_step_id):
        _, state, _ = self.geometry.observe(observation)
        arm, op = step['arm'], step['op']
        current = dict(zip(NAMES, map(float, state)))
        if op == 'nudge':
            targets = {arm + '_' + axis: current[arm + '_' + axis] + delta for axis, delta in zip('xyz', step['dxyz'])}
        elif op == 'lift': targets = {arm + '_z': current[arm + '_z'] + step['dz']}
        elif op == 'move_to': targets = {arm + '_' + axis: value for axis, value in zip('xyz', step['xyz'])}
        elif op == 'rotate': targets = {arm + '_yaw': step['yaw']}
        else: targets = {arm + '_gripper': step['value']}
        points = self.geometry.build(targets, observation, first_step_id)
        self._last_kind = 'repair'
        self._record_packet(points, operation=op, arm=arm)
        self._verify = op == 'lift' or not self._repair
        self._event('execute', 'Executing Spotter ' + op + ' with the ' + arm + ' arm', operation=op, arm=arm)
        return points

    def build_trajectory(self, prompt, observation, first_step_id):
        self._check_cancelled()
        window = self._snapshot(observation)
        if self._execution_failure:
            context, self._execution_failure = self._execution_failure, None
            self._plan(prompt, context)
        if self._post_policy_expectation and self._last_kind == 'policy':
            context = self._post_policy_expectation
            verdict = self.supervisor.verify(prompt, list(self.history), context)
            self._check_cancelled()
            self._post_policy_expectation = None
            self._event('verify', verdict.get('why', ''), verdict=verdict['verdict'])
            if verdict['verdict'] == 'success': raise PolicyComplete('Spotter visually reports completion')
            if verdict['verdict'] == 'replan':
                self._plan(prompt, {**context, 'verification': verdict, 'failed_policy_handback': True})
        if self._repair_context and self._verify:
            verdict = self.supervisor.verify(prompt, list(self.history), self._repair_context)
            self._check_cancelled()
            self._event('verify', verdict.get('why', ''), verdict=verdict['verdict'])
            self._verify = False
            if verdict['verdict'] == 'success': raise PolicyComplete('Spotter visually reports completion')
            if verdict['verdict'] == 'replan': self._plan(prompt, {**self._repair_context, 'verification': verdict})
        result = self._take_review(wait=bool(self._future and self._chunks - self._checked >= self.max_lead))
        if result and not self._repair_context:
            if result['verdict'] == 'success':
                # An asynchronous success decision must be checked against the newest scene.
                current = self.supervisor.judge(prompt, [window], {'previous_verdict': result})
                self._check_cancelled()
                if current['verdict'] == 'success': raise PolicyComplete('Spotter visually reports completion')
                result = current
            if result['verdict'] == 'intervene':
                if self._interventions >= self.max_interventions:
                    raise RuntimeError('Spotter intervention budget reached')
                self._interventions += 1
                self._rounds = 0
                self._repair_plans.clear()
                self._plan(prompt, {'detected_failure': result, 'replan_from_current_state': True})
        while self._repair:
            step = self._repair.popleft()
            if step['op'] == 'policy':
                self._repair.clear()
                self._post_policy_expectation = self._repair_context
                self._repair_context = None
                self._checked = self._chunks
                if self._repair_plans: self._repair_plans[-1]['status'] = 'handed_back'
                self._event('handoff', 'Returning control to the policy; Spotter keeps watching')
                break
            try:
                return self._primitive(step, observation, first_step_id)
            except ValueError as exc:
                # Replanning happens from fresh feedback, without dispatching a rejected path.
                self._plan(prompt, {**self._repair_context, 'execution_error': str(exc)[:300]})
                continue
        if self._repair_context:
            self._post_policy_expectation = self._repair_context
            self._repair_context = None
            self._checked = self._chunks
            if self._repair_plans: self._repair_plans[-1]['status'] = 'handed_back'
            self._event('handoff', 'Repair segment finished; returning to the policy')
        if self._future is None and self._checked < self._chunks:
            self._start_review(prompt)
        self._check_cancelled()
        self._connect_base()
        # DreamZero consumes a single snapshot. Dream-1 owns its live 5 Hz
        # camera/state history; freezing that source would fabricate its window.
        if hasattr(self.base, '_camera_source'):
            self.base._camera_source = FixedFrames(window['frames'])
        points = self.base.build_trajectory(prompt, observation, first_step_id)
        self._check_cancelled()
        # A confirmed error that arrived during inference takes precedence over this chunk.
        if self._future and self._future[1].done():
            verdict = self._future[1].result()
            if verdict['verdict'] != 'pass':
                # Re-enter from the same unexecuted measured state; the completed future is consumed above.
                return self.build_trajectory(prompt, observation, first_step_id)
        self._last_kind = 'policy'
        self._record_packet(points)
        self._event('policy', 'Policy action chunk ready; Spotter supervises in parallel')
        return points

    def _record_packet(self, points, **context):
        # Requested targets are intent, never proof of contact or task success.
        # Publish them to the next visual window only after controller feedback.
        self._pending_packet = dict(actor=self._last_kind, **context,
            first_step_id=points[0]['step_id'], last_step_id=points[-1]['step_id'],
            target={key: deepcopy(points[-1][key]) for key in
                    ('left_joints_deg', 'right_joints_deg', 'left_gripper', 'right_gripper')
                    if key in points[-1]})

    def _packet_outcome(self, status, waypoint_count, **details):
        if self._pending_packet is not None:
            self._preceding_packet = dict(self._pending_packet, status=status,
                                          waypoint_count=waypoint_count, **details)
            self._pending_packet = None

    def trajectory_completed(self, observation, waypoint_count):
        self._packet_outcome('completed', waypoint_count)
        if self._last_kind == 'policy':
            self._chunks += 1
            completed = getattr(self.base, 'trajectory_completed', None)
            if callable(completed): completed(observation, waypoint_count)

    def trajectory_failed(self, code, message, waypoint_count, *, feedback=None):
        # A failed packet is never a completed policy chunk. Dream discards its
        # pending smoother target and resets before its next fresh prediction.
        if self._last_kind == 'policy':
            failed = getattr(self.base, 'trajectory_failed', None)
            if not callable(failed):
                raise RuntimeError('Spotter base policy cannot recover from failed moves')
            failed(code, message, waypoint_count, feedback=feedback)
        elif self._last_kind == 'repair':
            if self._repair_plans:
                self._repair_plans[-1].update(status='failed', failure_code=code)
            # Do not run the rest of a primitive plan after a partial movement,
            # or treat its expectation as verified. Replan at the next measured
            # snapshot, using the existing finite plan budget.
            previous = self._repair_context
            self._repair.clear()
            self._repair_context = self._post_policy_expectation = None
            self._verify = False
            if self._future:
                self._future[1].cancel()
                self._future = None
            self._checked = self._chunks
            self._execution_failure = dict(replan_from_current_state=True,
                previous_repair=previous, execution_error=dict(code=code,
                    message=str(message)[:300], waypoint_count=waypoint_count))
        else:
            raise RuntimeError('Spotter received failed-move feedback without an active packet')
        self._packet_outcome('failed', waypoint_count, failure_code=code)
        self._event('recovery', 'Move did not reach its target; replanning from measured state',
                    failure_code=code, waypoint_count=waypoint_count)

    def close_transport(self):
        self._closed = True
        if self._future: self._future[1].cancel()
        self._pool.shutdown(wait=False, cancel_futures=True)
        if self.grounding: self.grounding.close()
        close = getattr(self.base, 'close_transport', None)
        if callable(close): close()

    def trajectory_adjusted(self, details):
        if self._pending_packet is not None:
            for key in ('left_joints_deg', 'right_joints_deg', 'left_gripper', 'right_gripper'):
                if key in details:
                    self._pending_packet['target'][key] = deepcopy(details[key])
        adjusted = getattr(self.base, 'trajectory_adjusted', None)
        if self._last_kind == 'policy' and callable(adjusted): adjusted(details)

    def cancel_pending_request(self):
        self.close_transport()
