"""Lifecycle regressions at Spotter's stateful Dream-1 handoff."""
from types import SimpleNamespace

import pytest

from spotter_yam.dream import SpotterDreamAdapter
from spotter_yam.app import SpotterApp, ROBOHOUSE
from test_spotter import adapter, observation


def test_intervention_invalidates_smoothing_and_defers_sdk_reset(tmp_path):
    base = SpotterDreamAdapter(provider='dream', model='dreamlabs/dream-1-beta',
        credentials='unused', python='unused', directory=tmp_path,
        camera_source=None, observation_source=None, robot_id=ROBOHOUSE)
    base._commanded = {'old': 1}
    base._pending_commanded = {'unexecuted': 1}
    base._worker = SimpleNamespace(call=lambda *a, **k: pytest.fail('Do not reset concurrently with inference'))
    base.supervisor_intervention()
    assert base._commanded is base._pending_commanded is None
    assert base._workspace_reset_pending is True
    assert 'fresh measured state' in base._workspace_feedback


def test_handoff_resets_sdk_before_requesting_fresh_prediction(tmp_path):
    from remote_yam.dream_policy import state_input
    calls = []
    base = SpotterDreamAdapter(provider='dream', model='dreamlabs/dream-1-beta',
        credentials='unused', python='unused', directory=tmp_path,
        camera_source=None, observation_source=None, robot_id=ROBOHOUSE)
    base._ready.set(); base._preparation = base._collector = object()
    base._history.append({'stale': True})
    base._commanded = base._pending_commanded = {'old': True}
    measured = observation(); measured['jetson_id'] = ROBOHOUSE
    tick = {'observation': state_input(measured, 'move'), 'observed_at': measured['observed_at']}
    def fresh_ticks(*args, **kwargs):
        assert calls[0] == 'reset' and not base._history
        calls.append('fresh inputs')
        return [tick]
    def call(kind, **kwargs):
        calls.append(kind)
        if kind == 'reset': return {'ok': True}
        assert kind == 'predict' and kwargs['commanded'] is None
        return {'ok': True, 'result': {'action': {
            key: [[0.]*6+[.5]]*2 for key in ('q_l_chunk', 'q_r_chunk')}}}
    base._worker = SimpleNamespace(call=call)
    base._wait_for_ticks = fresh_ticks
    base.supervisor_intervention()
    points = base.build_trajectory('move', measured, 4)
    assert calls[:3] == ['reset', 'fresh inputs', 'predict']
    assert points[0]['step_id'] == 4


def test_dream_lifecycle_is_forwarded_and_live_camera_history_is_preserved(adapter):
    calls = []
    live_camera = object()
    base = adapter.base
    base.camera_source = live_camera
    base.refresh_observation = None
    base.start_preparation = lambda cancelled: calls.append(('start', cancelled()))
    base.prepare_after_lease = lambda cancelled: calls.append(('lease', cancelled()))
    base.close_transport = lambda: calls.append(('close', True))
    adapter.supervisor.ready = lambda cancelled: calls.append(('supervisor', cancelled()))
    adapter.preparation = lambda: calls.append(('geometry', True))
    adapter.prepare_before_session('move')
    assert [c[0] for c in calls] == ['start', 'supervisor', 'geometry']
    adapter.prepare_after_lease(lambda: False)
    adapter.refresh_observation = lambda: {'fresh': True}
    adapter._connect_base()
    assert base.refresh_observation() == {'fresh': True}
    assert base.camera_source is live_camera and not hasattr(base, '_camera_source')
    adapter.close_transport()
    assert ('lease', False) in calls and ('close', True) in calls
    assert base.cancelled()


def test_every_repair_marks_a_causal_policy_handoff(adapter):
    calls = []
    adapter.base.supervisor_intervention = lambda: calls.append('invalidate')
    adapter._plan('move', {'detected_failure': 'missed'})
    assert calls == ['invalidate']
    assert adapter._repair


def test_robohouse_exposes_only_matching_dream_checkpoint(tmp_path):
    import shutil
    credentials, python = tmp_path/'credentials', tmp_path/'python'
    credentials.touch(); python.touch()
    app = SpotterApp(settings={'dream_credentials_file': str(credentials),
        'dream_python': str(python), 'vlm_endpoint': 'https://vlm.example.com/v1'},
        robot_id=ROBOHOUSE, public_origin='http://127.0.0.1:8821', development=True,
        session_api='', camera_origin='http://127.0.0.1:8089')
    try:
        assert app.configured
        assert set(app.runpod_providers) == {'spotter', 'dream'}
        assert b'Dream-1 moves.' in app.page() and b'DreamZero moves.' not in app.page()
        base = app.make_base('', tmp_path)
        assert isinstance(base, SpotterDreamAdapter)
        assert base.robot_id == ROBOHOUSE
        assert 0 < base.effective_joint_step_deg < 20
        with pytest.raises(Exception, match='Unknown station policy'):
            app.make_base('dreamzero', tmp_path)
        base.close_transport()
    finally:
        shutil.rmtree(app.root)


def test_robohouse_missing_dream_runtime_cannot_start():
    import shutil
    app = SpotterApp(settings={'policy_endpoint': 'https://wrong-yam1.example.com',
        'policy_key_file': 'unused', 'vlm_endpoint': 'https://vlm.example.com/v1'},
        robot_id=ROBOHOUSE, public_origin='http://127.0.0.1:8821', development=True,
        session_api='', camera_origin='http://127.0.0.1:8089')
    try:
        assert app.configured is False
        with pytest.raises(Exception, match='need configuration'):
            app.make_spotter('', '.')
    finally:
        shutil.rmtree(app.root)


