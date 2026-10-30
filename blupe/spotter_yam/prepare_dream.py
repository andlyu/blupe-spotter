"""Prepare the pinned Dream SDK's local solver without a robot/model prediction."""
import argparse
import json
import os
from pathlib import Path
import tempfile
import time

from remote_yam.dream_policy import DreamWorker


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work-dir', type=Path)
    parser.add_argument('--timeout', type=int, default=360)
    args = parser.parse_args()
    if not os.environ.get('JAX_COMPILATION_CACHE_DIR'):
        parser.error('Set a private, service-owned JAX_COMPILATION_CACHE_DIR first')
    python = os.environ.get('SPOTTER_DREAM_PYTHON', '')
    credentials = os.environ.get('SPOTTER_DREAM_CREDENTIALS_FILE', '')
    if not python or not credentials or not Path(python).is_file() or not Path(credentials).is_file():
        parser.error('Configure the Dream SDK interpreter and credential file')
    if not 1 <= args.timeout <= 600:
        parser.error('Timeout must be between 1 and 600 seconds')
    with tempfile.TemporaryDirectory(prefix='spotter-dream-prepare-') as temporary:
        worker = DreamWorker(python, credentials, args.work_dir or temporary)
        started = time.perf_counter()
        try:
            # This protocol operation uses synthetic rest poses, discards every
            # result, and does not call set_observation/get_action or lease a robot.
            reply = worker.call('prime', checkpoints=['dreamlabs/dream-1-beta'], timeout=args.timeout)
            ready = reply.get('ok') is True and (reply.get('result') or {}).get('fully_ready') is True
            print(json.dumps({'duration_s': round(time.perf_counter() - started, 3),
                              'ok': ready, 'result': reply.get('result'),
                              'error_type': reply.get('error_type'),
                              'stage_timings': reply.get('stage_timings')}), flush=True)
            return 0 if ready else 1
        finally:
            worker.close()


if __name__ == '__main__':
    raise SystemExit(main())
