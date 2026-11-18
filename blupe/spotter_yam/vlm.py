"""Server-owned OpenAI-compatible vision supervisor; credentials never enter UI."""
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import threading
import time
from urllib import error, request
from .repair_contract import repair_example, repair_schema

LOCATE = '''Select up to four task-relevant visible surface points in the CURRENT
TOP camera image, for measuring repair geometry. Include the object to manipulate
and an unoccupied part of its receiving surface where visible. Return only JSON:
{"points":[{"name":"short descriptive unique name","point_1000":[x,y]}]}.
Use integer relative coordinates on a 0–1000 grid: [0,0] is the top-left and
[1000,1000] the bottom-right of the TOP image, x right, y down. These are NOT
native pixel coordinates. Select an interior point on each visible surface,
away from edges/occlusion. Do not guess XYZ, unseen objects or
depth. Return an empty points list if no relevant surface is clearly visible.'''

ROBOT = '''
### The robot and what its numbers can and cannot tell you

This is a real tabletop scene, not RoboTwin or RoboCasa simulation. Two 6-DoF YAM
arms with parallel-jaw grippers work a table; the instruction names one thing to do
with one or two objects on it. Track the objects the instruction names and no others.
Object positions change between runs: read them from the current images, never from
an earlier run or a recorded example.

The two arms are not interchangeable. Each window gives both hands' measured
Cartesian position ("cartesian", metres, each arm in its own base frame) and joint
angles. Decide which hand owns the task before judging it: on a one-handed task the
other arm sitting still for the whole run is normal.

The gripper value is a normalized opening, 0 closed and 1 open, not a width and not
a force reading. No force or contact sensing exists. The one state the number alone
identifies is "shut with nothing between the fingers". A partial opening may be a
firm grip or a hand that stopped there: the number cannot tell you something is held.
Lift and look: an object that rises with the hand is held.

Each preceding_packet is the controller's receipt for the last motion: its target is
what was requested, measured is what the robot reached. A completed packet is not a
completed task and not proof of a grasp. Camera and state timestamps are not
hardware synchronized.

You see three cameras: top (overhead, the whole table) and the left and right
side views. Use the side views for height, contact and occlusion; they never supply
coordinates.'''

GOAL = '''
### Judge against the goal, not against the activity

Name the goal state in one sentence (the block resting on the plate and released,
the cube inside the cup) and each window ask only whether the scene is closer to it
than before. Compare the named objects across the time-ordered frames, not the arms.

Motion is not progress. A policy that has lost the plot keeps reaching, opening and
closing, looking busy in every frame. If nothing the instruction names has moved for
two or three windows while the hands kept moving, it is repeating something that does
not work and will keep repeating it. Slow is not stalled: a hand that pauses or
re-aims and then continues is working. The run has a fixed time limit, and every
repair spends the same clock the policy needs.

Concrete failures: a close and lift after which the object stays on the table; the
wrong object grasped (a distractor of another colour or shape, a marker, a pen); a
target dropped; a release that leaves the object outside or on the rim of the
receptacle; repeated failed attempts at the same object with no improvement.

Not failures: the first approach, during which the target is stationary — the first approach is normal;
a hand open for many chunks early on; a held object being carried toward the target;
the gripper still closed during transport (do not call a missed release from a
closed gripper alone); an object held over or beside the target, which is progress,
not placement.'''

SCREEN = '''You screen a bimanual YAM robot's recent execution for Spotter, which repairs
real failures of the base policy. The base policy leads; your flag sends the window
to a stronger judge, not straight to a repair. Flag concrete evidence of a failure;
do not flag ordinary slow progress. If the evidence is unreadable, flag it.''' + ROBOT + GOAL + '''
Screen the executed prefix, not future targets. A gripper-open value alone does not
prove that a released object landed in the cup or on the plate.
Return only JSON: {"flag":true|false,"risk":0..10,"why":"short observation"}.'''

JUDGE = '''You are Spotter's failure-confirming judge for a bimanual YAM robot. The frozen
base policy leads; you decide whether this window needs Spotter to take over.''' + ROBOT + GOAL + '''

### When intervening pays

A failed intervention is not free: it spends the policy's time and usually leaves
the scene no better. So the question is not "is this failing?" but "can Spotter fix
this with its tools in the time left?". Intervene when all three hold:

1. You can name the specific problem in the pictures (missed grasp, wrong object,
   dropped target, release off target, the same failed attempt repeated) and say what
   the goal state looks like.
2. A short supported repair fixes it: re-stage the hand, close on the right object,
   verify the lift, carry, release inside the receptacle, withdraw.
3. Enough of the run remains for that repair and whatever the policy still has to do.

When those hold, act at the first window you can see the problem; acting late is the
same as not acting. When the evidence shows ongoing approach, grasp, lift or
transport, return pass and let the policy run its next chunk. A missed release needs
a completed OPEN request that failed, or an actual failed placement; the object not
being on the target yet is not one.

Success is your visual judgement, not a privileged signal: the object visibly
released and resting on the requested target.
Return only JSON: {"verdict":"pass"|"intervene"|"success","why":"brief evidence"}.'''

