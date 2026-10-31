from concurrent.futures import Future
import threading
import time
from types import SimpleNamespace

import numpy as np
import pytest

from spotter_yam.policy import SpotterAdapter, validate_plan
from spotter_yam.vlm import object_from_text
from remote_yam.providers import PolicyComplete


def observation(step=0, x=.25, episode='one'):
    return dict(jetson_id='yam-1', episode_id=episode, settled=True,
                observed_at=time.time(), step_id=step, x=x,
                left_joints_deg=[10.] * 6, right_joints_deg=[-10.] * 6,
                left_gripper=.2, right_gripper=.8)


class Geometry:
    low = np.array([-.5] * 14)
    high = np.array([1.] * 14)
    def __init__(self): self.targets = []
    def observe(self, obs):
        return None, np.array([obs['x'], 0, .2, 0, 0, 0, .2] + [.3, 0, .2, 0, 0, 0, .8]), None
    def build(self, targets, obs, step):
        self.targets.append((targets, obs.copy(), step))
        return [dict(step_id=step, left_joints_deg=obs['left_joints_deg'], right_joints_deg=obs['right_joints_deg'])]


class Base:
    model = 'test-dreamzero'
    def __init__(self): self.calls = []
    def build_trajectory(self, prompt, obs, step):
        self.calls.append(obs.copy())
        return [dict(step_id=step, left_joints_deg=obs['left_joints_deg'], right_joints_deg=obs['right_joints_deg'])]


class Supervisor:
    model = 'test-qwen'
    def __init__(self): self.calls = []; self.plans = []
    def screen(self, prompt, history):
        self.calls.append(('screen', history)); return {'flag': False, 'risk': 0, 'why': 'progress'}
    def judge(self, *args): raise AssertionError('Unflagged windows must not call the judge')
    def repair(self, prompt, history, context):
        self.plans.append((history, context))
        return dict(why='re-stage', expectation='hand shifts right', steps=[dict(op='nudge',arm='left',dxyz=[.03,0,0]),dict(op='policy')])
    def verify(self, *args): return dict(verdict='verified', why='object moved with the hand')


@pytest.fixture
def adapter():
    frames = [SimpleNamespace(name=name, jpeg=b'not-used-in-transport-test') for name in ('top','left','right')]
    cameras = SimpleNamespace(capture_for_policy=lambda *a, **k: frames)
    value = SpotterAdapter(Base(), Supervisor(), Geometry(), robot_id='yam-1', camera_source=cameras)
    yield value
    value.close_transport()


def finished(verdict):
    future=Future(); future.set_result(verdict); return future


def test_policy_leads_and_unflagged_screen_does_not_call_judge(adapter):
    adapter.build_trajectory('move the block', observation(), 0)
    assert not adapter.supervisor.calls
    adapter.trajectory_completed(observation(1),1)
    adapter.build_trajectory('move the block', observation(1),1)
    adapter._future[1].result(timeout=2)
    adapter.trajectory_completed(observation(2),1)
    adapter.build_trajectory('move the block', observation(2),2)
    assert len(adapter.base.calls)==3
    assert adapter.supervisor.calls[0][0]=='screen'


def test_repair_uses_current_pose_not_stale_flagged_pose(adapter):
    adapter._chunks=2
    adapter._future=(1,finished(dict(verdict='intervene',why='missed grasp at old pose')))
    points=adapter.build_trajectory('move the block',observation(16,x=.4),16)
    targets, measured, first = adapter.geometry.targets[0]
    assert targets == {'left_x':pytest.approx(.43),'left_y':0,'left_z':.2}
    assert measured['x']==.4 and first==16 and points[0]['step_id']==16
    assert not adapter.base.calls
    assert adapter.supervisor.plans[0][1]['replan_from_current_state'] is True


