"""Delayed session association and history visibility before video publication."""
from threading import Lock
from types import SimpleNamespace

import pytest

from playground import HostedRunner
from remote_yam.past_runs import RunNames
from spotter_yam.app import SpotterApp, ROBOHOUSE
from spotter_yam.history import ReceiptHistory


def receipt_app(tmp_path):
    app = SpotterApp.__new__(SpotterApp)
    app.run_names = RunNames(tmp_path/'names.sqlite3')
    app.robot_id = ROBOHOUSE
    app.remembered_names = set()
    return app


def test_async_launch_associates_only_its_accepted_attempt(tmp_path, monkeypatch):
    app = receipt_app(tmp_path)
    state = {'attempt_id':'accepted', 'session_id':None, 'episode_id':None}
    visitor = SimpleNamespace(lock=Lock(), controller=SimpleNamespace(status=lambda:dict(state)),
        runner_session_id=None, runner_name='Andrew', runner_task='put cube in cup', episode_ids=set())
    monkeypatch.setattr(HostedRunner, 'launch', lambda *a, **k: {'ok':True, 'attempt_id':'accepted'})
    app.launch(visitor, {})
    app.remember_runner(visitor)
    assert not app.run_names.path.exists()
    state.update(attempt_id='unrelated', session_id='other-session', episode_id='ep_other')
    app.remember_runner(visitor)
    assert visitor.runner_session_id is None and not visitor.episode_ids
    state.update(attempt_id='accepted', session_id='owned-session', episode_id='ep_owned',
                 status='stopped', run_started_at=100, run_configuration={'model':'spotter/dreamlabs/dream-1-beta'})
    app.remember_runner(visitor)
    assert visitor.runner_session_id == 'owned-session' and visitor.episode_ids == {'ep_owned'}
    assert app.run_names.names() == {'ep_owned':'Andrew'}
    assert app.run_names.pending('ep_owned', ROBOHOUSE)['prompt'] == 'put cube in cup'


class Archive:
    def __init__(self):
        self.rows = [{'episode_id':'ep_old','robot_id':ROBOHOUSE,'prompt':'old task',
                      'started_at':1,'model':'baseline'}]
    def page(self, **kwargs): return {'runs':list(self.rows), 'stale':False}
    def details_for(self, rows):
        assert all(r.get('video_status') != 'processing' for r in rows)
        return [dict(r,video_url='https://archive.example/'+r['episode_id']) for r in rows]


@pytest.fixture
def history(tmp_path):
    names = RunNames(tmp_path/'names.sqlite3')
    names.remember_metadata('ep_recent', ROBOHOUSE, 'orange cube into cup', 10,
                            {'model':'spotter/dreamlabs/dream-1-beta'})
    names.remember_metadata('ep_other', 'yam-1', 'private other station receipt', 20)
    return ReceiptHistory(Archive(), names, ROBOHOUSE)


def test_pending_receipt_visible_in_catalog_and_session_history_without_fake_video(history):
    rows = history.page()['runs']
    assert [r['episode_id'] for r in rows] == ['ep_recent','ep_old']
    recent = history.get('ep_recent')
    assert recent['video_status'] == 'processing' and recent['video_url'] is None
    assert recent['original_available'] is False
    assert history.page(episode_ids={'ep_recent'})['runs'] == [recent]
    assert history.page(query='orange cube')['runs'][0]['episode_id'] == 'ep_recent'
    assert history.page(model='baseline')['runs'][0]['episode_id'] == 'ep_old'
    assert history.page(robot_id='yam-1')['runs'] == []


def test_published_archive_replaces_pending_receipt_without_duplicates(history):
    history.archive.rows.append({'episode_id':'ep_recent','robot_id':ROBOHOUSE,
        'prompt':'orange cube into cup','started_at':10,'model':'spotter/dreamlabs/dream-1-beta'})
    rows = history.page()['runs']
    assert len(rows) == 2
    assert rows[0]['video_url'] == 'https://archive.example/ep_recent'
    assert 'video_status' not in rows[0]


def test_receipt_remains_visible_when_archive_is_unavailable(history, monkeypatch):
    def unavailable(**kwargs): raise OSError('archive offline')
    monkeypatch.setattr(history.archive, 'page', unavailable)
    result = history.page()
    assert result['stale'] and result['runs'][0]['episode_id'] == 'ep_recent'
