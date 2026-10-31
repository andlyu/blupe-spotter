"""Server-owned OpenAI-compatible vision supervisor; credentials never enter UI."""
import base64
import hashlib
import json
import re
import threading
import time
from urllib import error, request

LOCATE = '''Select up to four task-relevant visible surface points in the CURRENT
TOP camera image, for measuring repair geometry. Include the object to manipulate
and an unoccupied part of its receiving surface where visible. Return only JSON:
{"points":[{"name":"short descriptive unique name","point_1000":[x,y]}]}.
Use integer relative coordinates on a 0–1000 grid: [0,0] is the top-left and
[1000,1000] the bottom-right of the TOP image, x right, y down. These are NOT
native pixel coordinates. Select an interior point on each visible surface,
away from edges/occlusion. Do not guess XYZ, unseen objects or
depth. Return an empty points list if no relevant surface is clearly visible.'''

SCREEN = '''You screen a bimanual YAM robot's recent task execution. The base policy
leads. Flag concrete evidence of missed grasps, wrong objects, drops or persistent
lack of progress. Compare object motion across the time-ordered camera frames.
An unfinished task, a held object, or carrying it toward the target is ordinary
progress. Do not flag a missed release merely because the gripper is still closed.
Use preceding_packet receipts to distinguish requested actions from outcomes.
Grippers are normalized 0 closed, 1 open; these are not millimetres, a force sensor,
or proof that an object is held. One stationary arm can be normal. Camera/state
timestamps are not hardware synchronized. If evidence is unreadable, flag it.
Return JSON: {"flag":true|false,"risk":0..10,"why":"short observation"}.'''

JUDGE = '''You are Spotter's failure-confirming supervisor for physical bimanual
YAM arms. The frozen policy leads. You intervene only for a concrete failure;
ordinary slow progress is not a failure. Compare task-relevant objects across
the history, then confirm with measured state. Never infer a successful grasp
from a gripper number alone. A closed gripper can be empty. Return only JSON:
{"verdict":"pass"|"intervene"|"success","why":"brief evidence"}.
Success is your visual assessment, not a privileged task-success signal.
Each preceding_packet is the controller's completed/failed packet receipt; its
target is what was requested, while measured is what the robot actually reached.
Packet completion is NOT task completion or proof of a grasp. A request to keep
closing/holding the gripper while transporting an object is normal progress.
Do not label that a missed release. A missed release requires evidence of a
completed OPEN request that failed, or an actual failed placement/departure;
the object not being on the target yet is insufficient. Compare the time-ordered
images and receipts. A completed close/lift where the object stays behind is
concrete missed-grasp evidence. When evidence shows ongoing approach, grasp,
lift or transport rather than a failed attempt, return pass and let the policy
continue its next chunk. For placement tasks, success requires the object to be
visibly released and resting on the requested target. Holding it over or beside
the target is progress, not completed placement.'''