def test_repair_uses_grounded_history_and_resolves_before_geometry(adapter):
    paired = [dict(frames=(), measured={'observed_at': 101.})]
    calls = []
    adapter.grounding = SimpleNamespace(
        capture=lambda *args: (paired, {'points': {'object': {'left': [.4, 0, .1]}}}, {'object': 1}),
        resolve=lambda result, points: calls.append(points) or {
            'why': 'measured target', 'expectation': 'approach object',
            'steps': [{'op': 'move_to', 'arm': 'left', 'xyz': [.4, 0, .2]}]},
        close=lambda: None)
    adapter._chunks = 2
    adapter._future = (1, finished(dict(verdict='intervene', why='missed grasp')))
    adapter.build_trajectory('move object', observation(16), 16)
    history, context = adapter.supervisor.plans[-1]
    assert history == paired and context['grounding']['points']['object']['left'] == [.4, 0, .1]
    assert calls == [{'object': 1}]
    assert adapter.geometry.targets[-1][0] == {'left_x': .4, 'left_y': 0, 'left_z': .2}


def test_slow_supervisor_holds_at_bound_and_stop_discards_late_result(adapter):
    adapter._chunks=2
    pending=Future(); adapter._future=(1,pending)
    outcome=[]
    def build():
        try:adapter.build_trajectory('move',observation(16),16)
        except Exception as exc:outcome.append(exc)
    thread=threading.Thread(target=build); thread.start()
    time.sleep(.08)
    assert thread.is_alive() and not adapter.base.calls
    adapter.cancelled=lambda:True
    thread.join(2)
    pending.set_result(dict(verdict='intervene',why='late result'))
    assert len(outcome)==1 and 'cancelled' in str(outcome[0])
    assert not adapter.geometry.targets and not adapter.base.calls


def test_failed_supervision_never_becomes_policy_pass(adapter):
    adapter._chunks=2
    future=Future();future.set_exception(RuntimeError('model unavailable'))
    adapter._future=(1,future)
    with pytest.raises(RuntimeError,match='unavailable'):
        adapter.build_trajectory('move',observation(16),16)
    assert not adapter.base.calls and not adapter.geometry.targets


def test_asynchronous_success_rechecked_against_current_scene(adapter):
    adapter._chunks=1
    adapter._future=(1,finished(dict(verdict='success',why='previous scene complete')))
    adapter.supervisor.judge=lambda *args:dict(verdict='pass',why='current scene still needs work')
    adapter.build_trajectory('move',observation(8),8)
    assert len(adapter.base.calls)==1


def test_verified_completion_is_model_reported_and_sends_no_next_packet(adapter):
    adapter._chunks=1
    adapter._future=(1,finished(dict(verdict='success',why='complete')))
    adapter.supervisor.judge=lambda *args:dict(verdict='success',why='current scene complete')
    with pytest.raises(PolicyComplete):adapter.build_trajectory('move',observation(8),8)
    assert not adapter.base.calls


def test_failed_policy_move_reaches_base_without_counting_completion(adapter):
    calls = []
    adapter.base.trajectory_failed = lambda *args, **kwargs: calls.append((args, kwargs))
    adapter._last_kind = 'policy'
    feedback = {'measured': observation(8), 'joints': [{'error_deg': 7.}]}
    adapter.trajectory_failed('final_position_mismatch', 'Target not reached', 8, feedback=feedback)
    assert calls == [(('final_position_mismatch', 'Target not reached', 8), {'feedback': feedback})]
    assert adapter._chunks == 0


def test_failed_repair_discards_remaining_steps_and_replans_from_fresh_pose(adapter):
    from collections import deque
    adapter._last_kind = 'repair'
    adapter._repair_context = {'expectation': 'old target'}
    adapter._repair = deque([{'op': 'move_to', 'arm': 'left', 'xyz': [1., 1., 1.]}])
    adapter._verify = True
    adapter.trajectory_failed('final_position_mismatch', 'Target not reached', 8,
                              feedback={'measured': observation(8, x=.2)})
    assert not adapter._repair
    adapter.build_trajectory('move', observation(9, x=.4), 9)
    history, context = adapter.supervisor.plans[-1]
    assert context['execution_error']['code'] == 'final_position_mismatch'
    assert context['replan_from_current_state']
    assert history[-1]['measured']['step_id'] == 9
    assert adapter.geometry.targets[-1][0]['left_x'] == pytest.approx(.43)


