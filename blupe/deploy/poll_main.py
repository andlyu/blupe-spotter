#!/usr/bin/env python3
"""Server-side pull deployment; uses public HTTPS and no GitHub credentials."""
import json
from pathlib import Path
import signal
import sys
try:
    from .auto_deploy import atomic_json
except ImportError:
    from auto_deploy import atomic_json


def poll(deployer, *, retry=False):
    revision = deployer.main_sha()
    current = json.loads((deployer.current / 'RELEASE.json').read_text())
    if current.get('commit') == revision and not deployer.maintenance.exists():
        try:
            state = deployer.health()
        except (OSError, ValueError, RuntimeError):
            state = {}
        if state.get('ready') is True and state.get('revision') == revision:
            return 'current'
    receipt = deployer.root / 'attempt.json'
    if receipt.exists() and not retry:
        previous = json.loads(receipt.read_text())
        if previous.get('revision') == revision and previous.get('failed') is True:
            return 'failed; waiting for a new main commit or an operator retry'
    # Written before entering the release: interrupted attempts retry on the
    # next tick; explicit failures wait for corrected source/operator action.
    atomic_json(receipt, {'revision': revision, 'failed': False})
    try:
        deployer.deploy(revision)
    except BaseException as exc:
        failed = not isinstance(exc, (KeyboardInterrupt, SystemExit))
        atomic_json(receipt, {'revision': revision, 'failed': failed})
        deployer.emit('failed' if failed else 'interrupted',
                      str(exc)[:500], revision=revision)
        raise
    atomic_json(receipt, {'revision': revision, 'failed': False})
    return 'deployed'


def main():
    # The operator installs these two reviewed files outside app releases.
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from auto_deploy import Deployer
    if sys.argv[1:] not in ([], ['--retry']):
        raise SystemExit('Usage: poll_main.py [--retry]')
    for sig in (signal.SIGTERM, signal.SIGHUP):
        signal.signal(sig, lambda *_: sys.exit('Deployment interrupted'))
    config = json.loads(Path('/etc/blupe-spotter-deploy.json').read_text())
    print(poll(Deployer(config), retry='--retry' in sys.argv), flush=True)


if __name__ == '__main__':
    main()