REPAIR = '''Plan a Spotter repair for a bimanual YAM robot from the CURRENT measured state
and camera frames, which may differ from the window where the failure was found.''' + ROBOT + '''

### Coordinates and the tools

All xyz are metres in the NAMED ARM'S OWN BASE FRAME (+x forward, +y left, +z up).
Rotations are yaw radians relative to the run's initial orientation. The supplied
bounds are the station's configured workspace. No reset, teleport or rewind exists.
Every step names "arm":"left"|"right", except a {"op":"policy"} hand-back. Steps:
{"op":"nudge","arm":"left","dxyz":[dx,dy,dz]},
{"op":"lift","arm":"left","dz":number,"intent":"clearance"|"grasp_check"},
{"op":"move_to","arm":"left","xyz":[x,y,z]},
{"op":"rotate","arm":"left","yaw":number},
{"op":"gripper","arm":"left","value":0..1},
{"op":"policy"}.
Obey context.max_plan_steps; context.remaining_plan_rounds is how many more plan
rounds this intervention has. When they run out, or a plan cannot be made valid,
Spotter hands control back to the policy and keeps watching; previous_repairs then
records a gave_up_handback. Keep the other arm at its measured state, above all if
it holds something, unless it also needs a correction.

When context.grounding is supplied, its points are measured surface coordinates from
the latest overhead RGB-D image, each with separate left- and right-arm XYZ. To go
to a measured object or surface, use
{"op":"move_to_point","arm":"left"|"right","point":"exact point name","offset":[dx,dy,dz]}
(offsets in the selected arm's base, each at most 0.15 m): it is re-measured just
before execution, so it tracks the object better than copying its numbers into a
move_to. move_to and nudge remain available, for example to move relative to the
hand's own measured position. A point's Z is the object's top surface,
not its grasp centre: approach above it first, then choose a small grasp-height
offset. Choose the arm whose approach AND destination both fit its bounds; a hand
need not do the task just because it moved last.

### What a repair looks like here

1. Decide which arm is in trouble and what the goal state is.
2. If the policy was doing the right thing and only the hand's line was off, re-stage
   the open hand where it can work from and hand back with {"op":"policy"}.
3. If the fault is what or where — the wrong object, a release off target, a grasp the
   policy has already missed after a hand-back — do that part yourself all the way to
   its end state: approach, close, a grasp_check lift, carry, release, withdraw. A
   hand-back after a small fix will redo the same wrong thing.
4. A plan without a final policy step stays under Spotter: after a lift or a
   completed segment, fresh images verify it and you plan the next round.

Every lift carries an intent. clearance raises or re-stages the hand before a grasp
and does not need the object to move. grasp_check follows a close and must raise the
intended object; replan an empty grasp from fresh observations. Never carry on as if
holding something a grasp_check did not show rising. Release only when the current
images show the held object over the interior of the receptacle, not its rim; do not
open a gripper just because the task is unfinished. If the policy is still carrying
the object toward the target, that is progress: hand back.

### Missing depth

If a point you need is absent (missing or noisy depth, or the arm hides the target),
inspect all views. When the arm visibly blocks the target and a bounded vertical lift
fits the measured pose and bounds, return only a short clearance lift, gripper and
other arm unchanged, and end the segment: Spotter verifies it, captures fresh RGB-D,
re-selects points and asks you again. Use only the new points afterwards. Missing 3D
targets never justify guessed positions or releases; do not repeat blind lifts when
the view is already clear or depth stays unavailable — say what limits you.

### Do not repeat what failed

context.previous_repairs records, across interventions, each planned plan and
whether it reached a hand-back, completed a clearance, or failed. Planned steps are
intent, not proof they ran. A recipe that already failed at this target will fail
again: change something real — the arm, the approach height or offset, the yaw, or
finish the step yourself. When failed_policy_handback is true, an unchanged
hand-back, or only reopening the gripper, does not repair it.

If the policy is making ordinary progress, or no supported repair fits, say so and
return just the hand-back.
Return only JSON: {"why":"brief evidence","expectation":"what should change visually
after this repair","steps":[...]}.'''