def test_failed_repair_still_obeys_plan_budget(adapter):
    adapter._last_kind = 'repair'; adapter._rounds = adapter.max_plan_rounds
    adapter.trajectory_failed('joint_settle_timeout', 'Not settled', 2)
    with pytest.raises(RuntimeError, match='plan budget'):
        adapter.build_trajectory('move', observation(9), 9)
    assert not adapter.geometry.targets


def test_supervisor_sees_completed_gripper_intent_separately_from_measurement(adapter):
    adapter.base.build_trajectory = lambda prompt, obs, step: [dict(step_id=step,
        left_joints_deg=obs['left_joints_deg'], right_joints_deg=obs['right_joints_deg'],
        left_gripper=1., right_gripper=.47)]
    adapter.build_trajectory('place the block', observation(), 0)
    assert adapter.history[-1]['preceding_packet'] is None  # planned is not executed
    measured = {**observation(1), 'right_gripper': .68}
    adapter.trajectory_completed(measured, 1)
    adapter.build_trajectory('place the block', measured, 1)
    window = adapter.history[-1]
    assert window['preceding_packet']['status'] == 'completed'
    assert window['preceding_packet']['actor'] == 'policy'
    assert window['preceding_packet']['target']['right_gripper'] == .47
    assert window['measured']['right_gripper'] == .68
    adapter._future[1].result(timeout=2)
    assert adapter.supervisor.calls[-1][1][-1]['preceding_packet']['target']['right_gripper'] == .47


def test_failed_packet_is_failure_evidence_not_a_completed_action(adapter):
    adapter.base.trajectory_failed = lambda *a, **k: None
    adapter.build_trajectory('move', observation(), 0)
    adapter.trajectory_failed('final_position_mismatch', 'Target not reached', 1)
    window = adapter._snapshot(observation(1))
    assert window['preceding_packet']['status'] == 'failed'
    assert window['preceding_packet']['failure_code'] == 'final_position_mismatch'
    assert adapter._chunks == 0


def test_adjusted_repair_receipt_uses_executed_target_and_names_primitive(adapter):
    adapter._primitive(dict(op='gripper', arm='right', value=1.), observation(), 0)
    adjusted = {**observation(1), 'right_gripper': .9}
    adapter.trajectory_adjusted(adjusted)
    adapter.trajectory_completed(adjusted, 1)
    window = adapter._snapshot(adjusted)
    receipt = window['preceding_packet']
    assert receipt['actor'] == 'repair' and receipt['operation'] == 'gripper'
    assert receipt['arm'] == 'right' and receipt['target']['right_gripper'] == .9
    assert adapter._chunks == 0


def test_unmet_expectation_replans_from_fresh_feedback(adapter):
    adapter._repair_context=dict(expectation='object rises')
    adapter._verify=True
    adapter.supervisor.verify=lambda *args:dict(verdict='replan',why='object stayed on table')
    adapter.build_trajectory('move',observation(8,x=.35),8)
    assert adapter.supervisor.plans[0][1]['verification']['verdict']=='replan'
    assert adapter.geometry.targets[0][0]['left_x']==pytest.approx(.38)


