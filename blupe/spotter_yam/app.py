"""Separate Spotter web application built on the pinned Blupe runner."""
import asyncio
from contextlib import suppress
import json
import logging
import math
import os
from pathlib import Path
import re
from threading import BoundedSemaphore
import time
from urllib import request

from . import ROOT
from playground import HostedRunner, RequestError
from remote_yam.controller_workspace import workspace_for_robot
from remote_yam.robocurve_trajectory import RoboCurveTrajectory
from remote_yam.yam_runpod_policy import MODELS
from remote_yam.dream_worker_pool import DreamWorkerPool
from .live_replays import LiveReplays, ReplayStore
from .policy import SpotterAdapter
from .vlm import VisionSupervisor
from .ui import runner_script
from .motion import YAMMotionAdapter
from .dream import SpotterDreamAdapter
from .history import ReceiptHistory

API = 'https://yam-session-api.n5hthc3gj4cqy.us-east-1.cs.amazonlightsail.com'
ASSETS = ROOT / 'blupe/static'
ROBOHOUSE = 'robot-ba8413962083809c'
STATIONS = {'yam-1': ('YAM1', 'dreamzero', 'DreamZero', MODELS['dreamzero']['model']),
            ROBOHOUSE: ('Robo-house', 'dream', 'Dream-1', 'dreamlabs/dream-1-beta')}


def secret_file(path):
    return Path(path).expanduser().read_text().strip() if path else ''