VERIFY_BASE = '''Verify the last Spotter repair step for a bimanual YAM robot using fresh CURRENT
images and measured state, against the recorded expectation.''' + ROBOT + '''

Return only JSON {"verdict":"verified"|"replan"|"success","why":"brief visual evidence"}.
replan when the expectation is not visibly met. A closed gripper alone is not proof
of a grasp. success means the whole task is visibly complete, not just the repair
step: for placement, the object is released and resting on the target; held over or
beside it is not placed.'''

VERIFY = VERIFY_BASE + '''
For checkpoint.scope="intermediate", judge only the completed_step and the
already-executed prefix. remaining_steps have NOT run yet: do not reject a
successful lift because pending transport or release has not happened. At a lift
checkpoint, verified requires visible evidence that the intended object rose
with the gripper; if it stayed on the table or the gripper is empty, replan.
The full-plan expectation describes the eventual result, not a demand that all
remaining steps already happened.'''

VERIFY_INTENT = VERIFY_BASE + '''
For an intermediate checkpoint, verify ONLY the completed step and the executed
prefix; remaining steps have NOT run. Use completed_step.intent and the plan
expectation. A clearance lift raises or re-stages the hand before grasping: it
does NOT require the target to rise, and the target staying on the table is
normal. Check the hand moved as intended and the scene suits the pending approach,
rotation or grasp. A grasp_check lift follows an attempted close: the intended
target must visibly rise with the hand; a target still on the table or an empty
grasp means replan. For unspecified intent, infer it from the planned steps and
expectation, never from the lift opcode alone. Do not reject a step only because
pending transport or release is incomplete.'''

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
    def __init__(self, endpoint, model, key='', *, timeout=90, api_style='vllm', readiness_cache=None,
                 use_repair_example=False):
        if api_style not in {'vllm', 'openrouter', 'codex'}:
            raise ValueError('Unknown supervisor API style')
        if api_style == 'openrouter' and not key.strip():
            raise ValueError('OpenRouter supervisor requires a server-owned API key')
        self.endpoint, self.model, self._key = endpoint.rstrip('/'), model, key
        # A proxied `codex exec` takes ~20 s and occasionally ~120 s; shorter
        # bounds would kill healthy calls and spend quota on retries.
        self.timeout = max(timeout, 150) if api_style == 'codex' else timeout
        self.api_style = api_style
        self.readiness_cache = readiness_cache
        self.use_repair_example = use_repair_example
        self.last_call = None
        self._opener = request.build_opener(request.ProxyHandler())

    def ready(self, cancelled=lambda: False):
        if self.readiness_cache is not None:
            return self.readiness_cache.check(self, cancelled)
        return self._ready(cancelled)

    def _ready(self, cancelled):
        if self.api_style in ('openrouter', 'codex'):
            if cancelled():
                raise RuntimeError('Spotter preparation cancelled')
            # The public model catalog does not verify authentication or credits.
            result = self.call('Return only JSON: {"ready":true}.', 'Readiness check', [],
                               max_tokens=256 if self.model == 'openai/gpt-6.1-sol' else 32)
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

    def call(self, system, task, history, *, context=None, max_tokens=1800, schema=None, example=None):
        content = [{'type': 'text', 'text': json.dumps({'task': task, 'context': context or {}}, allow_nan=False)}]
        for window in history:
            content.append({'type': 'text', 'text': json.dumps({key: value for key, value in window.items() if key != 'frames'}, allow_nan=False)})
            for frame in window['frames']:
                content.append({'type': 'text', 'text': frame.name + ' camera'})
                content.append({'type': 'image_url', 'image_url': {'url': 'data:image/jpeg;base64,' + base64.b64encode(frame.jpeg).decode()}})
        body = {'model': self.model, 'temperature': .1, 'max_tokens': max_tokens,
                'response_format': {'type': 'json_object'},
                'messages': [{'role': 'system', 'content': system}, {'role': 'user', 'content': content}]}
        if example:
            body['messages'][1:1] = example
        if schema is not None:
            body['response_format'] = {'type': 'json_schema', 'json_schema': {
                'name': 'spotter_repair', 'strict': True, 'schema': schema}}
        if self.api_style == 'codex':
            return self._codex_call(body['messages'], schema)
        if self.api_style == 'openrouter':
            body['provider'] = {'require_parameters': True, 'sort': 'latency'}
            # This instruct checkpoint does not advertise a reasoning parameter.
            if self.model == 'openai/gpt-6.1-sol':
                body.pop('temperature')
                body['reasoning'] = {'effort': 'low'}
            elif self.model != VISION_QWEN:
                body['reasoning'] = {'effort': 'none'}
        else:
            body['chat_template_kwargs'] = {'enable_thinking': False}
        req = request.Request(self.endpoint + '/chat/completions', data=json.dumps(body, allow_nan=False).encode(), headers=self._headers())
        started = time.monotonic()
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
        self.last_call = dict(model=result.get('model', self.model), duration_s=time.monotonic()-started,
                              usage=result.get('usage'))
        try:
            return object_from_text(result['choices'][0]['message']['content'])
        except Exception as exc:
            # Provider bodies/URLs can carry credentials. Log only the exception class.
            raise RuntimeError('Spotter supervisor request failed (' + type(exc).__name__ + ')') from None

    def _codex_call(self, messages, schema):
        """Local `codex exec` with the operator's ChatGPT login; endpoint names the binary."""
        binary = shutil.which(self.endpoint or 'codex')
        if not binary:
            raise RuntimeError('Spotter Codex CLI was not found on this host')
        with tempfile.TemporaryDirectory(prefix='spotter-codex-', ignore_cleanup_errors=True) as root:
            root, lines, images = Path(root), [], []
            for message in messages:
                lines.append('## ' + message['role'].upper())
                content = message['content']
                if isinstance(content, str):
                    lines.append(content)
                    continue
                for part in content:
                    if part['type'] == 'text':
                        lines.append(part['text'])
                    else:
                        path = root / f'image-{len(images) + 1}.jpg'
                        path.write_bytes(base64.b64decode(part['image_url']['url'].split(',', 1)[1]))
                        images.append(path)
                        lines.append(f'[attached image {len(images)}]')
            lines.append('Attached images are numbered in the order above. Reply with only the JSON object.')
            output = root / 'last-message.txt'
            # SPOTTER_CODEX_USE_CONFIG=1 keeps $CODEX_HOME/config.toml (an API-key relay
            # provider); forcing the ChatGPT login there makes codex delete that auth.json.
            login = ([] if os.environ.get('SPOTTER_CODEX_USE_CONFIG') == '1' else
                     ['--ignore-user-config', '-c', 'forced_login_method="chatgpt"',
                      '-c', 'model_provider="openai"'])
            command = [binary, 'exec', *login, '--skip-git-repo-check', '--ephemeral',
                       '--model', self.model, '-o', str(output), '-C', str(root),
                       '-c', 'model_reasoning_effort="low"', '-c', 'sandbox_mode="read-only"',
                       '-c', 'approval_policy="never"', '-c', 'web_search="disabled"',
                       '-c', 'features.shell_tool=false', '-c', 'features.multi_agent=false',
                       '-c', 'features.apps=false', '-c', 'features.hooks=false']
            if schema is not None:
                (root / 'schema.json').write_text(json.dumps(schema))
                command += ['--output-schema', str(root / 'schema.json')]
            for path in images:
                command += ['--image', str(path)]
            command += ['-']
            started = time.monotonic()
            try:
                subprocess.run(command, input='\n'.join(lines), text=True, timeout=self.timeout,
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
                text = output.read_text()
            except subprocess.TimeoutExpired:
                raise RuntimeError('Spotter Codex request timed out') from None
            except Exception as exc:
                raise RuntimeError('Spotter Codex request failed (' + type(exc).__name__ + ')') from None
        self.last_call = dict(model=self.model, duration_s=time.monotonic()-started, usage=None)
        try:
            return object_from_text(text)
        except Exception as exc:
            raise RuntimeError('Spotter Codex request failed (' + type(exc).__name__ + ')') from None

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
        options = {}
        if self.use_repair_example:
            options.update(schema=repair_schema(context),
                example=repair_example(max_steps=context.get('max_plan_steps', 16)), max_tokens=4000)
        return self.call(REPAIR, task, history, context=context, **options)

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


class TwoStageSupervisor:
    """Fast screening is independent of failure confirmation and correction."""
    def __init__(self, screening, intervention):
        self.screening, self.intervention = screening, intervention
        self.model = self.screening_model = screening.model
        self.intervention_model = intervention.model

    def ready(self, cancelled=lambda: False):
        self.screening.ready(cancelled)
        self.intervention.ready(cancelled)

    def screen(self, *args, **kwargs): return self.screening.screen(*args, **kwargs)
    def judge(self, *args, **kwargs): return self.intervention.judge(*args, **kwargs)
    def repair(self, *args, **kwargs): return self.intervention.repair(*args, **kwargs)
    def locate(self, *args, **kwargs): return self.intervention.locate(*args, **kwargs)
    def verify(self, *args, **kwargs): return self.intervention.verify(*args, **kwargs)
