"""Separate Spotter web application built on the pinned Blupe runner."""
import json
import os
from pathlib import Path
from urllib import request

from . import ROOT
from playground import HostedRunner, RequestError
from remote_yam.controller_workspace import workspace_for_robot
from remote_yam.robocurve_trajectory import RoboCurveTrajectory
from remote_yam.yam_runpod_policy import MODELS
from .policy import SpotterAdapter
from .vlm import VisionSupervisor
from .ui import runner_script
from .motion import YAMMotionAdapter

API = 'https://yam-session-api.n5hthc3gj4cqy.us-east-1.cs.amazonlightsail.com'
ASSETS = ROOT / 'blupe/static'


def secret_file(path):
    return Path(path).expanduser().read_text().strip() if path else ''


class SpotterApp(HostedRunner):
    def __init__(self, *, settings=None, **kwargs):
        self.settings = dict(settings or {})
        self.policy_endpoint = self.settings.get('policy_endpoint', '')
        self.policy_key_file = self.settings.get('policy_key_file', '')
        self.vlm_endpoint = self.settings.get('vlm_endpoint', '')
        self.vlm_model = self.settings.get('vlm_model', 'qwen38')
        self.vlm_key_file = self.settings.get('vlm_key_file', '')
        self.max_lead = int(self.settings.get('max_lead', 2))
        self.configured = bool(self.policy_endpoint and self.policy_key_file and self.vlm_endpoint)
        kwargs.setdefault('robot_id', 'yam-1')
        if kwargs['robot_id'] != 'yam-1':
            raise ValueError('The pinned DreamZero checkpoint is qualified for YAM1 only')
        super().__init__(**kwargs)
        # The separate host does not inherit the main playground's media proxy.
        # Use the runner's fresh per-camera transport rather than a missing composite.
        self.video_stream = None
        self.extra_providers.update(spotter=self.make_spotter, dreamzero=self.make_base)
        self.runpod_providers = {
            'spotter': {'label': 'Spotter · DreamZero + ' + self.vlm_model,
                        'model': 'spotter/' + MODELS['dreamzero']['model'],
                        'default_run_duration_s': 300,
                        'help': 'DreamZero leads. Spotter screens in parallel, confirms failures, repairs, then hands control back.'},
            'dreamzero': {'label': 'DreamZero · policy alone', 'model': MODELS['dreamzero']['model'],
                          'default_run_duration_s': 300, 'help': 'The same frozen YAM1 policy without Spotter supervision.'}}

    def require_configured(self):
        if not self.configured:
            raise RequestError(503, 'Spotter model services need configuration on the host. Live cameras remain available.')

    def make_base(self, model, directory):
        self.require_configured()
        if model not in ('', MODELS['dreamzero']['model']):
            raise RequestError(400, 'Unknown DreamZero checkpoint')
        return YAMMotionAdapter(secret_file(self.policy_key_file), provider='dreamzero',
            endpoint=self.policy_endpoint, camera_source=self.camera_source, robot_id=self.robot_id)

    def make_spotter(self, model, directory):
        if model not in ('', 'spotter/' + MODELS['dreamzero']['model']):
            raise RequestError(400, 'Unknown Spotter configuration')
        base = self.make_base('', directory)
        workspace = workspace_for_robot(self.robot_id)
        geometry = RoboCurveTrajectory(**workspace.rgb_geometry_kwargs())
        workspace.configure_geometry(geometry)
        supervisor = VisionSupervisor(self.vlm_endpoint, self.vlm_model, secret_file(self.vlm_key_file))
        def prepare_geometry():
            with request.urlopen(self.camera_origin_value + '/v1/robots/' + self.robot_id + '/calibration', timeout=10) as response:
                report = json.loads(response.read(4 * 1024 * 1024))
            workspace.validate_report(report)
        return SpotterAdapter(base, supervisor, geometry, robot_id=self.robot_id,
                              camera_source=self.camera_source, max_lead=self.max_lead,
                              preparation=prepare_geometry)

    def validate_launch(self, visitor, payload, paid):
        if payload.get('provider') not in ('spotter', 'dreamzero'):
            raise RequestError(400, 'Choose Spotter or the matching DreamZero baseline')
        self.require_configured()
        return super().validate_launch(visitor, payload, paid)

    def page(self):
        page = super().page().decode()
        page = page.replace('<title>BluPe · Run a policy</title>', '<title>Spotter on Blupe · Physical YAM demo</title>')
        page = page.replace('<!-- application-head -->',
                            '<link rel="stylesheet" href="/spotter/site.css"><script src="/spotter/site.js" defer></script>')
        page = page.replace('<span class="consoleProduct">Playground</span>', '<span class="consoleProduct">Spotter</span>')
        start = page.index('  <p class="playgroundIntro">')
        end = page.index('</p>', start) + 4
        page = page[:start] + '''  <p class="playgroundIntro">DreamZero moves. Spotter watches, repairs failures, and hands control back.
<a href="https://arxiv.org/abs/2609.36808" target="_blank" rel="noopener noreferrer">Paper</a> ·
<a href="https://github.com/andlyu/blupe-spotter" target="_blank" rel="noopener noreferrer">Code</a> ·
<a href="https://blupe.io/docs/robot-api/" target="_blank" rel="noopener noreferrer">Robot API</a></p>
<p id="spotterReadiness" class="spotterReadiness" role="status">Checking Spotter configuration…</p>''' + page[end:]
        page = page.replace('Astra decision notes', 'Spotter decisions').replace('Astra’s next note will appear here.', 'Spotter’s observations and repair decisions will appear here.')
        page = page.replace('<script src="/static/camera-preview.js" async fetchpriority="high"></script>', '')
        page = page.replace('<script src="/synchronized/reader.js" defer></script>', '')
        return page.encode()

    async def session_extension(self, cookies, visitor):
        setup, headers = await super().session_extension(cookies, visitor)
        return {**setup, 'spotter': {'configured': self.configured, 'base': 'DreamZero',
                                    'supervisor': self.vlm_model, 'max_lead': self.max_lead}}, headers

    async def public_extension(self, scope, receive, send, headers):
        name = scope.get('path', '')
        if scope.get('method') == 'GET' and name == '/static/hosted.js':
            await self.respond(send, 200, runner_script(), 'text/javascript; charset=utf-8')
            return True
        if scope.get('method') == 'GET' and name in ('/spotter/site.js', '/spotter/site.css'):
            path = ASSETS / name.rsplit('/', 1)[1]
            await self.respond(send, 200, path.read_bytes(), 'text/javascript' if path.suffix == '.js' else 'text/css')
            return True
        return await super().public_extension(scope, receive, send, headers)


