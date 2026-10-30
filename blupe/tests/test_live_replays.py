"""Exercise recording ownership, real encoding and finalization without a robot."""
import io
import json
import shutil
import time
from types import SimpleNamespace

import pytest
from PIL import Image

from remote_yam.cameras import CameraFrame
from spotter_yam.app import ROBOHOUSE
from spotter_yam.live_replays import LiveReplays, LiveRecording, ReplayStore
from spotter_yam.ui import runner_script


def state():
    return dict(status='running', session_id='owned-session', episode_id='ep_live',
                run_started_at=time.time(), run_configuration={'model':'spotter/dreamlabs/dream-1-beta'})


def test_recording_requires_owned_running_episode_and_never_restarts_it(tmp_path):
    jobs = []
    def factory(*args):
        job = SimpleNamespace(start=lambda:jobs.append(args))
        return job
    manager = LiveReplays(tmp_path, 'https://camera.example', ROBOHOUSE, job_factory=factory)
    running = state()
    manager.observe(running, 'someone-else', 'task', 'Andrew', lambda:running)
    manager.observe(dict(running,status='queued'), 'owned-session', 'task', 'Andrew', lambda:running)
    manager.observe(dict(running,episode_id='../other'), 'owned-session', 'task', 'Andrew', lambda:running)
    assert not jobs
    manager.observe(running, 'owned-session', 'task', 'Andrew', lambda:running)
    manager.observe(running, 'owned-session', 'task', 'Andrew', lambda:running)
    assert len(jobs) == 1 and jobs[0][3]['episode_id'] == 'ep_live'


def test_pre_run_and_future_images_are_not_used_as_current_run_footage(tmp_path):
    running = state()
    job = LiveRecording(tmp_path, 'https://camera.example', ROBOHOUSE, running,
                        'task', 'Andrew', lambda:running)
    for stamp in (running['run_started_at']-20, time.time()+100):
        job.accept(CameraFrame('top', b'ignored', time.time(), source_captured_at=stamp))
    assert not job.received
    job.accept(CameraFrame('top', b'fresh', time.time(), source_captured_at=time.time()))
    assert job.received == {'top'}


@pytest.mark.skipif(not shutil.which('ffmpeg'), reason='Host encoder is required')
def test_live_video_finalizes_on_its_terminal_state_without_native_archive(tmp_path, monkeypatch):
    running = state()
    first = time.monotonic()
    data = io.BytesIO()
    Image.new('RGB', (640,360), 'green').save(data, 'JPEG')
    class Collector:
        def __init__(self, origin, urls, directory, **kwargs):
            self.sink = kwargs['sink']
        def start(self):
            for role in ('left','top','right'):
                self.sink(CameraFrame(role, data.getvalue(), time.time(), source_captured_at=time.time()))
        def close(self): pass
    monkeypatch.setattr('spotter_yam.live_replays.SessionReviewRecorder', Collector)
    def read():
        return dict(running, status='failed' if time.monotonic()-first>1.2 else 'running')
    job = LiveRecording(tmp_path, 'https://camera.example', ROBOHOUSE, running,
                        'recording regression fixture', 'Automated test fixture', read)
    job.start(); job.join(timeout=8)
    assert not job.is_alive()
    clip = ReplayStore(tmp_path).get('ep_live', ROBOHOUSE)
    assert clip and clip['video_duration_s'] >= 1
    assert clip['capture_fps'] == 2 and clip['idle_removed_s'] == 0
    assert clip['preview_speed'] == 1 and clip['model'] == running['run_configuration']['model']
    assert ReplayStore(tmp_path).video('ep_live', clip['video_sha256'])[0] == 200
    result = json.loads((tmp_path/'.capture/ep_live/result.json').read_text())
    assert result['stopped_status'] == 'failed'
    assert time.monotonic()-first < 8


def test_replay_ui_autoplays_muted_and_distinguishes_retained_pauses():
    script = runner_script().decode()
    assert 'player.muted = true; player.play()' in script
    assert 'run.idle_removed_s === 0' in script
