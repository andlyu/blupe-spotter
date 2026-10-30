from concurrent.futures import Future
import threading
import time
from types import SimpleNamespace

import numpy as np
import pytest

from spotter_yam.policy import SpotterAdapter, validate_plan
from spotter_yam.vlm import object_from_text
from remote_yam.providers import PolicyComplete


def observation(step=0, x=.25, episode='one'):
    return dict(jetson_id='yam-1', episode_id=episode, settled=True,
                observed_at=time.time(), step_id=step, x=x,
                left_joints_deg=[10.] * 6, right_joints_deg=[-10.] * 6,
                left_gripper=.2, right_gripper=.8)


class Geometry:
    low = np.array([-.5] * 14)
    high = np.array([1.] * 14)
    def __init__(self): self.targets = []
    def observe(self, obs):
        return None, np.array([obs['x'], 0, .2, 0, 0, 0, .2] + [.3, 0, .2, 0, 0, 0, .8]), None
    def build(self, targets, obs, step):
        self.targets.append((targets, obs.copy(), step))
        return [dict(step_id=step, left_joints_deg=obs['left_joints_deg'], right_joints_deg=obs['right_joints_deg'])]


class Base:
    model = 'test-dreamzero'
    def __init__(self): self.calls = []
    def build_trajectory(self, prompt, obs, step):
        self.calls.append(obs.copy())
        return [dict(step_id=step, left_joints_deg=obs['left_joints_deg'], right_joints_deg=obs['right_joints_deg'])]


class Supervisor:
    model = 'test-qwen'
    def __init__(self): self.calls = []; self.plans = []
    def screen(self, prompt, history):
        self.calls.append(('screen', history)); return {'flag': False, 'risk': 0, 'why': 'progress'}
    def judge(self, *args): raise AssertionError('Unflagged windows must not call the judge')
    def repair(self, prompt, history, context):
        self.plans.append((history, context))
        return dict(why='re-stage', expectation='hand shifts right', steps=[dict(op='nudge',arm='left',dxyz=[.03,0,0]),dict(op='policy')])
    def verify(self, *args): return dict(verdict='verified', why='object moved with the hand')


@pytest.fixture
def adapter():
    frames = [SimpleNamespace(name=name, jpeg=b'not-used-in-transport-test') for name in ('top','left','right')]
    cameras = SimpleNamespace(capture_for_policy=lambda *a, **k: frames)
    value = SpotterAdapter(Base(), Supervisor(), Geometry(), robot_id='yam-1', camera_source=cameras)
    yield value
    value.close_transport()


def finished(verdict):
    future=Future(); future.set_result(verdict); return future


def test_policy_leads_and_unflagged_screen_does_not_call_judge(adapter):
    adapter.build_trajectory('move the block', observation(), 0)
    assert not adapter.supervisor.calls
    adapter.trajectory_completed(observation(1),1)
    adapter.build_trajectory('move the block', observation(1),1)
    adapter._future[1].result(timeout=2)
    adapter.trajectory_completed(observation(2),1)
    adapter.build_trajectory('move the block', observation(2),2)
    assert len(adapter.base.calls)==3
    assert adapter.supervisor.calls[0][0]=='screen'


def test_repair_uses_current_pose_not_stale_flagged_pose(adapter):
    adapter._chunks=2
    adapter._future=(1,finished(dict(verdict='intervene',why='missed grasp at old pose')))
    points=adapter.build_trajectory('move the block',observation(16,x=.4),16)
    targets, measured, first = adapter.geometry.targets[0]
    assert targets == {'left_x':pytest.approx(.43),'left_y':0,'left_z':.2}
    assert measured['x']==.4 and first==16 and points[0]['step_id']==16
    assert not adapter.base.calls
    assert adapter.supervisor.plans[0][1]['replan_from_current_state'] is True


def test_slow_supervisor_holds_at_bound_and_stop_discards_late_result(adapter):
    adapter._chunks=2
    pending=Future(); adapter._future=(1,pending)
    outcome=[]
    def build():
        try:adapter.build_trajectory('move',observation(16),16)
        except Exception as exc:outcome.append(exc)
    thread=threading.Thread(target=build); thread.start()
    time.sleep(.08)
    assert thread.is_alive() and not adapter.base.calls
    adapter.cancelled=lambda:True
    thread.join(2)
    pending.set_result(dict(verdict='intervene',why='late result'))
    assert len(outcome)==1 and 'cancelled' in str(outcome[0])
    assert not adapter.geometry.targets and not adapter.base.calls


def test_failed_supervision_never_becomes_policy_pass(adapter):
    adapter._chunks=2
    future=Future();future.set_exception(RuntimeError('model unavailable'))
    adapter._future=(1,future)
    with pytest.raises(RuntimeError,match='unavailable'):
        adapter.build_trajectory('move',observation(16),16)
    assert not adapter.base.calls and not adapter.geometry.targets


def test_asynchronous_success_rechecked_against_current_scene(adapter):
    adapter._chunks=1
    adapter._future=(1,finished(dict(verdict='success',why='previous scene complete')))
    adapter.supervisor.judge=lambda *args:dict(verdict='pass',why='current scene still needs work')
    adapter.build_trajectory('move',observation(8),8)
    assert len(adapter.base.calls)==1


def test_verified_completion_is_model_reported_and_sends_no_next_packet(adapter):
    adapter._chunks=1
    adapter._future=(1,finished(dict(verdict='success',why='complete')))
    adapter.supervisor.judge=lambda *args:dict(verdict='success',why='current scene complete')
    with pytest.raises(PolicyComplete):adapter.build_trajectory('move',observation(8),8)
    assert not adapter.base.calls


def test_unmet_expectation_replans_from_fresh_feedback(adapter):
    adapter._repair_context=dict(expectation='object rises')
    adapter._verify=True
    adapter.supervisor.verify=lambda *args:dict(verdict='replan',why='object stayed on table')
    adapter.build_trajectory('move',observation(8,x=.35),8)
    assert adapter.supervisor.plans[0][1]['verification']['verdict']=='replan'
    assert adapter.geometry.targets[0][0]['left_x']==pytest.approx(.38)


def test_episode_switch_and_wrong_robot_rejected_before_policy(adapter):
    adapter.build_trajectory('move',observation(),0)
    with pytest.raises(ValueError,match='episodes'):
        adapter.build_trajectory('move',observation(8,episode='two'),8)
    with pytest.raises(ValueError,match='another robot'):
        adapter.build_trajectory('move',{**observation(),'jetson_id':'other'},8)
    assert len(adapter.base.calls)==1


@pytest.mark.parametrize('step',[
 {'op':'reset'}, {'op':'nudge','arm':'left','dxyz':[float('nan'),0,0]},
 {'op':'gripper','arm':'left','value':True}, {'op':'gripper','arm':'left','value':-1},
 {'op':'lift','dz':.02}, {'op':'lift','arm':'left','dz':.02,'url':'extra'},
])
def test_invalid_repair_rejected_before_execution(step):
    with pytest.raises(ValueError):validate_plan(dict(expectation='check',steps=[step]))


def test_model_json_accepts_fenced_object_and_rejects_nonobject():
    assert object_from_text('```json\n{"flag":false}\n```')=={'flag':False}
    with pytest.raises(ValueError):object_from_text('[]')
