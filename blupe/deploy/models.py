"""Serverless inference configuration; no GPU minimum or new persistent volume.

Run from a trusted operator machine. This is not exposed through the web app.
"""
import argparse
import json
from pathlib import Path
from urllib import request, error

NAME = 'blupe-spotter-qwen-20261030'
IMAGE = 'vllm/vllm-openai@sha256:befccf0e7e4089aa23926bb6f887a85c0d46c2a99e6de5c5ffdf5cb7957c5b34'
MODEL = 'Qwen/Qwen3.8-27B-FP8'
REVISION = '017b9c7af6b5689d5dd426a76e0bc077eb5ca20a'
DREAMZERO = 'kwtqqchzvju2uh'


def api(path, body=None, method=None):
    key = (Path.home() / '.config/runpod/api-key').read_text().strip()
    req = request.Request('https://api.runpod.io/v2/' + path,
        data=None if body is None else json.dumps(body).encode(),
        headers={'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json'}, method=method)
    try:
        with request.urlopen(req, timeout=45) as response:
            data = response.read()
            return json.loads(data) if data else {}
    except error.HTTPError as exc:
        raise RuntimeError('RunPod request failed: HTTP ' + str(exc.code)) from None


def config():
    return {'name': NAME, 'type': 'LOAD_BALANCER', 'image': IMAGE,
        'entrypoint': ['python', '-m', 'vllm.entrypoints.openai.api_server'],
        'cmd': ['--model', MODEL, '--revision', REVISION, '--served-model-name', 'qwen38',
                '--host', '0.0.0.0', '--port', '80', '--max-model-len', '32768',
                '--max-num-seqs', '1', '--gpu-memory-utilization', '0.9',
                '--limit-mm-per-prompt', '{"image":30}'],
        'disk': 100, 'ports': [],
        'env': {'PORT': '80', 'PORT_HEALTH': '80', 'HEALTH_CHECK_PATH': '/health',
                'HF_HUB_DISABLE_PROGRESS_BARS': '1', 'TOKENIZERS_PARALLELISM': 'false'},
        'gpu': {'pools': ['ADA_48_PRO'], 'count': 1, 'minCudaVersion': '12.9'},
        'workers': {'min': 0, 'max': 1, 'idleTimeout': 300},
        'scaling': {'type': 'REQUEST_COUNT', 'requestCount': 1},
        'timeout': 300000, 'flashboot': 'FLASHBOOT'}


def summary(endpoint):
    return {key: endpoint.get(key) for key in ('id', 'name', 'image', 'gpu', 'workers')}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['plan', 'provision-qwen', 'enable-dreamzero', 'status'])
    parser.add_argument('--state', required=True)
    args = parser.parse_args()
    state_path = Path(args.state)
    state = json.loads(state_path.read_text()) if state_path.exists() else {}
    if args.action == 'plan':
        print(json.dumps(config(), indent=2)); return
    if args.action == 'provision-qwen':
        # Reconcile by exact unique name before creating, including retries.
        page, matches = None, []
        while True:
            listing = api('serverless' + ('?cursor=' + page if page else ''))
            matches += [e for e in listing.get('endpoints', []) if e.get('name') == NAME]
            page = listing.get('pagination', {}).get('nextCursor')
            if not page: break
        if len(matches) > 1: raise RuntimeError('Multiple matching Qwen endpoints need reconciliation')
        endpoint = matches[0] if matches else api('serverless', config())
        if endpoint.get('image') != IMAGE: raise RuntimeError('Existing Qwen endpoint image differs')
        state['qwen'] = endpoint['id']
        state_path.parent.mkdir(parents=True, exist_ok=True)
        state_path.write_text(json.dumps(state, indent=2) + '\n')
        print(json.dumps(summary(endpoint))); return
    if args.action == 'enable-dreamzero':
        endpoint = api('serverless/' + DREAMZERO)
        if (endpoint.get('name') != 'dreamzero-yam-trial-01a1848c'
                or endpoint.get('networkVolumes') != ['w8bhyy9lve']):
            raise RuntimeError('DreamZero identity differs from the reviewed configuration')
        endpoint = api('serverless/' + DREAMZERO,
            {'workers': {'min': 0, 'max': 1, 'idleTimeout': 300}}, 'PATCH')
        state['dreamzero'] = DREAMZERO
        state_path.parent.mkdir(parents=True, exist_ok=True)
        state_path.write_text(json.dumps(state, indent=2) + '\n')
        print(json.dumps(summary(endpoint))); return
    for kind, identity in state.items():
        print(kind, json.dumps(summary(api('serverless/' + identity))))


if __name__ == '__main__': main()