REPAIR = '''Plan a short Spotter repair from the CURRENT measured state and
camera frames, which may differ from the earlier detected failure. Keep the
other hand at its measured state unless it also needs a correction. All xyz
coordinates are metres in the NAMED ARM'S OWN BASE FRAME (+x forward,+y left,+z
up). Rotations are yaw radians relative to the run's initial orientation.
Grippers: 0 closed, 1 open; no force/contact oracle. The supplied bounds are
the station's configured bounds. No simulator reset, teleport, or rewind exists.
Return only JSON: {"why":"brief evidence","expectation":"what should change
visually after this repair","steps":[...]}. At most 8 steps. Each step must name
"arm":"left"|"right", except a final {"op":"policy"} hand-back. Supported steps:
{"op":"nudge","arm":"left","dxyz":[dx,dy,dz]},
{"op":"lift","arm":"left","dz":number,"intent":"clearance"|"grasp_check"},
{"op":"move_to","arm":"left","xyz":[x,y,z]},
{"op":"rotate","arm":"left","yaw":number},
{"op":"gripper","arm":"left","value":0..1},
{"op":"policy"}. The executor returns fresh measured feedback after each step;
after a lift or completed plan segment it asks you to verify the visible outcome before
continuing. Prefer re-staging then handing back to the base policy. If current
evidence no longer supports a repair, return only the policy hand-back.'''
REPAIR += '''
Give every lift an explicit intent: clearance raises/re-stages the hand before a
grasp, while grasp_check follows an attempted close and must lift the intended
object. A clearance lift does not require the object to move. These intents do
not claim that a grasp succeeded; verification uses fresh images.'''
REPAIR += '''
Do not open a gripper just because the task is unfinished. Confirm in current
images that a held object is actually over the intended receiving surface before
releasing it. If the base policy is still carrying the object toward that surface,
or the needed 3D target is uncertain, hand back instead of guessing a release or
an absolute xyz pose. Completed packet intent is not proof of grasp or placement.'''
REPAIR += '''
When context.grounding is supplied, its points are measured surface coordinates
from the latest paired native overhead RGB-D image. Each point provides separate
left/right arm-base XYZ. Choose an arm whose approach AND destination fit its
bounds; the right hand need not do a task just because it moved previously.
Use {"op":"move_to_point","arm":"left"|"right","point":"exact point name",
"offset":[dx,dy,dz]} for ALL horizontal repair positioning. Offsets are metres
in the selected arm base, each no larger than 0.15 in magnitude. Approach above
the surface first; surface Z is the object top, not automatically the grasp
center. Select an appropriate small grasp-height offset, then close and lift
to verify before transport. Do not emit raw move_to or horizontal nudge when
grounding is supplied. Lift, rotate, gripper and policy hand-back remain allowed.
If the measurements/bounds do not support a repair, hand back. Experimental
calibration is not a contact oracle; preserve its uncertainty.'''
REPAIR += '''
Context.previous_repairs records planned steps and whether each reached a policy
handback or failed. Use this causal history with the current visual evidence.
When failed_policy_handback is true, the prior handback has already been tested
and failed: another unchanged handback, or only opening the gripper again, does
not repair that failure. Re-stage the arm at a measured task-relevant approach,
or correct its orientation, before trying the policy again. A manual close is
available after a failed handback if visual evidence supports a grounded grasp.
Do not spend the remaining rounds repeating the same ineffective release and
handback. Keep inactive arms at their measured state and verify a lift before
transport. If no valid repair is supported, explain the limitation explicitly.'''

VERIFY = '''Verify the last Spotter repair using fresh CURRENT images and measured
state against the recorded expectation. Return JSON {"verdict":"verified"|
"replan"|"success","why":"brief visual evidence"}. A closed gripper alone is
not proof of a grasp. Use replan if the expectation is not visibly met.
Success means the whole user's task is visually complete, not just the repair
step. For placement, the object must be visibly released and resting on the
target. An object still held over or beside it has not been placed.'''
VERIFY += '''
For checkpoint.scope="intermediate", judge only the completed_step and the
already-executed prefix. remaining_steps have NOT run yet: do not reject a
successful lift because pending transport or release has not happened. At a lift
checkpoint, verified requires visible evidence that the intended object rose
with the gripper; if it stayed on the table or the gripper is empty, replan.
The full-plan expectation describes the eventual result, not a demand that all
remaining steps already happened. Even at an intermediate checkpoint, success
still requires the whole task visibly complete and the object released on target.'''

VERIFY_INTENT = VERIFY.split('For checkpoint.scope=')[0] + '''
For an intermediate checkpoint, verify ONLY the completed step and executed prefix.
Remaining steps have NOT run. Use completed_step.intent and the plan expectation.
A clearance lift raises/re-stages the hand before grasping: it does NOT require
the target to rise; the target remaining on the table is normal. Check the hand
moved as intended and the scene is appropriate for the pending approach/rotation/grasp.
A grasp_check lift follows an attempted close: the intended target must visibly
rise with the hand. Target still on the table or an empty grasp means replan.
For unspecified intent, infer from planned steps/expectation; never from the lift
opcode alone. Never infer holding from a gripper fraction alone. Do not reject a
step just because pending transport/release is incomplete. Success still requires
the whole placement complete with the object released on target.'''

VISION_QWEN = 'qwen/qwen3-vl-235b-a22b-instruct'


def object_from_text(text):
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.S).strip()
    if '</think>' in text:
        text = text.split('</think>', 1)[1].strip()
    text = re.sub(r'^```(?:json)?\s*|\s*```$', '', text).strip()
    value = json.loads(text)
    if not isinstance(value, dict):
        raise ValueError('Supervisor must return a JSON object')
    return value


