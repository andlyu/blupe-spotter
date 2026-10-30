"""Encode timestamped public-camera frames during an owned physical run.

No lease or motion is requested here. Finalization does not wait for the native
recorder's transfer or archive upload. Native recordings remain separate.
"""
import hashlib
import fcntl
import io
import json
import logging
import math
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import threading
import time

from remote_yam.aspire_review_recording import SessionReviewRecorder
from remote_yam.quick_replays import QuickReplays

LOG = logging.getLogger(__name__)
ROLES = ('left', 'top', 'right')
TERMINAL = {'stopped', 'completed', 'failed', 'error', 'timed_out', 'cancelled',
            'ended', 'safety_aborted', 'disconnected'}


def atomic_json(path, value):
    temporary = path.with_suffix('.partial.json')
    temporary.write_text(json.dumps(value, allow_nan=False) + '\n')
    temporary.replace(path)


class ReplayStore(QuickReplays):
    def get(self, eid, robot_id=None):
        row = super().get(eid, robot_id)
        if row:
            try:
                preview = json.loads((self.root/(eid+'.json')).read_text())['preview']
                idle = preview.get('idle_removed_s')
                if type(idle) in (int, float) and math.isfinite(idle) and idle >= 0:
                    row['idle_removed_s'] = idle
                if preview.get('capture_source') == 'public-camera-api':
                    row['capture_fps'] = preview['fps']
            except (OSError, ValueError, KeyError, TypeError):
                pass
        return row


class LiveReplays:
    def __init__(self, root, origin, robot_id, *, job_factory=None):
        self.root, self.origin, self.robot_id = Path(root), origin.rstrip('/'), robot_id
        self._jobs, self._lock, self._closed = {}, threading.Lock(), False
        self.job_factory = job_factory or LiveRecording

    def observe(self, state, owner_session, task, runner, read_state):
        eid, session = state.get('episode_id'), state.get('session_id')
        if (state.get('status') != 'running' or not owner_session or session != owner_session
                or not re.fullmatch(r'ep_[A-Za-z0-9_-]{1,100}', eid or '')
                or type(state.get('run_started_at')) not in (int, float)):
            return
        with self._lock:
            if self._closed or eid in self._jobs or (self.root/(eid+'.json')).exists():
                return
            for old, job in list(self._jobs.items()):
                if len(self._jobs) <= 64:
                    break
                if not job.is_alive():
                    self._jobs.pop(old)
            job = self.job_factory(self.root, self.origin, self.robot_id, dict(state),
                                   task, runner, read_state)
            self._jobs[eid] = job
            job.start()

    def close(self):
        with self._lock:
            self._closed = True
            jobs = list(self._jobs.values())
        for job in jobs:
            job.stop.set()
        for job in jobs:
            job.join(timeout=4)
            job.terminate_encoder()


