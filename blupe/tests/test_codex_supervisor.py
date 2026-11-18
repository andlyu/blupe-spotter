import json
import subprocess
from pathlib import Path
from types import SimpleNamespace

from spotter_yam import vlm
from spotter_yam.vlm import VisionSupervisor


def test_codex_repair_attaches_images_schema_and_parses_last_message(monkeypatch):
    plan = {'why': 'restage', 'expectation': 'above object', 'steps': [{'op': 'policy'}]}
    seen = {}
    def run(command, *, input, **kwargs):
        seen['command'], seen['input'] = command, input
        images = [Path(command[i + 1]) for i, part in enumerate(command) if part == '--image']
        seen['images'] = [path.read_bytes() for path in images]
        seen['schema'] = json.loads(Path(command[command.index('--output-schema') + 1]).read_text())
        Path(command[command.index('-o') + 1]).write_text('```json\n' + json.dumps(plan) + '\n```')
    monkeypatch.setattr(vlm.shutil, 'which', lambda name: '/bin/codex')
    monkeypatch.setattr(vlm.subprocess, 'run', run)
    value = VisionSupervisor('codex', 'gpt-6.1-sol', api_style='codex', use_repair_example=True)
    frame = SimpleNamespace(name='top', jpeg=b'CURRENT')
    assert value.repair('CURRENT TASK', [{'window': 1, 'frames': [frame]}], {'max_plan_steps': 4}) == plan
    assert seen['command'][:2] == ['/bin/codex', 'exec'] and 'sandbox_mode="read-only"' in seen['command']
    assert seen['images'][-1] == b'CURRENT' and len(seen['images']) == 4  # three example frames first
    assert seen['schema']['properties']['steps']['maxItems'] == 4
    assert 'CURRENT TASK' in seen['input'] and seen['input'].index('## ASSISTANT') < seen['input'].rindex('## USER')


def test_codex_failure_never_leaks_process_output(monkeypatch):
    def run(command, **kwargs):
        raise subprocess.CalledProcessError(1, command, output='secret', stderr='token')
    monkeypatch.setattr(vlm.shutil, 'which', lambda name: '/bin/codex')
    monkeypatch.setattr(vlm.subprocess, 'run', run)
    value = VisionSupervisor('codex', 'gpt-6.1-sol', api_style='codex')
    try:
        value.judge('task', [], {})
    except RuntimeError as error:
        assert str(error) == 'Spotter Codex request failed (CalledProcessError)'
    else:
        raise AssertionError('expected failure')
