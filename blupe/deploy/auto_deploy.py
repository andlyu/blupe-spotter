#!/usr/bin/env python3
"""Fixed-target Robo-house deployment entry point, installed outside releases.

Called by a forced-command SSH key, never by a robot controller. The GitHub
workflow supplies only the requested main commit. No model/session credential
is supplied to the workflow or loaded into the offline preflight environment.
"""
import fcntl
import hashlib
import http.cookies
import io
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import tarfile
import tempfile
import time
from urllib import error, request

REPO = 'andlyu/blupe-spotter'
SERVICE = 'blupe-spotter-robohouse.service'
HOST = 'robohouse.spotter.54.209.185.15.sslip.io'
DEPENDENCIES = {'blupe/vendor/remote-yam': 'andlyu/blupe-remote-yam',
                'upstream/Spotter': 'zqc3117/Spotter'}
MAX_ARCHIVE = 50 * 1024 * 1024


def sha(value):
    if not isinstance(value, str) or not re.fullmatch('[0-9a-f]{40}', value):
        raise ValueError('A full lowercase commit SHA is required')
    return value


def atomic_json(path, value):
    path = Path(path)
    with tempfile.NamedTemporaryFile(mode='w', dir=path.parent, delete=False) as stream:
        json.dump(value, stream, indent=2)
        stream.flush()
        os.fsync(stream.fileno())
        temp = Path(stream.name)
    temp.chmod(0o644)
    os.replace(temp, path)


def link(path, target):
    path, target = Path(path), Path(target)
    temporary = path.with_name(path.name + '.next')
    temporary.unlink(missing_ok=True)
    temporary.symlink_to(target, target_is_directory=True)
    os.replace(temporary, path)


def unpack(data, destination):
    """Bound archive sizes and reject links/devices/traversal before extraction."""
    destination = Path(destination)
    with tarfile.open(fileobj=io.BytesIO(data), mode='r:gz') as archive:
        entries = archive.getmembers()
        if len(entries) > 20000 or sum(x.size for x in entries) > 250 * 1024 * 1024:
            raise ValueError('Source archive exceeds its extraction limit')
        roots = set()
        for entry in entries:
            parts = Path(entry.name).parts
            if not parts or Path(entry.name).is_absolute() or '..' in parts:
                raise ValueError('Unsafe source archive path')
            if not (entry.isfile() or entry.isdir()):
                raise ValueError('Source archive links/devices are not accepted')
            roots.add(parts[0])
        if len(roots) != 1:
            raise ValueError('Source archive needs one repository root')
        destination.mkdir(parents=True, exist_ok=False)
        for entry in entries:
            parts = Path(entry.name).parts[1:]
            if not parts:
                continue
            target = destination.joinpath(*parts)
            if entry.isdir():
                target.mkdir(parents=True, exist_ok=True)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                with archive.extractfile(entry) as source:
                    target.write_bytes(source.read())
                target.chmod(0o755 if entry.mode & 0o111 else 0o644)