class SpotterApp(HostedRunner):
    def __init__(self, *, settings=None, **kwargs):
        self.settings = dict(settings or {})
        self.policy_endpoint = self.settings.get('policy_endpoint', '')
        self.policy_key_file = self.settings.get('policy_key_file', '')
        self.vlm_endpoint = self.settings.get('vlm_endpoint', '')
        self.vlm_model = self.settings.get('vlm_model', 'qwen38')
        self.vlm_api_style = self.settings.get('vlm_api_style', 'vllm')
        self.vlm_key_file = self.settings.get('vlm_key_file', '')
        self.max_lead = int(self.settings.get('max_lead', 2))
        kwargs.setdefault('robot_id', 'yam-1')
        if kwargs['robot_id'] not in STATIONS:
            raise ValueError('Spotter requires a configured YAM1 or Robo-house station')
        self.station_name, self.base_provider, self.base_label, self.base_model = STATIONS[kwargs['robot_id']]
        self.dream_credentials = self.settings.get('dream_credentials_file', '')
        self.dream_python = self.settings.get('dream_python', '')
        self.dream_workers = BoundedSemaphore(1)
        base_configured = (bool(self.policy_endpoint and self.policy_key_file) if self.base_provider == 'dreamzero'
                           else bool(self.dream_credentials and self.dream_python
                                     and Path(self.dream_credentials).is_file() and Path(self.dream_python).is_file()))
        vlm_configured = bool(self.vlm_endpoint and (self.vlm_api_style != 'openrouter'
                              or self.vlm_key_file and Path(self.vlm_key_file).is_file()
                              and secret_file(self.vlm_key_file)))
        self.configured = bool(base_configured and vlm_configured)
        super().__init__(**kwargs)
        self.local_replays = ReplayStore(self.settings.get('replay_root'))
        self.past_runs = ReceiptHistory(self.past_runs, self.run_names, self.robot_id, self.local_replays)
        self.replay_capture = (LiveReplays(self.local_replays.root, kwargs.get('camera_origin', API), self.robot_id)
                               if self.local_replays.root and self.robot_id == ROBOHOUSE else None)
        self.dream_resident = None
        self.dream_preparation_task = None
        self.dream_preparation_failed = False
        resident_dir = self.settings.get('dream_resident_dir', '')
        if self.base_provider == 'dream' and base_configured and resident_dir:
            self.dream_resident = DreamWorkerPool(self.dream_python, self.dream_credentials, resident_dir)
        # The separate host does not inherit the main playground's media proxy.
        # Use the runner's fresh per-camera transport rather than a missing composite.
        self.video_stream = None
        self.extra_providers.update({'spotter': self.make_spotter, self.base_provider: self.make_base})
        self.runpod_providers = {
            'spotter': {'label': 'Spotter · ' + self.base_label + ' + ' + self.vlm_model,
                        'model': 'spotter/' + self.base_model,
                        'default_run_duration_s': 300,
                        'help': self.base_label + ' leads. Spotter screens in parallel, confirms failures, repairs, then hands control back.'},
            self.base_provider: {'label': self.base_label + ' · policy alone', 'model': self.base_model,
                          'default_run_duration_s': 300, 'help': 'The same station policy without Spotter supervision.'}}

    def dream_readiness(self):
        if self.dream_resident is None:
            return None
        state = self.dream_resident.status()
        return {**state, 'preparing': state['preparing'] or bool(
            self.dream_preparation_task and not self.dream_preparation_task.done()),
            'preparation_failed': self.dream_preparation_failed}

    def runtime_configured(self):
        state = self.dream_readiness()
        return self.configured and (state is None or state['ready'])

    async def prepare_dream(self):
        started = time.perf_counter()
        try:
            await asyncio.to_thread(self.dream_resident.prime, timeout=360)
            logging.getLogger(__name__).info('Dream solver prepared in %.3fs', time.perf_counter() - started)
        except Exception as error:
            self.dream_preparation_failed = True
            logging.getLogger(__name__).warning('Dream preparation failed (%s)', type(error).__name__)

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'lifespan' or self.dream_resident is None:
            return await super().__call__(scope, receive, send)

        async def lifecycle_receive():
            event = await receive()
            if event['type'] == 'lifespan.startup' and self.dream_preparation_task is None:
                self.dream_preparation_task = asyncio.create_task(self.prepare_dream())
            return event

        try:
            await super().__call__(scope, lifecycle_receive, send)
        finally:
            # The parent drains visitors first. Pool cleanup also interrupts an
            # unfinished prime; cancelled inference replies are never lent out.
            if self.replay_capture:
                await asyncio.to_thread(self.replay_capture.close)
            await asyncio.to_thread(self.dream_resident.close)
            if self.dream_preparation_task:
                self.dream_preparation_task.cancel()
                with suppress(asyncio.CancelledError):
                    await self.dream_preparation_task

    def require_configured(self):
        if not self.configured:
            raise RequestError(503, 'Spotter model services need configuration on the host. Live cameras remain available.')
        if not self.runtime_configured():
            raise RequestError(503, 'Dream solver is preparing or unavailable. Live cameras remain available; try again when the page reports ready.')

    def launch(self, visitor, payload, **kwargs):
        result = super().launch(visitor, payload, **kwargs)
        visitor.spotter_attempt_id = result.get('attempt_id')
        return result

    def remember_runner(self, visitor):
        # Prequeue preparation has no session ID at launch return. Associate
        # only the same visitor-owned attempt once its session exists.
        with visitor.lock:
            state = visitor.controller.status()
            attempt = getattr(visitor, 'spotter_attempt_id', None)
            if (attempt and attempt == state.get('attempt_id') and state.get('session_id')
                    and not visitor.runner_session_id):
                visitor.runner_session_id = state['session_id']
        result = super().remember_runner(visitor)
        capture = getattr(self, 'replay_capture', None)
        if capture:
            # Capture only a visitor-owned running episode. The background job
            # watches this controller's read-only status even after the tab closes.
            capture.observe(state, visitor.runner_session_id, visitor.runner_task,
                            visitor.runner_name, visitor.controller.status)
        return result

    def make_base(self, model, directory):
        self.require_configured()
        if model not in ('', self.base_model):
            raise RequestError(400, 'Unknown station policy checkpoint')
        if self.base_provider == 'dream':
            limits = workspace_for_robot(self.robot_id)._safety()
            step = .9 * math.degrees(min(limits['max_adjacent_delta_rad'], limits['max_joint_velocity_rad_s'] / 10))
            return SpotterDreamAdapter(provider='dream', model=self.base_model,
                credentials=self.dream_credentials, python=self.dream_python,
                directory=Path(directory) / 'dream-sdk', camera_source=self.camera_source,
                observation_source=lambda: self.monitor_api.get_robot_observation(self.robot_id),
                robot_id=self.robot_id, gateway_max_step_deg=step, worker_pool=self.dream_workers,
                **({'worker_factory': self.dream_resident.factory} if self.dream_resident else {}))
        return YAMMotionAdapter(secret_file(self.policy_key_file), provider='dreamzero',
            endpoint=self.policy_endpoint, camera_source=self.camera_source, robot_id=self.robot_id)

    def make_spotter(self, model, directory):
        if model not in ('', 'spotter/' + self.base_model):
            raise RequestError(400, 'Unknown Spotter configuration')
        base = self.make_base('', directory)
        workspace = workspace_for_robot(self.robot_id)
        geometry = RoboCurveTrajectory(**workspace.rgb_geometry_kwargs())
        workspace.configure_geometry(geometry)
        supervisor = VisionSupervisor(self.vlm_endpoint, self.vlm_model, secret_file(self.vlm_key_file),
                                      api_style=self.vlm_api_style)
        def prepare_geometry():
            with request.urlopen(self.camera_origin_value + '/v1/robots/' + self.robot_id + '/calibration', timeout=10) as response:
                report = json.loads(response.read(4 * 1024 * 1024))
            workspace.validate_report(report)
        return SpotterAdapter(base, supervisor, geometry, robot_id=self.robot_id,
                              camera_source=self.camera_source, max_lead=self.max_lead,
                              preparation=prepare_geometry)

    def validate_launch(self, visitor, payload, paid):
        if payload.get('provider') not in ('spotter', self.base_provider):
            raise RequestError(400, 'Choose Spotter or the matching station policy baseline')
        self.require_configured()
        return super().validate_launch(visitor, payload, paid)

    def page(self):
        page = super().page().decode()
        page = page.replace('<title>BluPe · Run a policy</title>', '<title>Spotter on Blupe · ' + self.station_name + '</title>')
        page = page.replace('<!-- application-head -->',
                            '<link rel="stylesheet" href="/spotter/site.css"><script src="/spotter/site.js" defer></script>')
        page = page.replace('<span class="consoleProduct">Playground</span>', '<span class="consoleProduct">Spotter</span>')
        start = page.index('  <p class="playgroundIntro">')
        end = page.index('</p>', start) + 4
        page = page[:start] + ('  <p class="playgroundIntro">' + self.base_label + ''' moves. Spotter watches, repairs failures, and hands control back.
<a href="https://arxiv.org/abs/2609.36808" target="_blank" rel="noopener noreferrer">Paper</a> ·
<a href="https://github.com/andlyu/blupe-spotter" target="_blank" rel="noopener noreferrer">Code</a> ·
<a href="https://blupe.io/docs/robot-api/" target="_blank" rel="noopener noreferrer">Robot API</a></p>
<p id="spotterReadiness" class="spotterReadiness" role="status">Checking Spotter configuration…</p>''') + page[end:]
        page = page.replace('Astra decision notes', 'Spotter decisions').replace('Astra’s next note will appear here.', 'Spotter’s observations and repair decisions will appear here.')
        page = page.replace('<script src="/static/camera-preview.js" async fetchpriority="high"></script>', '')
        page = page.replace('<script src="/synchronized/reader.js" defer></script>', '')
        return page.encode()

    async def session_extension(self, cookies, visitor):
        setup, headers = await super().session_extension(cookies, visitor)
        return {**setup, 'spotter': {'configured': self.runtime_configured(), 'base': self.base_label,
                                    'base_provider': self.base_provider, 'station': self.station_name,
                                    'stations': self.robots,
                                    'supervisor': self.vlm_model, 'max_lead': self.max_lead,
                                    'dream_runtime': self.dream_readiness()}}, headers

    async def public_extension(self, scope, receive, send, headers):
        name = scope.get('path', '')
        clip = re.fullmatch(r'/api/quick-replays/(ep_[A-Za-z0-9_-]{1,100})/([0-9a-f]{64})\.mp4', name)
        if scope.get('method') == 'GET' and clip:
            eid, digest = clip.groups()
            # Only this station's atomically installed metadata can expose media.
            ready = self.local_replays.get(eid, self.robot_id)
            result = (await asyncio.to_thread(self.local_replays.video, eid, digest, headers.get('range'))
                      if ready and ready['video_sha256'] == digest else None)
            if result is None:
                await self.json(send, 404, {'error': 'Replay not available'})
            else:
                status, body, extra = result
                await self.respond(send, status, body, 'video/mp4', extra)
            return True
        if scope.get('method') == 'GET' and name == '/spotter/readiness':
            await self.json(send, 200, {'configured': self.runtime_configured(),
                                      'dream_runtime': self.dream_readiness()})
            return True
        if scope.get('method') == 'GET' and name == '/static/hosted.js':
            await self.respond(send, 200, runner_script(), 'text/javascript; charset=utf-8')
            return True
        if scope.get('method') == 'GET' and name in ('/spotter/site.js', '/spotter/site.css'):
            path = ASSETS / name.rsplit('/', 1)[1]
            await self.respond(send, 200, path.read_bytes(), 'text/javascript' if path.suffix == '.js' else 'text/css')
            return True
        return await super().public_extension(scope, receive, send, headers)

    async def start_response(self, send, status, content_type, size, extra=()):
        async def local_media(message):
            if message['type'] == 'http.response.start':
                message = dict(message, headers=[(key, value.replace(
                    b'media-src https://huggingface.co', b"media-src 'self' https://huggingface.co"))
                    if key == b'content-security-policy' else (key, value)
                    for key, value in message['headers']])
            await send(message)
        await super().start_response(local_media, status, content_type, size, extra)


