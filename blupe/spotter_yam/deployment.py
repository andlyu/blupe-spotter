"""Public deployment metadata and admission draining; never robot control."""
from contextlib import contextmanager
import json
from pathlib import Path
from threading import RLock


class DeploymentPaused(RuntimeError):
    pass


class DeploymentState:
    def __init__(self, path, revision, active_runs):
        self.path = Path(path) if path else None
        self.revision, self.active_runs = revision, active_runs
        self.lock, self.launches = RLock(), 0

    def status(self):
        if self.path is None:
            return {'paused': False}
        try:
            value = json.loads(self.path.read_text())
            if not isinstance(value, dict):
                raise ValueError('Invalid deployment state')
            return {'paused': True, 'phase': str(value.get('phase', 'updating'))[:50],
                    'message': str(value.get('message', 'Spotter is updating. Active runs finish first.'))[:300]}
        except FileNotFoundError:
            return {'paused': False}
        except (OSError, ValueError):
            return {'paused': True, 'phase': 'unavailable',
                    'message': 'Spotter update status is unavailable. New runs are temporarily paused.'}

    @contextmanager
    def admission(self):
        with self.lock:
            if self.status()['paused']:
                raise DeploymentPaused('Spotter is updating. Active runs finish first; try again shortly.')
            self.launches += 1
        try:
            yield
        finally:
            with self.lock:
                self.launches -= 1

    def health(self, ready):
        with self.lock:
            launches = self.launches
        return {'ok': True, 'revision': self.revision, 'ready': bool(ready),
                'active_runs': self.active_runs(), 'launches': launches,
                'deployment': self.status()}
