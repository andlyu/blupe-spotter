"""Server-owned OpenAI-compatible vision supervisor; credentials never enter UI."""
import base64
import json
import re
import time
from urllib import request

SCREEN = '''You screen a bimanual YAM robot's recent task execution. The base policy
leads. Flag concrete evidence of missed grasps, wrong objects, drops or persistent
lack of progress. Compare object motion across the time-ordered camera frames.
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
Success is your visual assessment, not a privileged task-success signal.'''

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
{"op":"lift","arm":"left","dz":number},
{"op":"move_to","arm":"left","xyz":[x,y,z]},
{"op":"rotate","arm":"left","yaw":number},
{"op":"gripper","arm":"left","value":0..1},
{"op":"policy"}. The executor returns fresh measured feedback after each step;
after a lift or completed plan segment it asks you to verify the visible outcome before
continuing. Prefer re-staging then handing back to the base policy. If current
evidence no longer supports a repair, return only the policy hand-back.'''

VERIFY = '''Verify the last Spotter repair using fresh CURRENT images and measured
state against the recorded expectation. Return JSON {"verdict":"verified"|
"replan"|"success","why":"brief visual evidence"}. A closed gripper alone is
not proof of a grasp. Use replan if the expectation is not visibly met.'''


def object_from_text(text):
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.S).strip()
    if '</think>' in text:
        text = text.split('</think>', 1)[1].strip()
    text = re.sub(r'^```(?:json)?\s*|\s*```$', '', text).strip()
    value = json.loads(text)
    if not isinstance(value, dict):
        raise ValueError('Supervisor must return a JSON object')
    return value


class VisionSupervisor:
    def __init__(self, endpoint, model, key='', *, timeout=90):
        self.endpoint, self.model, self._key = endpoint.rstrip('/'), model, key
        self.timeout = timeout
        self._opener = request.build_opener(request.ProxyHandler())

    def ready(self, cancelled=lambda: False):
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

    def call(self, system, task, history, *, context=None):
        content = [{'type': 'text', 'text': json.dumps({'task': task, 'context': context or {}}, allow_nan=False)}]
        for window in history:
            content.append({'type': 'text', 'text': json.dumps({key: value for key, value in window.items() if key != 'frames'}, allow_nan=False)})
            for frame in window['frames']:
                content.append({'type': 'text', 'text': frame.name + ' camera'})
                content.append({'type': 'image_url', 'image_url': {'url': 'data:image/jpeg;base64,' + base64.b64encode(frame.jpeg).decode()}})
        body = {'model': self.model, 'temperature': .1, 'max_tokens': 1800,
                'response_format': {'type': 'json_object'},
                'messages': [{'role': 'system', 'content': system}, {'role': 'user', 'content': content}],
                'chat_template_kwargs': {'enable_thinking': False}}
        req = request.Request(self.endpoint + '/chat/completions', data=json.dumps(body, allow_nan=False).encode(), headers=self._headers())
        try:
            with self._opener.open(req, timeout=self.timeout) as response:
                result = json.loads(response.read(4 * 1024 * 1024))
            return object_from_text(result['choices'][0]['message']['content'])
        except Exception as exc:
            # Provider bodies/URLs can carry credentials. Log only the exception class.
            raise RuntimeError('Spotter supervisor request failed (' + type(exc).__name__ + ')') from None

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

    def verify(self, task, history, context):
        result = self.call(VERIFY, task, history, context=context)
        if result.get('verdict') not in {'verified', 'replan', 'success'}:
            raise ValueError('Malformed verification result')
        return result