def test_failed_handback_requires_restaging_before_another_policy_chunk(adapter):
    adapter._last_kind = 'policy'
    adapter._post_policy_expectation = {'expectation': 'grasp block after releasing marker'}
    adapter.supervisor.verify = lambda *a: dict(verdict='replan', why='same wrong object again')
    default = adapter.supervisor.repair
    def repair(task, history, context):
        if not adapter.supervisor.plans:
            adapter.supervisor.plans.append((history, context))
            return dict(expectation='try again unchanged', steps=[dict(op='policy')])
        return default(task, history, context)
    adapter.supervisor.repair = repair
    adapter.build_trajectory('move block', observation(8), 8)
    assert len(adapter.supervisor.plans) == 2
    assert adapter.supervisor.plans[-1][1]['failed_policy_handback'] is True
    assert 'restaging' in adapter.supervisor.plans[-1][1]['planner_feedback']
    assert adapter.geometry.targets[-1][0]['left_x'] == pytest.approx(.28)
    assert not adapter.base.calls and adapter._rounds == 1


def test_repeated_invalid_handbacks_stop_without_base_or_repair_motion(adapter):
    adapter._last_kind = 'policy'
    adapter._post_policy_expectation = {'expectation': 'grasp block'}
    adapter.supervisor.verify = lambda *a: dict(verdict='replan', why='wrong object again')
    def repair(task, history, context):
        adapter.supervisor.plans.append((history, context))
        return dict(expectation='unchanged', steps=[dict(op='gripper', arm='right', value=1), dict(op='policy')])
    adapter.supervisor.repair = repair
    with pytest.raises(RuntimeError, match='restaging'):
        adapter.build_trajectory('move block', observation(8), 8)
    assert len(adapter.supervisor.plans) == 2
    assert not adapter.base.calls and not adapter.geometry.targets


def test_repair_context_retains_planned_steps_and_actual_handback(adapter):
    adapter._chunks = 2
    adapter._future = (1, finished(dict(verdict='intervene', why='missed grasp')))
    adapter.build_trajectory('move block', observation(8), 8)
    adapter.trajectory_completed(observation(9), 1)
    adapter.build_trajectory('move block', observation(9), 9)
    assert adapter._post_policy_expectation['steps'][0]['op'] == 'nudge'
    assert adapter._repair_plans[-1]['status'] == 'handed_back'


def test_episode_switch_and_wrong_robot_rejected_before_policy(adapter):
    adapter.build_trajectory('move',observation(),0)
    with pytest.raises(ValueError,match='episodes'):
        adapter.build_trajectory('move',observation(8,episode='two'),8)
    with pytest.raises(ValueError,match='another robot'):
        adapter.build_trajectory('move',{**observation(),'jetson_id':'other'},8)
    assert len(adapter.base.calls)==1


@pytest.mark.parametrize('step',[
 {'op':'reset'}, {'op':'nudge','arm':'left','dxyz':[float('nan'),0,0]},
 {'op':'gripper','arm':'left','value':True}, {'op':'gripper','arm':'left','value':-1},
 {'op':'lift','dz':.02}, {'op':'lift','arm':'left','dz':.02,'url':'extra'},
])
def test_invalid_repair_rejected_before_execution(step):
    with pytest.raises(ValueError):validate_plan(dict(expectation='check',steps=[step]))


def test_model_json_accepts_fenced_object_and_rejects_nonobject():
    assert object_from_text('```json\n{"flag":false}\n```')=={'flag':False}
    with pytest.raises(ValueError):object_from_text('[]')


def test_public_host_uses_private_ephemeral_recordings(monkeypatch, tmp_path):
    import shutil
    from spotter_yam.app import create_app
    monkeypatch.setenv('SPOTTER_ORIGIN', 'https://spotter.example.com')
    monkeypatch.setenv('SPOTTER_RECORDINGS', str(tmp_path / 'station-only'))
    app = create_app()
    try:
        assert app.origin == 'https://spotter.example.com'
        assert app.secure and app.hardware_control
        assert app.retain_recordings is False
        assert not (tmp_path / 'station-only').exists()
        assert b'Spotter on Blupe' in app.page()
    finally:
        shutil.rmtree(app.root)
