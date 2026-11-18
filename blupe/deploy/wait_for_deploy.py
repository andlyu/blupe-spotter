"""GitHub runner: verify the server's rollout over public HTTPS, without secrets."""
import json
import os
import sys
import time
from urllib import request, error

ORIGIN = 'https://robohouse.spotter.54.209.185.15.sslip.io'


def read(url):
    req = request.Request(url, headers={'Cache-Control': 'no-cache'})
    with request.urlopen(req, timeout=15) as response:
        return json.loads(response.read(1024 * 1024))


def wait(revision, *, fetch=read, clock=time.monotonic, sleep=time.sleep, timeout=2550):
    until, last, next_main_check = clock() + timeout, None, 0.
    while clock() < until:
        try:
            health = fetch(ORIGIN + '/spotter/health')
        except (OSError, ValueError):
            health = {}
        if health.get('revision') == revision and health.get('ready') is True:
            print('Spotter is ready at ' + revision, flush=True)
            return 0
        try:
            state = fetch(ORIGIN + '/spotter/deployment')
        except (OSError, ValueError):
            state = {'phase': 'waiting', 'message': 'Waiting for the server to detect this main commit'}
        key = (state.get('phase'), state.get('message'), state.get('revision'))
        if key != last:
            print(json.dumps(state), flush=True)
            last = key
        if state.get('revision') == revision and state.get('phase') in ('failed', 'interrupted'):
            return 1
        # Main may have advanced while this run waited in GitHub's queue.
        if clock() >= next_main_check:
            next_main_check = clock() + 60
            try:
                latest = fetch('https://api.github.com/repos/andlyu/blupe-spotter/git/ref/heads/main')['object']['sha']
                if latest != revision:
                    print('Superseded by a newer main commit: ' + latest, flush=True)
                    return 0
            except (OSError, ValueError, KeyError):
                pass
        sleep(15)
    print('Timed out waiting for this revision to become ready', flush=True)
    return 1


if __name__ == '__main__':
    raise SystemExit(wait(os.environ['DEPLOY_SHA']))