def test_managed_supervisor_requires_a_nonempty_key_and_reaches_station_factory(tmp_path, monkeypatch):
    import shutil
    from spotter_yam import app as app_module
    credentials, python, key = (tmp_path / name for name in ('credentials', 'python', 'key'))
    credentials.touch(); python.touch(); key.touch()
    settings = {'dream_credentials_file': str(credentials), 'dream_python': str(python),
        'vlm_endpoint': 'https://openrouter.ai/api/v1', 'vlm_model': 'qwen/qwen3.8-27b',
        'vlm_api_style': 'openrouter', 'vlm_key_file': str(key)}
    for key_value in ('', 'test-key'):
        key.write_text(key_value)
        app = SpotterApp(settings=settings, robot_id=ROBOHOUSE,
            public_origin='http://127.0.0.1:8821', development=True,
            session_api='', camera_origin='http://127.0.0.1:8089')
        try:
            assert app.configured is bool(key_value)
            if not key_value:
                with pytest.raises(Exception, match='need configuration'):
                    app.make_spotter('', tmp_path)
            else:
                # A real station factory, with geometry construction isolated from
                # this HTTP configuration test. No model or hardware request runs.
                monkeypatch.setattr(app_module, 'RoboCurveTrajectory', lambda **kwargs: object())
                monkeypatch.setattr(app_module, 'workspace_for_robot', lambda robot_id: SimpleNamespace(
                    rgb_geometry_kwargs=lambda: {}, configure_geometry=lambda value: None))
                monkeypatch.setattr(app, 'make_base', lambda *args: SimpleNamespace(model='dream-1'))
                adapter = app.make_spotter('', tmp_path)
                try:
                    assert adapter.supervisor.api_style == 'openrouter'
                    assert adapter.supervisor.model == 'qwen/qwen3.8-27b'
                finally:
                    adapter.close_transport()
        finally:
            shutil.rmtree(app.root)


@pytest.fixture
def resident_app(tmp_path, monkeypatch):
    import shutil
    from spotter_yam import app as app_module

    class PreparedPool:
        ready = False
        closed = False
        failure = False
        def __init__(self, *args): pass
        def status(self):
            return {'ready': self.ready, 'busy': False, 'preparing': False,
                    'recovery_attempts': 0, 'recovery_exhausted': False}
        def prime(self, **kwargs):
            if self.failure:
                raise RuntimeError('private provider detail')
            self.ready = True
        def factory(self, *args):
            pytest.fail('Factory must not be invoked before a robot lease')
        def close(self): self.closed = True

    monkeypatch.setattr(app_module, 'DreamWorkerPool', PreparedPool)
    credentials, python = tmp_path/'credentials', tmp_path/'python'
    credentials.touch(); python.touch()
    app = SpotterApp(settings={'dream_credentials_file': str(credentials),
        'dream_python': str(python), 'dream_resident_dir': str(tmp_path/'resident'),
        'vlm_endpoint': 'https://vlm.example.com/v1'}, robot_id=ROBOHOUSE,
        public_origin='http://127.0.0.1:8821', development=True,
        session_api='', camera_origin='http://127.0.0.1:8089')
    try:
        yield app
    finally:
        app.dream_resident.close()
        shutil.rmtree(app.root, ignore_errors=True)


def test_resident_preparation_gates_launch_and_supplies_exclusive_factory(resident_app, tmp_path):
    import asyncio
    app = resident_app
    assert app.configured and not app.runtime_configured()
    with pytest.raises(Exception, match='Dream solver is preparing or unavailable'):
        app.make_base('', tmp_path)
    asyncio.run(app.prepare_dream())
    assert app.runtime_configured()
    base = app.make_base('', tmp_path)
    try:
        assert base.worker_factory == app.dream_resident.factory
        assert base.worker_pool is app.dream_workers  # Still waits for lease.
    finally:
        base.close_transport()
    app.dream_resident.ready = False
    with pytest.raises(Exception, match='Dream solver is preparing or unavailable'):
        app.validate_launch(None, {'provider': 'spotter'}, False)


def test_resident_preparation_failure_stays_unavailable_without_private_errors(resident_app, caplog):
    import asyncio
    app = resident_app
    app.dream_resident.failure = True
    asyncio.run(app.prepare_dream())
    assert not app.runtime_configured()
    assert app.dream_readiness()['preparation_failed']
    assert 'private provider detail' not in caplog.text


def test_resident_lifespan_prepares_in_background_and_closes_pool(resident_app, monkeypatch):
    import asyncio
    app = resident_app

    async def exercise():
        events = asyncio.Queue()
        sent = []
        async def maintenance(): await asyncio.Event().wait()
        monkeypatch.setattr(app, 'maintenance', maintenance)
        async def send(event): sent.append(event['type'])
        runner = asyncio.create_task(app({'type': 'lifespan'}, events.get, send))
        await events.put({'type': 'lifespan.startup'})
        for _ in range(100):
            if app.runtime_configured(): break
            await asyncio.sleep(.01)
        assert app.runtime_configured()
        assert 'lifespan.startup.complete' in sent
        await events.put({'type': 'lifespan.shutdown'})
        await asyncio.wait_for(runner, 2)
        assert app.dream_resident.closed
        assert sent[-1] == 'lifespan.shutdown.complete'

    asyncio.run(exercise())
