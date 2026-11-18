"""Deployment lifecycle regressions: no model/network/robot calls."""
import io
import json
from pathlib import Path
import tarfile
from threading import Event, Thread

import pytest

from deploy.auto_deploy import Deployer, atomic_json, link, sha, unpack
from spotter_yam.deployment import DeploymentPaused, DeploymentState

OLD, NEW = '1' * 40, '2' * 40


@pytest.fixture
def deployer(tmp_path):
    root = tmp_path / 'deploy'; root.mkdir()
    for name, revision in [('old', OLD), ('new', NEW)]:
        (root / name).mkdir()
        (root / name / 'RELEASE.json').write_text(json.dumps({'commit': revision}))
    link(root / 'current', root / 'old'); link(root / 'last-good', root / 'old')
    clock = [0.]
    d = Deployer(dict(root=str(root), state_file=str(tmp_path / 'maintenance.json'),
                     drain_timeout_s=5, health_timeout_s=5),
                 clock=lambda: clock[0], sleep=lambda seconds: clock.__setitem__(0, clock[0]+seconds))
    d.main_sha = lambda: NEW
    d.restart = lambda: None
    d.public_health = lambda: {'revision': NEW, 'ready': True}
    return d


def test_success_waits_for_busy_and_pending_launch_then_promotes_exact_revision(deployer):
    d = deployer
    states = iter([{'active_runs': 1, 'launches': 0}, {'active_runs': 0, 'launches': 0},
                   {'active_runs': 0, 'launches': 1}, {'active_runs': 0, 'launches': 0},
                   {'active_runs': 0, 'launches': 0}])
    d.config['drain_timeout_s'] = 20
    d.health = lambda: next(states)
    observed = []
    d.wait_ready = lambda revision: observed.append((revision, d.current.resolve().name))
    d.promote(d.root / 'new', NEW)
    assert observed == [(NEW, 'new')]
    assert d.good.resolve().name == 'new' and not d.maintenance.exists()


@pytest.mark.parametrize('failure', ['wrong_revision', 'not_ready', 'health_error'])
def test_readiness_failure_restores_previous_release_and_reports_failure(deployer, failure):
    d = deployer
    d.wait_idle = lambda: None
    calls = []
    def ready(revision):
        calls.append(revision)
        if revision == NEW:
            raise RuntimeError(failure)
    d.wait_ready = ready
    with pytest.raises(RuntimeError, match=failure): d.promote(d.root / 'new', NEW)
    assert calls == [NEW, OLD]
    assert d.current.resolve().name == 'old' and d.good.resolve().name == 'old'
    assert not d.maintenance.exists()


def test_failed_rollback_keeps_admission_paused(deployer):
    d = deployer; d.wait_idle = lambda: None
    d.wait_ready = lambda revision: (_ for _ in ()).throw(RuntimeError('unhealthy'))
    with pytest.raises(RuntimeError): d.promote(d.root / 'new', NEW)
    assert d.maintenance.exists() and d.current.resolve().name == 'old'


def test_busy_timeout_never_restarts_or_swaps(deployer):
    d = deployer
    d.health = lambda: {'active_runs': 1, 'launches': 0}
    d.restart = lambda: pytest.fail('active run interrupted')
    with pytest.raises(RuntimeError, match='Active runs'): d.promote(d.root / 'new', NEW)
    assert d.current.resolve().name == 'old' and not d.maintenance.exists()


def test_unknown_status_fails_closed_before_restart(deployer):
    d = deployer
    d.health = lambda: (_ for _ in ()).throw(RuntimeError('status unavailable'))
    d.restart = lambda: pytest.fail('unknown status must not restart')
    with pytest.raises(RuntimeError, match='unavailable'): d.promote(d.root / 'new', NEW)
    assert d.current.resolve().name == 'old'


def test_superseded_commit_does_not_swap(deployer):
    d = deployer; d.wait_idle = lambda: None; d.main_sha = lambda: '3' * 40
    d.restart = lambda: pytest.fail('superseded deployment')
    d.promote(d.root / 'new', NEW)
    assert d.current.resolve().name == 'old' and not d.maintenance.exists()