def create_app():
    public_origin = os.environ.get('SPOTTER_ORIGIN', 'http://127.0.0.1:8820')
    development = public_origin.startswith('http://127.0.0.1:')
    api = os.environ.get('YAM_SESSION_API', API)
    camera_origin = os.environ.get('YAM_CAMERA_ORIGIN', api)
    settings = {key: os.environ.get('SPOTTER_' + key.upper(), '') for key in
                ('policy_endpoint', 'policy_key_file', 'vlm_endpoint', 'vlm_key_file')}
    settings.update(vlm_model=os.environ.get('SPOTTER_VLM_MODEL', 'qwen38'),
                    vlm_api_style=os.environ.get('SPOTTER_VLM_API_STYLE', 'vllm'),
                    max_lead=int(os.environ.get('SPOTTER_MAX_LEAD', '2')),
                    dream_credentials_file=os.environ.get('SPOTTER_DREAM_CREDENTIALS_FILE', ''),
                    dream_python=os.environ.get('SPOTTER_DREAM_PYTHON', ''),
                    dream_resident_dir=os.environ.get('SPOTTER_DREAM_RESIDENT_DIR', ''),
                    replay_root=os.environ.get('SPOTTER_REPLAY_ROOT', ''))
    robot_id = os.environ.get('SPOTTER_ROBOT_ID', 'yam-1')
    robots = [{'id': robot_id, 'name': STATIONS[robot_id][0], 'url': public_origin + '/'}]
    other_origin = os.environ.get('SPOTTER_OTHER_STATION_ORIGIN', '')
    if other_origin:
        other_id = ROBOHOUSE if robot_id == 'yam-1' else 'yam-1'
        robots.append({'id': other_id, 'name': STATIONS[other_id][0], 'url': other_origin.rstrip('/') + '/'})
    app = SpotterApp(settings=settings, public_origin=public_origin, session_api=api,
        camera_origin=camera_origin, development=development,
        hardware_control=True, default_provider='spotter', robot_id=robot_id,
        # The shared runner permits durable station recordings only on localhost.
        # Public visitors keep the runner's private, ephemeral per-session storage.
        recording_root=os.environ.get('SPOTTER_RECORDINGS', '/tmp/spotter-recordings') if development else None,
        robots=robots,
        share_conversation=False)
    app.camera_origin_value = camera_origin.rstrip('/')
    return app