class ReadinessCache:
    """Short-lived authenticated preflight only; never camera or policy data."""
    def __init__(self, ttl=60, clock=time.monotonic):
        self.ttl, self.clock = ttl, clock
        self._condition = threading.Condition()
        self._identity, self._until = None, 0.
        self._checking = self._scheduled = False
        self._next_probe = 0.
        self._closed = threading.Event()

    @staticmethod
    def identity(supervisor):
        return (supervisor.endpoint, supervisor.model, supervisor.api_style,
                hashlib.sha256(supervisor._key.encode()).digest())

    def check(self, supervisor, cancelled, *, refresh=False):
        identity = self.identity(supervisor)
        stopped = lambda: self._closed.is_set() or cancelled()
        with self._condition:
            if stopped(): raise RuntimeError('Spotter preparation cancelled')
            if not refresh and self._identity == identity and self.clock() < self._until:
                return
            while self._checking:
                if stopped(): raise RuntimeError('Spotter preparation cancelled')
                self._condition.wait(.1)
            if stopped(): raise RuntimeError('Spotter preparation cancelled')
            if not refresh and self._identity == identity and self.clock() < self._until:
                return
            self._checking = True
            if not refresh:
                self._identity, self._until = None, 0.
        try:
            supervisor._ready(stopped)
            if stopped(): raise RuntimeError('Spotter preparation cancelled')
            with self._condition:
                self._identity, self._until = identity, self.clock() + self.ttl
        except Exception:
            with self._condition:
                # A failed refresh must not leave an earlier success usable.
                self._identity, self._until = None, 0.
            raise
        finally:
            with self._condition:
                self._checking = False
                self._condition.notify_all()

    def start(self, supervisor):
        """Rate-limited refresh while the page polls; foreground launch can join it."""
        with self._condition:
            now = self.clock()
            if (self._closed.is_set() or self._checking or self._scheduled or now < self._next_probe
                    or self._identity == self.identity(supervisor) and self._until - now > 15):
                return
            self._scheduled, self._next_probe = True, now + 15
        def probe():
            try:
                self.check(supervisor, self._closed.is_set, refresh=True)
            except Exception:
                pass  # Launch still performs its authenticated check and reports failures.
            finally:
                with self._condition:
                    self._scheduled = False
        threading.Thread(target=probe, daemon=True, name='spotter-supervisor-preflight').start()

    def close(self):
        self._closed.set()
        with self._condition:
            self._condition.notify_all()