class LiveRecording(threading.Thread):
    def __init__(self, root, origin, robot_id, state, task, runner, read_state):
        super().__init__(name='spotter-replay-'+state['episode_id'], daemon=True)
        self.root, self.origin, self.robot_id = root, origin, robot_id
        self.state, self.task, self.runner, self.read_state = state, task, runner, read_state
        self.stop, self._lock, self._latest = threading.Event(), threading.Lock(), {}
        self.encoder = None
        self.ended = dict(state)
        self.frames, self.received = 0, set()

    def terminate_encoder(self):
        if self.encoder and self.encoder.poll() is None:
            self.encoder.kill()

    def accept(self, frame):
        captured = frame.source_captured_at or frame.received_at
        # Do not attach pre-run images or implausible/future timestamps to a run.
        if (frame.name not in ROLES or not math.isfinite(captured)
                or captured < self.state['run_started_at']-.25
                or captured > time.time()+1):
            return
        with self._lock:
            self._latest[frame.name] = frame
            self.received.add(frame.name)

    def canvas(self):
        from PIL import Image, ImageDraw
        image = Image.new('RGB', (960, 576), '#171b20')
        draw = ImageDraw.Draw(image)
        with self._lock:
            frames = dict(self._latest)
        for name, box in (('top', (0, 18, 960, 540)),
                          ('left', (8, 446, 176, 99)), ('right', (776, 446, 176, 99))):
            x, y, width, height = box
            frame = frames.get(name)
            fresh = frame and time.time()-frame.received_at <= 3
            if fresh:
                with Image.open(io.BytesIO(frame.jpeg)) as source:
                    tile = source.convert('RGB')
                    tile.thumbnail((width, height))
                image.paste(tile, (x+(width-tile.width)//2, y+(height-tile.height)//2))
            else:
                draw.rectangle((x, y, x+width, y+height), fill='#171b20')
                draw.text((x+5, y+height//2), 'NO FRESH FRAME', fill='white')
            if name != 'top':
                draw.rectangle((x, y+height, x+width, y+height+18), fill='#171b20')
                draw.text((x+4, y+height+3), name.upper()+' WRIST', fill='white')
        elapsed = max(0, time.time()-self.state['run_started_at'])
        draw.text((8, 4), f'TOP | {elapsed:.1f}s | 2 fps camera API recording', fill='white')
        return image.tobytes()

    def run(self):
        eid, session = self.state['episode_id'], self.state['session_id']
        directory = self.root/'.capture'/eid
        recorder = None
        started = time.time()
        try:
            directory.mkdir(parents=True, exist_ok=False, mode=0o700)
            atomic_json(directory/'identity.json', dict(episode_id=eid, session_id=session,
                robot_id=self.robot_id, task=self.task, started_at=self.state['run_started_at'],
                capture_started_at=started, capture_source='public-camera-api'))
            urls = {role:self.origin+f'/v1/robots/{self.robot_id}/cameras/{role}.jpg' for role in ROLES}
            recorder = SessionReviewRecorder(self.origin, urls, directory/'frames',
                                             interval_s=.5, sink=self.accept)
            recorder.start()
            encoder = shutil.which('ffmpeg')
            if not encoder:
                raise RuntimeError('FFmpeg unavailable')
            partial = directory/'recording.partial.mp4'
            with tempfile.TemporaryFile() as errors:
                self.encoder = subprocess.Popen([encoder, '-y', '-loglevel', 'error',
                    '-f', 'rawvideo', '-pixel_format', 'rgb24', '-video_size', '960x576',
                    '-framerate', '2', '-i', '-', '-an', '-c:v', 'libx264', '-threads', '1',
                    '-preset', 'ultrafast', '-crf', '25', '-pix_fmt', 'yuv420p',
                    '-movflags', '+faststart', str(partial)], stdin=subprocess.PIPE,
                    stdout=subprocess.DEVNULL, stderr=errors)
                deadline = time.monotonic()+615
                while not self.stop.is_set() and time.monotonic() < deadline:
                    tick = time.monotonic()
                    state = self.read_state()
                    if (state.get('episode_id') != eid or state.get('session_id') != session
                            or state.get('status') in TERMINAL):
                        self.ended = state
                        break
                    # Wait for actual post-start frames before beginning video.
                    if set(ROLES) <= self.received:
                        self.encoder.stdin.write(self.canvas())
                        self.frames += 1
                    self.stop.wait(max(0, .5-(time.monotonic()-tick)))
                recorder.close()
                recorder = None
                self.encoder.stdin.close()
                if self.encoder.wait(timeout=10) != 0 or self.frames < 2:
                    raise RuntimeError('No playable recorded frames')
            if self.stop.is_set():
                raise RuntimeError('Capture interrupted; no final replay published')
            body = partial.read_bytes()
            if not 0 < len(body) <= 16*1024*1024:
                raise RuntimeError('Replay exceeds serving limit')
            digest = hashlib.sha256(body).hexdigest()
            target = self.root/eid
            target.mkdir(parents=True, exist_ok=True, mode=0o700)
            partial.replace(target/(digest+'.mp4'))
            ended_at = time.time()
            configuration = self.state.get('run_configuration') or {}
            entry = dict(episode_id=eid, robot_id=self.robot_id, task=self.task,
                model=configuration.get('model'), runner_name=self.runner,
                started_at=self.state['run_started_at'], ended_at=ended_at,
                outcome='user_requested', original_available=False, bytes=len(body),
                locally_ready_at=ended_at, preview=dict(sha256=digest, quality_stage='final',
                    fps=2, frames=self.frames, duration_s=self.frames/2, speed=1,
                    idle_removed_s=0, camera_order=list(ROLES), layout='top-with-grippers',
                    capture_source='public-camera-api', capture_started_at=started,
                    capture_ended_at=ended_at))
            with (self.root/'.install.lock').open('a') as lock:
                fcntl.flock(lock, fcntl.LOCK_EX)
                if not ReplayStore(self.root).get(eid, self.robot_id):
                    atomic_json(self.root/(eid+'.json'), entry)
            atomic_json(directory/'result.json', dict(status='ready', episode_id=eid,
                frames=self.frames, ready_at=ended_at, stopped_status=self.ended.get('status'),
                video_sha256=digest))
            LOG.warning('Spotter replay ready episode=%s frames=%d', eid, self.frames)
        except Exception as error:
            LOG.warning('Spotter replay unavailable episode=%s cause=%s', eid, type(error).__name__)
            if directory.is_dir():
                atomic_json(directory/'result.json', dict(status='unavailable',
                    episode_id=eid, error_type=type(error).__name__))
        finally:
            if recorder:
                recorder.close()
            self.terminate_encoder()
            if self.encoder and self.encoder.stdin and not self.encoder.stdin.closed:
                self.encoder.stdin.close()
            with self._lock:
                self._latest.clear()
