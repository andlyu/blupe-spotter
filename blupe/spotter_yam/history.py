"""Keep public run receipts visible while the external video archive catches up."""
import sqlite3

from remote_yam.run_search import rank_runs


class ReceiptHistory:
    source = 'public archive and local run receipts'

    def __init__(self, archive, names, robot_id, replays=None):
        self.archive, self.names, self.robot_id = archive, names, robot_id
        self.replays = replays

    def pending(self, published):
        if not self.names.path.exists():
            return []
        with sqlite3.connect(self.names.path) as db:
            if not db.execute("SELECT name FROM sqlite_master WHERE name='run_metadata'").fetchone():
                return []
            ids = [r[0] for r in db.execute(
                'SELECT episode_id FROM run_metadata WHERE robot_id=? ORDER BY started_at DESC LIMIT 100',
                (self.robot_id,)) if r[0] not in published]
        return [dict(row, original_available=False) for eid in ids
                if (row := self.names.pending(eid, self.robot_id))]

    def page(self, offset=0, *, episode_id=None, episode_ids=None, robot_id=None,
             model='', query='', metadata=False, models=None):
        try:
            catalog = self.archive.page(metadata=True)
        except Exception:
            if not self.pending(set()):
                raise
            catalog = {'runs': [], 'stale': True}
        rows = catalog['runs'] + self.pending({r['episode_id'] for r in catalog['runs']})
        rows = [dict(r) for r in rows if (episode_ids is None or r['episode_id'] in episode_ids)
                and (robot_id is None or r['robot_id'] == robot_id)]
        choices = sorted({r.get('model') or '__unrecorded__' for r in rows}, key=str.casefold)
        rows = [r for r in rows if (not model or (r.get('model') or '__unrecorded__') == model)
                and (not models or (r.get('model') or '__unrecorded__') in models)]
        rows.sort(key=lambda r: r.get('started_at') or 0, reverse=True)
        if query.strip() and episode_id is None:
            rows = rank_runs(rows, query)
        if episode_id is not None:
            rows = [r for r in rows if r['episode_id'] == episode_id]
        selected = rows if metadata else rows[offset:offset+12]
        return {'runs': selected if metadata else self.details_for(selected),
                'total': len(rows), 'models': choices, 'stale': catalog.get('stale', False),
                'next_offset': offset+len(selected) if not metadata and offset+len(selected)<len(rows) else None}

    def details_for(self, rows):
        local = {r['episode_id']: clip for r in rows if self.replays
                 and (clip := self.replays.get(r['episode_id'], self.robot_id))}
        published = [r for r in rows if r['episode_id'] not in local
                     and r.get('video_status') != 'processing']
        details = {r['episode_id']:r for r in self.archive.details_for(published)} if published else {}
        return [dict(r, **{k:v for k,v in local[r['episode_id']].items() if v is not None},
                     video_status='ready') if r['episode_id'] in local
                else details.get(r['episode_id'], dict(r)) for r in rows]

    def get(self, episode_id):
        if self.replays and (clip := self.replays.get(episode_id, self.robot_id)):
            row = self.names.pending(episode_id, self.robot_id) or {}
            return dict(row, **{k:v for k,v in clip.items() if v is not None}, video_status='ready')
        rows = self.page(episode_id=episode_id)['runs']
        return rows[0] if rows else None