class VisionSupervisor:
    def __init__(self, endpoint, model, key='', *, timeout=90, api_style='vllm', readiness_cache=None):
        if api_style not in {'vllm', 'openrouter'}:
            raise ValueError('Unknown supervisor API style')
        if api_style == 'openrouter' and not key.strip():
            raise ValueError('OpenRouter supervisor requires a server-owned API key')
        self.endpoint, self.model, self._key = endpoint.rstrip('/'), model, key
        self.timeout, self.api_style = timeout, api_style
        self.readiness_cache = readiness_cache
        self._opener = request.build_opener(request.ProxyHandler())

    def ready(self, cancelled=lambda: False):
        if self.readiness_cache is not None:
            return self.readiness_cache.check(self, cancelled)
        return self._ready(cancelled)

    def _ready(self, cancelled):
        if self.api_style == 'openrouter':
            if cancelled():
                raise RuntimeError('Spotter preparation cancelled')
            # The public model catalog does not verify authentication or credits.
            result = self.call('Return only JSON: {"ready":true}.', 'Readiness check', [], max_tokens=32)
            if cancelled():
                raise RuntimeError('Spotter preparation cancelled')
            if result.get('ready') is not True:
                raise RuntimeError('Spotter supervisor returned an invalid readiness response')
            return
        deadline = time.monotonic() + 1200
        while not cancelled():
            try:
                req = request.Request(self.endpoint + '/models', headers=self._headers())
                with self._opener.open(req, timeout=10) as response:
                    models = json.loads(response.read(1024 * 1024))
            except Exception:
                if time.monotonic() >= deadline:
                    raise RuntimeError('Spotter supervisor did not become ready within twenty minutes') from None
                for _ in range(30):
                    if cancelled(): raise RuntimeError('Spotter preparation cancelled')
                    time.sleep(.1)
                continue
            if self.model not in [item.get('id') for item in models.get('data', [])]:
                raise RuntimeError('Configured supervisor model is not served')
            return
        raise RuntimeError('Spotter preparation cancelled')

    def _headers(self):
        headers = {'Content-Type': 'application/json'}
        if self._key:
            headers['Authorization'] = 'Bearer ' + self._key
        return headers

    def call(self, system, task, history, *, context=None, max_tokens=1800):
        content = [{'type': 'text', 'text': json.dumps({'task': task, 'context': context or {}}, allow_nan=False)}]
        for window in history:
            content.append({'type': 'text', 'text': json.dumps({key: value for key, value in window.items() if key != 'frames'}, allow_nan=False)})
            for frame in window['frames']:
                content.append({'type': 'text', 'text': frame.name + ' camera'})
                content.append({'type': 'image_url', 'image_url': {'url': 'data:image/jpeg;base64,' + base64.b64encode(frame.jpeg).decode()}})
        body = {'model': self.model, 'temperature': .1, 'max_tokens': max_tokens,
                'response_format': {'type': 'json_object'},
                'messages': [{'role': 'system', 'content': system}, {'role': 'user', 'content': content}]}
        if self.api_style == 'openrouter':
            body['provider'] = {'require_parameters': True, 'sort': 'latency'}
            # This instruct checkpoint does not advertise a reasoning parameter.
            if self.model != VISION_QWEN:
                body['reasoning'] = {'effort': 'none'}
        else:
            body['chat_template_kwargs'] = {'enable_thinking': False}
        req = request.Request(self.endpoint + '/chat/completions', data=json.dumps(body, allow_nan=False).encode(), headers=self._headers())
        try:
            with self._opener.open(req, timeout=self.timeout) as response:
                result = json.loads(response.read(4 * 1024 * 1024))
        except error.HTTPError as exc:
            status = exc.code
            exc.close()
            raise self._api_error(status) from None
        except Exception as exc:
            raise RuntimeError('Spotter supervisor request failed (' + type(exc).__name__ + ')') from None
        if isinstance(result, dict) and isinstance(result.get('error'), dict):
            raise self._api_error(result['error'].get('code')) from None
        try:
            return object_from_text(result['choices'][0]['message']['content'])
        except Exception as exc:
            # Provider bodies/URLs can carry credentials. Log only the exception class.
            raise RuntimeError('Spotter supervisor request failed (' + type(exc).__name__ + ')') from None

    @staticmethod
    def _api_error(status):
        # Never expose provider bodies, URLs or credential fragments in run notes.
        if type(status) is not int:
            status = None
        messages = {
            401: 'Spotter supervisor API key was rejected. Check the host configuration.',
            402: 'Spotter supervisor has insufficient API credits. Add credits before retrying.',
            403: 'Spotter supervisor API access was denied. Check the key permissions.',
            429: 'Spotter supervisor API is rate limited. Please retry shortly.',
        }
        return RuntimeError(messages.get(status, 'Spotter supervisor API request failed'))

    def screen(self, task, history):
        result = self.call(SCREEN, task, history)
        if type(result.get('flag')) is not bool or type(result.get('risk')) is not int or not 0 <= result['risk'] <= 10:
            raise ValueError('Malformed screener result')
        return result

    def judge(self, task, history, context):
        result = self.call(JUDGE, task, history, context=context)
        if result.get('verdict') not in {'pass', 'intervene', 'success'}:
            raise ValueError('Malformed judge verdict')
        return result

    def repair(self, task, history, context):
        return self.call(REPAIR, task, history, context=context)

    def locate(self, task, history):
        latest = history[-1]
        frames = [frame for frame in latest['frames'] if frame.name == 'top']
        if len(frames) != 1:
            raise ValueError('Point selection requires exactly one paired top image')
        return self.call(LOCATE, task, [{**latest, 'frames': frames}], max_tokens=600)

    def verify(self, task, history, context):
        checkpoint = context.get('checkpoint', {}).get('completed_step', {})
        prompt = VERIFY_INTENT if checkpoint.get('intent') in ('clearance', 'grasp_check') else VERIFY
        if self.model == VISION_QWEN:
            result = self.call(prompt, task, history[-2:], context=context, max_tokens=1200)
        else:
            result = self.call(prompt, task, history, context=context)
        if result.get('verdict') not in {'verified', 'replan', 'success'}:
            raise ValueError('Malformed verification result')
        return result