class Deployer:
    def __init__(self, config, *, clock=time.monotonic, sleep=time.sleep):
        self.config, self.clock, self.sleep = config, clock, sleep
        self.root = Path(config['root'])
        self.current, self.good = self.root / 'current', self.root / 'last-good'
        self.maintenance = Path(config['state_file'])
        self.cookie = ''

    def emit(self, phase, message, **details):
        event = dict(at=time.time(), phase=phase, message=message, **details)
        print(json.dumps(event), flush=True)
        return event

    @staticmethod
    def github(repo, route):
        req = request.Request('https://api.github.com/repos/' + repo + '/' + route,
            headers={'Accept': 'application/vnd.github+json', 'Cache-Control': 'no-cache',
                     'User-Agent': 'blupe-spotter-deploy'})
        with request.urlopen(req, timeout=30) as response:
            return json.loads(response.read(8 * 1024 * 1024))

    def main_sha(self):
        return self.github(REPO, 'git/ref/heads/main')['object']['sha']

    @staticmethod
    def archive(repo, revision, destination):
        sha(revision)
        with request.urlopen('https://api.github.com/repos/' + repo + '/tarball/' + revision,
                             timeout=60) as response:
            data = response.read(MAX_ARCHIVE + 1)
        if len(data) > MAX_ARCHIVE:
            raise ValueError('Source download exceeds its limit')
        unpack(data, destination)

    def stage(self, revision):
        releases = self.root / 'releases'
        releases.mkdir(exist_ok=True)
        # A fresh directory avoids trusting leftovers from a failed preflight.
        release = Path(tempfile.mkdtemp(prefix=revision + '-', dir=releases)) / 'source'
        self.archive(REPO, revision, release)
        tree = self.github(REPO, 'git/trees/' + revision + '?recursive=1')
        pins = {x['path']: x['sha'] for x in tree['tree'] if x.get('mode') == '160000'}
        if set(pins) != set(DEPENDENCIES):
            raise ValueError('Dependency layout changed; update the deployment configuration first')
        for name, repo in DEPENDENCIES.items():
            target = release / name
            if target.exists():
                target.rmdir()  # git archives contain empty submodule directories
            self.archive(repo, pins[name], target)
        runtime = Path(self.config['python'])
        digest = hashlib.sha256((release / 'blupe/requirements.txt').read_bytes()).hexdigest()
        if digest != self.config['requirements_sha256']:
            # Dependency changes get their own cached virtual environment, never
            # a pip install into the still-running website's environment.
            env = self.root / 'venvs' / digest
            runtime = env / 'bin/python'
            if not (env / '.installed').is_file():
                env.parent.mkdir(exist_ok=True)
                subprocess.run(['/usr/bin/python3', '-m', 'venv', str(env)], check=True, timeout=120)
                subprocess.run([str(runtime), '-m', 'pip', 'install', '--disable-pip-version-check',
                    '--no-input', '-r', str(release / 'blupe/requirements.txt'),
                    *self.config['test_requirements']], check=True, timeout=600)
                (env / '.installed').write_text(digest)
        (release / '.venv').symlink_to(runtime.parent.parent, target_is_directory=True)
        required = ['test_control_contract.py', 'test_grounding_freshness.py', 'test_auto_deploy.py']
        if not all((release / 'blupe/tests' / name).is_file() for name in required):
            raise ValueError('Required command/deployment regression tests are missing')
        self.emit('testing', 'Running the complete offline release preflight', revision=revision)
        started = time.monotonic()
        result = subprocess.run(['bash', 'blupe/deploy/preflight.sh'], cwd=release,
            env={**os.environ, 'PYTHON': str(runtime)}, text=True,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=600)
        print(result.stdout, flush=True)
        receipt = dict(command='PYTHON=<release runtime> bash blupe/deploy/preflight.sh',
                       exit_code=result.returncode, elapsed_s=time.monotonic()-started,
                       output=result.stdout)
        manifest = {str(p.relative_to(release)): hashlib.sha256(p.read_bytes()).hexdigest()
                    for p in release.rglob('*') if p.is_file() and not p.is_symlink()
                    and not any(part in ('.venv', '__pycache__', '.pytest_cache')
                                for part in p.relative_to(release).parts)}
        atomic_json(release / 'RELEASE.json', dict(commit=revision, runtime_code_commit=revision,
                    frontend_code_commit=revision, dependency_pins=pins,
                    owned_sha256=manifest, preflight=receipt, deployed_by='automatic Robo-house deployment',
                    physical_acceptance='Not qualified by deployment; see integration checklist'))
        if result.returncode:
            raise RuntimeError('Offline release preflight failed; current website was left unchanged')
        return release

    def web(self, path, *, data=None):
        headers = {'Host': HOST, 'Cache-Control': 'no-cache'}
        if self.cookie:
            headers['Cookie'] = self.cookie
        if data is not None:
            headers.update(Origin='https://' + HOST, **{'Content-Type': 'application/json'})
        with request.urlopen(request.Request('http://127.0.0.1:8821' + path,
                             data=data, headers=headers), timeout=10) as response:
            if data is not None:
                cookies = http.cookies.SimpleCookie()
                cookies.load(response.headers.get('Set-Cookie', ''))
                self.cookie = '; '.join(k + '=' + v.value for k, v in cookies.items())
            return json.loads(response.read(2 * 1024 * 1024))

    def health(self):
        try:
            return self.web('/spotter/health')
        except error.HTTPError as exc:
            status = exc.code
            exc.close()
            if status != 404:
                raise
        # Bootstrap compatibility only: the original release has no new health
        # route. Caddy's file gate already blocks new /api/run requests.
        old = json.loads((self.current / 'RELEASE.json').read_text())
        if not old.get('bootstrap'):
            raise RuntimeError('Current website has no deployment health endpoint')
        if not self.cookie:
            self.web('/api/session', data=b'{}')
        status = self.web('/api/status')
        readiness = self.web('/spotter/readiness')
        queue = status.get('queue_snapshot')
        if queue is None:
            raise RuntimeError('Robot queue status unavailable; refusing to interrupt a run')
        return dict(ok=True, revision=old['commit'], ready=readiness.get('configured') is True,
                    active_runs=len(status.get('whats_running', [])) + self.queued(queue), launches=0)

    @staticmethod
    def queued(queue):
        if not isinstance(queue, dict):
            raise ValueError('Invalid queue status')
        # Unknown busy/queue shapes fail closed rather than silently clearing.
        if 'entries' in queue:
            if not isinstance(queue['entries'], list):
                raise ValueError('Invalid queue entries')
            return len(queue['entries']) + bool(queue.get('public_run'))
        if not any(k in queue for k in ('active', 'active_session', 'waiting', 'queue')):
            raise ValueError('Unknown queue shape')
        active = queue.get('active') or queue.get('active_session')
        waiting = queue.get('waiting', queue.get('queue', []))
        if not isinstance(waiting, list):
            raise ValueError('Invalid waiting queue')
        return bool(active) + len(waiting)

    def state(self, phase, message, **details):
        atomic_json(self.maintenance, self.emit(phase, message, **details))

    def wait_idle(self):
        until, settled = self.clock() + self.config.get('drain_timeout_s', 900), 0
        while self.clock() < until:
            state = self.health()  # Unknown status never becomes idle.
            idle = state.get('active_runs') == 0 and state.get('launches') == 0
            settled = settled + 1 if idle else 0
            self.emit('draining', 'Waiting for active runs and cleanup to finish',
                      active_runs=state.get('active_runs'), launches=state.get('launches'))
            if settled >= 2:
                return
            self.sleep(2)
        raise RuntimeError('Active runs did not finish within the deployment window; no restart performed')

    def restart(self):
        self.cookie = ''
        subprocess.run(['sudo', '-n', 'systemctl', 'restart', SERVICE], check=True, timeout=180)

    def public_health(self):
        req = request.Request('https://' + HOST + '/spotter/health',
                              headers={'Cache-Control': 'no-cache'})
        with request.urlopen(req, timeout=10) as response:
            return json.loads(response.read(1024 * 1024))

    def wait_ready(self, revision):
        until = self.clock() + self.config.get('health_timeout_s', 600)
        while self.clock() < until:
            try:
                state = self.health()
                if state.get('revision') == revision and state.get('ready') is True:
                    release = json.loads((self.current / 'RELEASE.json').read_text())
                    if release.get('bootstrap'):
                        return state
                    public = self.public_health()
                    if public.get('revision') == revision and public.get('ready') is True:
                        return state
            except (OSError, ValueError, RuntimeError):
                pass
            self.emit('warming', 'Waiting for the new website and Dream solver to become ready', revision=revision)
            self.sleep(5)
        raise RuntimeError('New website did not report its exact revision ready')

    def promote(self, release, revision):
        previous = self.current.resolve(strict=True)
        swapped, recovered = False, False
        try:
            self.state('draining', 'Spotter is updating. Active runs finish first; new runs are paused.', revision=revision)
            self.wait_idle()
            if self.main_sha() != revision:
                self.emit('superseded', 'A newer main commit will deploy instead', revision=revision)
                return
            self.state('restarting', 'Spotter is updating. Live cameras remain available; runs resume after preparation.', revision=revision)
            link(self.current, release)
            swapped = True
            self.restart()
            self.wait_ready(revision)
            link(self.good, release)
            recovered = True
            self.emit('ready', 'Spotter deployment is healthy', revision=revision)
        except BaseException:
            if swapped:
                self.state('rollback', 'Spotter update failed; restoring the previous release.', revision=revision)
                link(self.current, previous)
                self.restart()
                old_revision = json.loads((previous / 'RELEASE.json').read_text())['commit']
                self.wait_ready(old_revision)
                recovered = True
                self.emit('rolled_back', 'Previous website restored; deployment failed', revision=old_revision)
            raise
        finally:
            # If rollback itself failed, keep admission closed for recovery.
            if not swapped or recovered:
                self.maintenance.unlink(missing_ok=True)

    def deploy(self, revision):
        sha(revision)
        self.root.mkdir(exist_ok=True)
        with (self.root / 'deploy.lock').open('w') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            if revision != self.main_sha():
                self.emit('superseded', 'Only the current main commit may deploy', revision=revision)
                return
            if self.maintenance.exists():
                # Recover a process killed between swap and readiness. No run
                # could start while the persistent admission flag was present.
                good = self.good.resolve(strict=True)
                if self.current.resolve() != good:
                    self.state('rollback', 'Recovering an interrupted Spotter update.')
                    link(self.current, good)
                    self.restart()
                old_revision = json.loads((good / 'RELEASE.json').read_text())['commit']
                self.wait_ready(old_revision)
                self.maintenance.unlink()
            release = self.stage(revision)
            self.promote(release, revision)


def main():
    original = os.environ.get('SSH_ORIGINAL_COMMAND', '')
    matched = re.fullmatch(r'deploy ([0-9a-f]{40})', original)
    if not matched:
        raise SystemExit('This key permits only deploy <full-main-commit-sha>')
    config = json.loads(Path('/etc/blupe-spotter-deploy.json').read_text())
    for name in (signal.SIGTERM, signal.SIGHUP):
        signal.signal(name, lambda *_: sys.exit('Deployment interrupted'))
    try:
        Deployer(config).deploy(matched[1])
    except Exception as exc:
        print(json.dumps({'phase': 'failed', 'error': str(exc)[:500]}), flush=True)
        raise SystemExit(1) from None


if __name__ == '__main__':
    main()
