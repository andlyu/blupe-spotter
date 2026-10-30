"""Recover finalized Spotter footage already on the web host; no robot access.

Run with the publisher's Python environment. It provides the pinned renderer
and immutable cache installer, but no publisher, uploader or controller is run.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import sqlite3
import sys
import tempfile
import time


def snapshot(source, destination, eid, robot_id):
    meta = json.loads((source / 'manifest.json').read_text())
    raw = (source / 'samples.jsonl').read_bytes()
    if (meta.get('episode_id') != eid or meta.get('robot_id') != robot_id
            or meta.get('status') != 'finalized' or meta.get('simulated') is not False
            or hashlib.sha256(raw).hexdigest() != meta.get('samples_sha256')):
        raise ValueError('Recording identity or finalized sample hash mismatch')
    rows = [json.loads(line) for line in raw.splitlines()]
    if not rows or len(rows) != meta.get('rows'):
        raise ValueError('Incomplete recording samples')
    images = source / 'images'
    paths = set()
    missing_observer = 0
    for row in rows:
        cameras = ('left', 'top', 'right') + (('observer',) if row.get('observer_image_path') else ())
        for camera in cameras:
            value = row.get(camera + '_image_path')
            if not isinstance(value, str):
                raise ValueError('Incomplete three-camera recording')
            path = (source / value).resolve()
            if path.parent != images.resolve() or path.is_symlink():
                raise ValueError('Image path escapes recording')
            if camera == 'observer' and not path.is_file():
                # The optional observer can be incomplete after a failed copy.
                # Remove only unavailable references in a derived render input;
                # the renderer explicitly labels camera gaps. Keep native raw
                # samples untouched as the source-of-truth hash for installation.
                row.pop('observer_image_path')
                missing_observer += 1
                continue
            paths.add(path)
    (destination / 'images').mkdir(parents=True)
    for path in paths:
        image = path.read_bytes()
        if not image.startswith(b'\xff\xd8') or not image.endswith(b'\xff\xd9'):
            raise ValueError('Incomplete JPEG; wait for staging to finish')
        (destination / 'images' / path.name).write_bytes(image)
    (destination / 'samples.jsonl').write_bytes(raw)
    (destination / 'manifest.json').write_text(json.dumps(meta))
    if missing_observer:
        render = destination / 'render'
        render.mkdir()
        (render / 'images').symlink_to('../images', target_is_directory=True)
        derived = ''.join(json.dumps(row)+'\n' for row in rows).encode()
        (render / 'samples.jsonl').write_bytes(derived)
        (render / 'manifest.json').write_text(json.dumps(dict(meta,
            samples_sha256=hashlib.sha256(derived).hexdigest(),
            source_samples_sha256=meta['samples_sha256'],
            missing_observer_images=missing_observer)))
    return meta


def recover(database, source_root, cache, work, robot_id, publisher):
    # Shared publisher code is used only for offline rendering and installation.
    sys.path[:0] = [str(publisher), str(publisher / 'scripts')]
    from YAM_control.training_video import render_video
    from local_replay_store import install_preview
    cache.mkdir(parents=True, exist_ok=True, mode=0o700)
    work.mkdir(parents=True, exist_ok=True, mode=0o700)
    if not database.is_file():
        return []
    with sqlite3.connect(database.resolve().as_uri() + '?mode=ro', uri=True) as db:
        ids = [r[0] for r in db.execute(
            'SELECT episode_id FROM run_metadata WHERE robot_id=? ORDER BY started_at DESC LIMIT 100',
            (robot_id,))]
    results = []
    for eid in ids:
        if not re.fullmatch(r'ep_[A-Za-z0-9_-]{1,100}', eid or ''):
            continue
        if (cache / (eid + '.json')).is_file():
            continue
        source = source_root / eid
        if not (source / 'manifest.json').is_file() or source.resolve().parent != source_root.resolve():
            continue
        started = time.monotonic()
        try:
            with tempfile.TemporaryDirectory(prefix=eid + '-', dir=work) as directory:
                episode = Path(directory)
                meta = snapshot(source, episode, eid, robot_id)
                video = episode / 'viewing.mp4'
                render_input = episode / 'render' if (episode / 'render').is_dir() else episode
                info = render_video(render_input, video, preview=True)
                if render_input != episode:
                    derived = json.loads((render_input / 'manifest.json').read_text())
                    info.update(render_samples_sha256=derived['samples_sha256'],
                                missing_observer_images=derived['missing_observer_images'])
                if not 0 < video.stat().st_size <= 16 * 1024 * 1024:
                    raise ValueError('Replay exceeds serving limit')
                info.update(samples_sha256=meta['samples_sha256'],
                            sha256=hashlib.sha256(video.read_bytes()).hexdigest())
                (episode / 'viewing.json').write_text(json.dumps(info))
                entry = install_preview(cache, episode)
                result = dict(episode_id=eid, status='ready', elapsed_s=time.monotonic()-started,
                              video_sha256=info['sha256'], bytes=entry['bytes'], preview=info)
                print(json.dumps(result), flush=True)
                results.append(result)
        except (OSError, ValueError, KeyError, RuntimeError) as error:
            # Incomplete copies are retried on the next timer tick; never publish
            # a partial video or invent a recording for a different episode.
            print(json.dumps(dict(episode_id=eid, status='pending', reason=str(error))), flush=True)
    return results


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('database', 'source-root', 'cache', 'work', 'publisher'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--robot-id', required=True)
    recover(**vars(parser.parse_args()))
