"""Local replay playback remains available when the public archive is delayed."""
import asyncio
import hashlib
import json
from pathlib import Path

import pytest

from remote_yam.quick_replays import QuickReplays
from spotter_yam.app import SpotterApp, ROBOHOUSE
from spotter_yam.recover_replays import snapshot
from test_history import history


def local_clip(root, eid='ep_recent', robot=ROBOHOUSE):
    body = b'original-encoded-video-for-range-test'
    digest = hashlib.sha256(body).hexdigest()
    (root / eid).mkdir()
    (root / eid / (digest + '.mp4')).write_bytes(body)
    (root / (eid + '.json')).write_text(json.dumps(dict(
        episode_id=eid, robot_id=robot, task='orange cube into cup',
        started_at=10, ended_at=20, outcome='user_requested',
        bytes=len(body), locally_ready_at=21, original_available=False,
        preview=dict(sha256=digest, duration_s=5, speed=2,
                     camera_order=['left', 'top', 'right']))))
    return body, digest


def test_local_footage_bypasses_archive_and_preserves_recorded_model(history, tmp_path):
    local_clip(tmp_path)
    history.replays = QuickReplays(tmp_path)
    row = history.get('ep_recent')
    assert row['video_status'] == 'ready'
    assert row['video_url'].startswith('/api/quick-replays/ep_recent/')
    assert row['model'] == 'spotter/dreamlabs/dream-1-beta'
    assert row['original_available'] is False
    calls = []
    def offline(**kwargs):
        calls.append(True)
        raise OSError('offline')
    history.archive.page = offline
    assert history.get('ep_recent')['video_url'] == row['video_url']
    assert not calls


def test_station_mismatch_does_not_expose_local_footage(history, tmp_path):
    local_clip(tmp_path, robot='yam-1')
    history.replays = QuickReplays(tmp_path)
    assert history.get('ep_recent')['video_url'] is None


def response(app, path, headers=None):
    messages = []
    async def send(message): messages.append(message)
    asyncio.run(app.public_extension({'method':'GET', 'path':path}, None, send, headers or {}))
    return messages[0], messages[1]['body']


def test_video_route_serves_ranges_and_allows_self_media_only(tmp_path):
    body, digest = local_clip(tmp_path)
    app = SpotterApp.__new__(SpotterApp)
    app.secure = True
    app.robot_id = ROBOHOUSE
    app.local_replays = QuickReplays(tmp_path)
    path = f'/api/quick-replays/ep_recent/{digest}.mp4'
    start, result = response(app, path, {'range':'bytes=3-9'})
    headers = dict(start['headers'])
    assert start['status'] == 206 and result == body[3:10]
    assert headers[b'content-range'] == f'bytes 3-9/{len(body)}'.encode()
    assert b"media-src 'self' https://huggingface.co" in headers[b'content-security-policy']
    assert b"default-src 'none'" in headers[b'content-security-policy']
    start, _ = response(app, path, {'range':'bytes=999-'})
    assert start['status'] == 416
    (tmp_path/'ep_recent'/(digest+'.mp4')).write_bytes(b'tampered')
    assert response(app, path)[0]['status'] == 404


def recording(root):
    (root/'images').mkdir(parents=True)
    row = {'timestamp':0.1}
    for name in ('left', 'top', 'right'):
        row[name+'_image_path'] = 'images/'+name+'.jpg'
        (root/'images'/(name+'.jpg')).write_bytes(b'\xff\xd8saved\xff\xd9')
    raw = json.dumps(row).encode()+b'\n'
    (root/'samples.jsonl').write_bytes(raw)
    meta = dict(episode_id='ep_source', robot_id=ROBOHOUSE, status='finalized',
                simulated=False, rows=1, samples_sha256=hashlib.sha256(raw).hexdigest())
    (root/'manifest.json').write_text(json.dumps(meta))
    return meta


def test_snapshot_uses_only_hash_verified_original_episode(tmp_path):
    source, target = tmp_path/'source', tmp_path/'copy'
    meta = recording(source)
    assert snapshot(source, target, 'ep_source', ROBOHOUSE) == meta
    assert (target/'samples.jsonl').read_bytes() == (source/'samples.jsonl').read_bytes()
    with pytest.raises(ValueError, match='identity'):
        snapshot(source, tmp_path/'wrong-station', 'ep_source', 'yam-1')
    (source/'samples.jsonl').write_bytes(b'changed')
    with pytest.raises(ValueError, match='hash'):
        snapshot(source, tmp_path/'changed', 'ep_source', ROBOHOUSE)


def test_incomplete_staged_images_cannot_be_published(tmp_path):
    source = tmp_path/'source'
    recording(source)
    (source/'images'/'top.jpg').write_bytes(b'\xff\xd8unfinished')
    with pytest.raises(ValueError, match='Incomplete JPEG'):
        snapshot(source, tmp_path/'copy', 'ep_source', ROBOHOUSE)


def test_optional_observer_gap_preserves_native_hash_and_labels_derived_input(tmp_path):
    source, target = tmp_path/'source', tmp_path/'copy'
    meta = recording(source)
    row = json.loads((source/'samples.jsonl').read_text())
    row['observer_image_path'] = 'images/observer-not-copied.jpg'
    raw = (json.dumps(row)+'\n').encode()
    meta['samples_sha256'] = hashlib.sha256(raw).hexdigest()
    (source/'samples.jsonl').write_bytes(raw)
    (source/'manifest.json').write_text(json.dumps(meta))
    snapshot(source, target, 'ep_source', ROBOHOUSE)
    assert (target/'samples.jsonl').read_bytes() == raw
    derived = json.loads((target/'render'/'manifest.json').read_text())
    assert derived['source_samples_sha256'] == meta['samples_sha256']
    assert derived['missing_observer_images'] == 1
    assert 'observer_image_path' not in json.loads((target/'render'/'samples.jsonl').read_text())
