"""Spotter handoff for the pinned Dream-1 adapter's causal action history."""
import math
from pathlib import Path
import time

from remote_yam.dream_policy import DreamAdapter, DreamWorker

CHECKPOINT = 'dreamlabs/dream-1-beta'
PREPARATION_TIMEOUT_S = 900


class PreparedDreamWorker(DreamWorker):
    """Station-only startup budget; the pinned solver itself is unchanged."""
    def __init__(self, python, credentials, directory):
        directory = Path(directory)
        directory.mkdir(mode=0o700, parents=True, exist_ok=True)
        # The upstream worker hardcodes a 120s wait for SDK background compile.
        # On the shared host that expires while JAX is still making progress.
        # Extend only this startup event wait in an in-memory, guarded overlay;
        # retain the pinned protocol, IK settings, kernels and release handling.
        launcher = directory / 'prepared-python'
        # Preserve the venv interpreter path; resolving its symlink would run
        # system Python without the pinned Dream SDK.
        launcher.write_text('#!' + str(Path(python).absolute()) + '\n' + '''import sys
from pathlib import Path
worker = Path(sys.argv[1])
source = worker.read_text()
needle = 'traj_ready.wait(120)'
if source.count(needle) != 1:
    raise RuntimeError('Pinned Dream preparation contract changed')
sys.path.insert(0, str(worker.parent))
exec(compile(source.replace(needle, 'traj_ready.wait(600)'), str(worker), 'exec'),
     {'__name__': '__main__', '__file__': str(worker)})
''')
        launcher.chmod(0o700)
        super().__init__(launcher, credentials, directory)

    def call(self, command, **kwargs):
        if command == 'prime':
            # This site exposes beta only. Do not compile an unused Flash client
            # or retain a second solver on the shared host.
            requested = kwargs.get('checkpoints', [])
            if CHECKPOINT not in requested or set(requested) - {CHECKPOINT, CHECKPOINT + '-flash'}:
                raise ValueError('Unknown station checkpoint preparation')
            kwargs['checkpoints'] = [CHECKPOINT]
        elif command == 'configure' and kwargs.get('checkpoint') != CHECKPOINT:
            raise ValueError('Unknown station checkpoint')
        return super().call(command, **kwargs)


class CapacityRefusal(RuntimeError):
    """The SDK explicitly refused inference before producing an action."""
    def __init__(self, reply):
        super().__init__('Dream capacity is busy')
        self.reply = reply


class CapacityWorker:
    def __init__(self, worker):
        self.worker = worker

    def __getattr__(self, name):
        return getattr(self.worker, name)

    def call(self, command, **kwargs):
        reply = self.worker.call(command, **kwargs)
        # Never retry transport faults, ambiguous actions or non-retryable
        # refusals. The SDK contract identifies these as unplaced requests.
        if (command == 'predict' and reply.get('ok') is False
                and reply.get('phase') == 'predict'
                and reply.get('error_type') == 'DreamServerError'
                and reply.get('code') == 'DA-2000' and reply.get('retryable') is True
                and reply.get('reason') in {'pool_full', 'queue_timeout', 'rate_limited'}):
            raise CapacityRefusal(reply)
        return reply


class CapacityWorkerFactory:
    def __init__(self, factory):
        self.factory = factory

    def __call__(self, *args, **kwargs):
        return CapacityWorker(self.factory(*args, **kwargs))


class SpotterDreamAdapter(DreamAdapter):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.worker_factory = CapacityWorkerFactory(self.worker_factory)

    def build_trajectory(self, prompt, observation, first_step_id):
        deadline, attempts = None, 0
        while True:
            try:
                # Re-enter the pinned adapter's fresh-input barrier on every
                # refusal, retaining lease, completed anchors and step IDs.
                return super().build_trajectory(prompt, observation, first_step_id)
            except CapacityRefusal as error:
                self._worker_timings(error.reply)
                if self._cancelled():
                    raise RuntimeError('Dream capacity wait cancelled') from None
                now = time.monotonic()
                if deadline is None:
                    deadline = now + 30.
                delay = error.reply.get('retry_after_s')
                delay = max(1., float(delay)) if type(delay) in (int, float) and math.isfinite(delay) else 5.
                reason = error.reply['reason']
                if attempts >= 3 or now + delay >= deadline:
                    message = ('Dream hosted model is busy (' + reason + '); '
                               'no action was sent for this request. Try again shortly.')
                    self._interaction('model_failure', message, code='DA-2000', reason=reason,
                                      retryable=True, capacity_retries=attempts)
                    raise RuntimeError(message) from None
                attempts += 1
                self._interaction('model_progress',
                    f'Dream capacity is busy ({reason}); retrying in {delay:g}s ({attempts}/3)',
                    progress_type='status', reason=reason, retry_after_s=delay,
                    capacity_retries=attempts)
                until = now + delay
                while True:
                    if self._cancelled():
                        raise RuntimeError('Dream capacity wait cancelled') from None
                    remaining = until - time.monotonic()
                    if remaining <= 0:
                        break
                    self._stop.wait(min(.1, remaining))

    def supervisor_intervention(self):
        # The upstream adapter resets between predictions before collecting new
        # inputs. Use that path to discard smoothing anchors and camera history
        # from before the repair, including any prediction Spotter superseded.
        with self._changed:
            self._commanded = self._pending_commanded = None
            self._workspace_reset_pending = True
            self._workspace_feedback = (
                'Spotter intervened and repaired the scene. The previous action '
                'plan was discarded. Continue from fresh measured state and images.')