def test_health_requires_matching_ready_revision(deployer):
    d = deployer
    states = iter([{'revision': OLD, 'ready': True}, {'revision': NEW, 'ready': False},
                   {'revision': NEW, 'ready': True}])
    d.config['health_timeout_s'] = 20; d.health = lambda: next(states)
    assert d.wait_ready(NEW) == {'revision': NEW, 'ready': True}


def test_public_site_must_report_the_new_revision_too(deployer):
    d = deployer
    d.health = lambda: {'revision': NEW, 'ready': True}
    d.public_health = lambda: {'revision': OLD, 'ready': True}
    with pytest.raises(RuntimeError, match='exact revision'): d.wait_ready(NEW)


def test_admission_pause_does_not_cancel_an_inflight_launch(tmp_path):
    state = DeploymentState(tmp_path / 'state.json', OLD, lambda: 0)
    entered, release = Event(), Event()
    def pending():
        with state.admission(): entered.set(); assert release.wait(2)
    thread = Thread(target=pending); thread.start(); assert entered.wait(2)
    try:
        atomic_json(state.path, {'phase': 'draining', 'message': 'Updating'})
        assert state.health(True)['launches'] == 1
        with pytest.raises(DeploymentPaused):
            with state.admission(): pytest.fail('new launch admitted')
        assert thread.is_alive()
    finally:
        release.set(); thread.join(2)
    assert state.health(True)['launches'] == 0


def test_corrupt_state_pauses_new_launch_and_disabled_gate_stays_compatible(tmp_path):
    path = tmp_path / 'state'; path.write_text('incomplete JSON')
    state = DeploymentState(path, OLD, lambda: 2)
    assert state.health(False)['active_runs'] == 2
    with pytest.raises(DeploymentPaused):
        with state.admission(): pass
    with DeploymentState(None, OLD, lambda: 0).admission(): pass


@pytest.mark.parametrize('value', ['', 'main', '../main', NEW + '; reboot', 'A' * 40])
def test_only_full_hex_revisions_are_accepted(value):
    with pytest.raises(ValueError): sha(value)


@pytest.mark.parametrize('name,kind', [('repo/../../outside', 'file'), ('repo/link', 'symlink'),
                                       ('/outside', 'file'), ('repo/device', 'device')])
def test_archive_cannot_write_links_devices_or_outside_its_release(tmp_path, name, kind):
    body = io.BytesIO()
    with tarfile.open(fileobj=body, mode='w:gz') as archive:
        info = tarfile.TarInfo(name)
        if kind == 'symlink': info.type = tarfile.SYMTYPE; info.linkname = '/etc/passwd'
        elif kind == 'device': info.type = tarfile.CHRTYPE
        else: info.size = 1
        archive.addfile(info, io.BytesIO(b'x') if kind == 'file' else None)
    with pytest.raises(ValueError): unpack(body.getvalue(), tmp_path / 'release')
    assert not (tmp_path / 'outside').exists()


def test_actual_queue_snapshot_counts_waiting_and_active_entries():
    assert Deployer.queued({'entries': [], 'public_run': None}) == 0
    assert Deployer.queued({'entries': [{'status': 'queued'}], 'public_run': None}) == 1
    assert Deployer.queued({'entries': [], 'public_run': {'status': 'running'}}) == 1
    with pytest.raises(ValueError): Deployer.queued({'unknown': True})


def test_preflight_failure_never_enters_promotion(deployer):
    d = deployer
    d.stage = lambda revision: (_ for _ in ()).throw(RuntimeError('preflight failed'))
    d.promote = lambda *args: pytest.fail('failing gate activated')
    with pytest.raises(RuntimeError, match='preflight'): d.deploy(NEW)
    assert d.current.resolve().name == 'old' and not d.maintenance.exists()