def create_app():
    public_origin = os.environ.get('SPOTTER_ORIGIN', 'http://127.0.0.1:8820')
    development = public_origin.startswith('http://127.0.0.1:')
    api = os.environ.get('YAM_SESSION_API', API)
    camera_origin = os.environ.get('YAM_CAMERA_ORIGIN', api)
    settings = {key: os.environ.get('SPOTTER_' + key.upper(), '') for key in
                ('policy_endpoint', 'policy_key_file', 'vlm_endpoint', 'vlm_key_file')}
    settings.update(vlm_model=os.environ.get('SPOTTER_VLM_MODEL', 'qwen38'),
                    max_lead=int(os.environ.get('SPOTTER_MAX_LEAD', '2')))
    app = SpotterApp(settings=settings, public_origin=public_origin, session_api=api,
        camera_origin=camera_origin, development=development,
        hardware_control=True, default_provider='spotter',
        # The shared runner permits durable station recordings only on localhost.
        # Public visitors keep the runner's private, ephemeral per-session storage.
        recording_root=os.environ.get('SPOTTER_RECORDINGS', '/tmp/spotter-recordings') if development else None,
        robots=[{'id': 'yam-1', 'name': 'YAM1 · DreamZero', 'url': public_origin + '/'}],
        share_conversation=False)
    app.camera_origin_value = camera_origin.rstrip('/')
    return app
