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
        # This fixture owns its run lifecycle. End after actual encoded frames,
        # so unrelated encoder/startup load cannot end it before recording starts.
        return dict(running, status='failed' if job.frames >= 3 else 'running')
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


@pytest.mark.skipif(not shutil.which('ffmpeg'), reason='Host encoder is required')
def test_slow_first_frame_does_not_end_the_fixture_before_recording(tmp_path, monkeypatch):
    original = LiveRecording.canvas
    def slow_first_frame(self):
        if self.frames == 0: time.sleep(1.3)
        return original(self)
    monkeypatch.setattr(LiveRecording, 'canvas', slow_first_frame)
    test_live_video_finalizes_on_its_terminal_state_without_native_archive(tmp_path, monkeypatch)


@pytest.mark.skipif(not shutil.which('ffmpeg'), reason='Host encoder is required')
def test_ten_minute_encoder_output_fits_unchanged_shared_replay_limit(tmp_path):
    from spotter_yam.live_replays import encoder_command
    import subprocess
    video = tmp_path/'ten-minute-encoder-fixture.mp4'
    segment = tmp_path/'one-minute-encoder-fixture.mp4'
    # Stress the real native-size encoder with changing noise, then repeat its
    # actual encoded minute without re-encoding. This verifies a600s file and
    # its byte budget, rather than imposing an unrelated fast-encoding target
    # on a shared CPU. Synthetic input only; never physical run evidence.
    command = encoder_command(shutil.which('ffmpeg'), segment, input_args=[
        '-f', 'lavfi', '-i', 'testsrc2=size=960x576:rate=2:duration=60,noise=alls=24:allf=t'])
    subprocess.run(command, check=True, capture_output=True, timeout=60)
    subprocess.run([shutil.which('ffmpeg'),'-y','-loglevel','error','-stream_loop','9',
        '-i',str(segment),'-c','copy','-movflags','+faststart',str(video)],
        check=True,capture_output=True,timeout=60)
    assert 0 < video.stat().st_size < 16*1024*1024
    result = subprocess.run(['ffprobe','-v','error','-show_entries','format=duration',
        '-of','json',str(video)],check=True,capture_output=True,text=True)
    assert float(json.loads(result.stdout)['format']['duration']) == 600
    import hashlib
    from spotter_yam.live_replays import atomic_json
    digest=hashlib.sha256(video.read_bytes()).hexdigest()
    directory=tmp_path/'ep_long';directory.mkdir()
    video.rename(directory/(digest+'.mp4'))
    atomic_json(tmp_path/'ep_long.json',dict(episode_id='ep_long',robot_id=ROBOHOUSE,
        task='Synthetic encoder fixture, not robot footage',bytes=(directory/(digest+'.mp4')).stat().st_size,
        locally_ready_at=time.time(),preview=dict(sha256=digest,duration_s=600,speed=1,camera_order=['top'])))
    store=ReplayStore(tmp_path)
    assert store.get('ep_long',ROBOHOUSE)['video_duration_s']==600
    status,body,headers=store.video('ep_long',digest,'bytes=1024-2047')
    assert status==206 and len(body)==1024


def test_replay_ui_autoplays_muted_and_distinguishes_retained_pauses():
    script = runner_script().decode()
    assert 'player.muted = true; player.play()' in script
    assert 'run.idle_removed_s === 0' in script