def test_real_launch_wrapper_rejects_maintenance_before_parent_dispatch(tmp_path, monkeypatch):
    from types import SimpleNamespace
    from playground import HostedRunner, RequestError
    from spotter_yam.app import SpotterApp
    app = object.__new__(SpotterApp)
    app.deployment = DeploymentState(tmp_path / 'state', OLD, lambda: 0)
    atomic_json(app.deployment.path, {'phase': 'draining'})
    monkeypatch.setattr(HostedRunner, 'launch', lambda *a, **k: pytest.fail('launch reached parent'))
    with pytest.raises(RequestError, match='updating'):
        app.launch(SimpleNamespace(), {'provider': 'dream'})


def test_public_health_route_contains_revision_and_counts_without_identity(tmp_path):
    import asyncio
    from spotter_yam.app import SpotterApp
    app = object.__new__(SpotterApp)
    app.deployment = DeploymentState(tmp_path / 'state', NEW, lambda: 1)
    app.runtime_configured = lambda: True
    replies = []
    async def reply(send, code, data): replies.append((code, data))
    app.json = reply
    assert asyncio.run(app.public_extension({'method': 'GET', 'path': '/spotter/health'}, None, None, {}))
    assert replies[0][0] == 200
    data = replies[0][1]
    assert data['revision'] == NEW and data['active_runs'] == 1 and data['ready']
    assert set(data) == {'ok', 'revision', 'ready', 'active_runs', 'launches', 'deployment'}


@pytest.mark.parametrize('status', [401, 404])
def test_only_bootstrap_can_use_legacy_status_instead_of_health(deployer, status):
    from urllib.error import HTTPError
    d = deployer
    manifest = d.current / 'RELEASE.json'
    manifest.write_text(json.dumps({'commit': OLD, 'bootstrap': True}))
    def web(path, **kwargs):
        if path == '/spotter/health': raise HTTPError('offline', status, 'old route', {}, None)
        if path == '/api/session': return {}
        if path == '/api/status': return {'whats_running': [], 'queue_snapshot': {'entries': []}}
        if path == '/spotter/readiness': return {'configured': True}
        raise AssertionError(path)
    d.web = web
    assert d.health() == dict(ok=True, revision=OLD, ready=True, active_runs=0, launches=0)
    manifest.write_text(json.dumps({'commit': OLD}))
    with pytest.raises(RuntimeError, match='no deployment health'): d.health()


def test_pull_poller_skips_healthy_current_release_but_not_leftover_pause(deployer):
    from deploy.poll_main import poll
    d = deployer; d.main_sha = lambda: OLD
    d.health = lambda: dict(revision=OLD, ready=True)
    calls=[]; d.deploy=lambda revision:calls.append(revision)
    assert poll(d) == 'current' and not calls
    atomic_json(d.maintenance, {'phase': 'interrupted'})
    assert poll(d) == 'deployed' and calls == [OLD]


def test_failing_source_is_not_repeatedly_activated_by_the_timer(deployer):
    from deploy.poll_main import poll
    d = deployer
    d.deploy = lambda revision: (_ for _ in ()).throw(RuntimeError('preflight failed'))
    with pytest.raises(RuntimeError): poll(d)
    calls=[]; d.deploy=lambda revision:calls.append(revision)
    assert poll(d).startswith('failed;') and not calls
    assert poll(d, retry=True) == 'deployed' and calls == [NEW]


def test_github_waiter_checks_public_revision_and_reports_failed_gate():
    from deploy.wait_for_deploy import wait
    def ready(url): return {'revision': NEW, 'ready': True}
    assert wait(NEW, fetch=ready) == 0
    def failed(url):
        if url.endswith('/health'): return {'revision': OLD, 'ready': True}
        return {'revision': NEW, 'phase': 'failed', 'message': 'preflight failed'}
    assert wait(NEW, fetch=failed) == 1


def test_github_waiter_does_not_claim_success_from_generic_health():
    from deploy.wait_for_deploy import wait
    clock=[0.]
    def fetch(url):
        if 'api.github.com' in url:return {'object':{'sha':NEW}}
        return {'revision':OLD,'ready':True,'phase':'warming'}
    assert wait(NEW,fetch=fetch,clock=lambda:clock[0],
                sleep=lambda seconds:clock.__setitem__(0,clock[0]+seconds),timeout=20)==1
