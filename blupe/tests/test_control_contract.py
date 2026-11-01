"""No network: real parser -> generator -> canonical validator -> JSON wire bytes."""
import io
import json
import time
from types import SimpleNamespace

import numpy as np
import pytest

from remote_yam.controller_workspace import workspace_for_robot
from remote_yam.robocurve_trajectory import RoboCurveTrajectory
from remote_yam.session import HttpSessionAPI, _trajectory_waypoints
from spotter_yam.policy import SpotterAdapter, validate_plan
from spotter_yam.repair_motion import RepairTrajectory
from spotter_yam.grounding import RepairGrounding

RID = 'robot-ba8413962083809c'


def measured():
    return dict(jetson_id=RID, episode_id='offline', observed_at=time.time(), settled=True, homed=True,
        source='hardware', mode='API_ACTIVE', safety={'ok': True, 'estop_engaged': False},
        left_joints_deg=[-1.21306, 45.58265, 35.37546, -21.47444, -.66664, -.46992],
        right_joints_deg=[-1.21306, 45.47336, 35.52845, -21.60558, -1.14749, -1.16935],
        left_gripper=.9992793312193716, right_gripper=.438)


def geometry(cls=RepairTrajectory):
    workspace = workspace_for_robot(RID)
    value = cls(**workspace.rgb_geometry_kwargs()); workspace.configure_geometry(value)
    return value


@pytest.fixture
def bridge(monkeypatch):
    wire = []
    def transport(req, **kwargs):
        wire.append(json.loads(req.data))
        return io.BytesIO(b'{"accepted":true}')
    monkeypatch.setattr('remote_yam.session.request.urlopen', transport)
    api = HttpSessionAPI('https://offline.invalid', supports_trajectories=True, robot_id=RID)
    api._session_capabilities['offline'] = 'test-only-capability'
    def send(points):
        api.submit_trajectory('offline', 'offline-episode', 'offline-lease', 'offline-trajectory', 10, points)
        return wire[-1]['waypoints']
    return send, wire


@pytest.mark.parametrize('arm', ['left', 'right'])
@pytest.mark.parametrize('target', [0., 1., .37, 1e-12, 1-1e-12])
def test_fractional_gripper_start_endpoint_and_exact_holds_through_serialized_packet(bridge, arm, target):
    send, wire = bridge; obs = measured(); obs[arm+'_gripper'] = .9992793312193716
    gen = geometry(); adapter = SpotterAdapter(SimpleNamespace(model='offline'), SimpleNamespace(model='offline'), gen,
                                              robot_id=RID, camera_source=None)
    try:
        step = validate_plan({'expectation': 'gripper moves', 'steps': [{'op': 'gripper', 'arm': arm, 'value': target}]})[0]
        points = send(adapter._primitive(step, obs, 11))
        assert len(wire) == 1 and points[-1][arm+'_gripper'] == target
        assert [x['step_id'] for x in points] == list(range(11, 11+len(points)))
        other = 'right' if arm == 'left' else 'left'
        for point in points:
            assert point['left_joints_deg'] == obs['left_joints_deg']
            assert point['right_joints_deg'] == obs['right_joints_deg']
            assert point[other+'_gripper'] == obs[other+'_gripper']
            assert 0 <= point[arm+'_gripper'] <= 1
        values = [obs[arm+'_gripper']] + [x[arm+'_gripper'] for x in points]
        assert max(abs(b-a) for a,b in zip(values, values[1:])) <= .1
    finally: adapter.close_transport()


@pytest.mark.parametrize('arm', ['left', 'right'])
@pytest.mark.parametrize('op', ['nudge', 'lift', 'move_to', 'rotate'])
def test_cartesian_primitives_preserve_unrequested_arm_grippers_and_pacing(bridge, arm, op):
    send, _ = bridge; obs = measured(); gen = geometry(); _, values, _ = gen.observe(obs)
    names = [arm+'_'+axis for axis in ('x','y','z')]
    from remote_yam.robocurve_trajectory import NAMES
    current = dict(zip(NAMES, map(float, values)))
    step = dict(op=op, arm=arm)
    if op == 'nudge': step['dxyz'] = [0, 0, .04]
    elif op == 'lift': step.update(dz=.04, intent='clearance')
    elif op == 'move_to': step['xyz'] = [current[n]+(.035 if n.endswith('_x') else 0) for n in names]
    else: step['yaw'] = .6
    adapter = SpotterAdapter(SimpleNamespace(model='offline'), SimpleNamespace(model='offline'), gen, robot_id=RID, camera_source=None)
    try:
        step = validate_plan({'expectation': 'small measured move', 'steps': [step]})[0]
        points = send(adapter._primitive(step, obs, 0)); other = 'right' if arm == 'left' else 'left'
        previous = obs
        for point in points:
            assert point[other+'_joints_deg'] == obs[other+'_joints_deg']
            assert point['left_gripper'] == obs['left_gripper'] and point['right_gripper'] == obs['right_gripper']
            assert max(abs(a-b) for a,b in zip(point[arm+'_joints_deg'],previous[arm+'_joints_deg'])) <= np.degrees(.035)+1e-9
            previous = point
        from remote_yam.mujoco_ik import POSITION_TOLERANCE_M, ORIENTATION_TOLERANCE_RAD
        final = dict(zip(NAMES, map(float, gen.observe({**obs, **points[-1], 'settled':True})[1])))
        expected = np.array([current[n] for n in names])
        if op == 'move_to': expected = np.array(step['xyz'])
        elif op in ('nudge', 'lift'): expected += [0,0,.04]
        assert np.linalg.norm(np.array([final[n] for n in names])-expected) <= POSITION_TOLERANCE_M
        if op == 'rotate': assert abs(final[arm+'_yaw']-step['yaw']) <= ORIENTATION_TOLERANCE_RAD
    finally: adapter.close_transport()


@pytest.mark.parametrize('value', [-1e-16, 1+1e-15, -1, 2, float('nan'), float('inf'), True, '0'])
def test_invalid_gripper_requests_never_reach_transport(bridge, value):
    send, wire = bridge
    with pytest.raises(ValueError):
        step = validate_plan({'expectation': 'invalid', 'steps': [{'op': 'gripper', 'arm': 'left', 'value': value}]})[0]
        send(geometry().build({'left_gripper': step['value']}, measured(), 0))
    assert wire == []


def test_strict_validator_rejects_documented_negative_roundoff_packet_without_dispatch(bridge):
    send, wire = bridge; obs = measured(); packet = [{**{k:obs[k] for k in ('left_joints_deg','right_joints_deg','left_gripper','right_gripper')}, 'step_id':0}]
    packet[0]['left_gripper'] = -1.1102230246251565e-16
    with pytest.raises(ValueError, match='between 0 and 1'): send(packet)
    assert wire == []


def test_unsettled_feedback_and_bad_step_budget_never_dispatch(bridge):
    send, wire = bridge; obs = measured(); obs['settled'] = False
    with pytest.raises(RuntimeError, match='settled'): send(geometry().build({'left_gripper':0}, obs, 0))
    obs['settled'] = True
    with pytest.raises(ValueError, match='budget'): send(geometry().build({'left_gripper':0}, obs, 2999))
    assert wire == []


@pytest.mark.parametrize('arm', ['left', 'right'])
def test_measured_point_reference_runs_through_resolver_generator_and_wire(bridge, arm):
    send, _ = bridge; obs = measured(); gen = geometry()
    from remote_yam.robocurve_trajectory import NAMES
    current = dict(zip(NAMES, map(float, gen.observe(obs)[1])))
    points = {'current surface': {side: [current[side+'_'+axis] for axis in ('x','y','z')]
                                 for side in ('left','right')}}
    grounding = RepairGrounding(SimpleNamespace(), lambda report: None)
    grounding.snapshot = SimpleNamespace(age=lambda: .1)
    result = grounding.resolve({'expectation':'above measured point', 'steps':[
        {'op':'move_to_point','arm':arm,'point':'current surface','offset':[0,0,.01]}]}, points)
    adapter = SpotterAdapter(SimpleNamespace(model='offline'),SimpleNamespace(model='offline'),gen,robot_id=RID,camera_source=None)
    try:
        path = send(adapter._primitive(validate_plan(result)[0], obs, 4))
        assert path[0]['step_id'] == 4 and len(path) >= 1
    finally: adapter.close_transport()


@pytest.mark.parametrize('value', [float('nan'),float('inf'),-.0000000000000001])
def test_invalid_cartesian_target_never_dispatches(bridge, value):
    send, wire = bridge; gen = geometry()
    with pytest.raises(ValueError): send(gen.build({'left_x':value},measured(),0))
    assert wire == []


@pytest.mark.parametrize('arm', ['left','right'])
def test_invalid_measured_fraction_never_dispatches(bridge, arm):
    send, wire = bridge;obs=measured();obs[arm+'_gripper']=-1e-16
    with pytest.raises(RuntimeError,match='normalized gripper'):send(geometry().build({arm+'_gripper':0},obs,0))
    assert wire==[]


def test_base_dream_joint_chunk_reaches_actual_serializer_without_network(bridge, tmp_path):
    from spotter_yam.dream import SpotterDreamAdapter
    from remote_yam.dream_policy import state_input
    send, _ = bridge; obs = measured()
    base = SpotterDreamAdapter(provider='dream',model='dreamlabs/dream-1-beta',credentials='unused',
        python='unused',directory=tmp_path,camera_source=None,observation_source=None,robot_id=RID)
    base._ready.set();base._preparation=base._collector=object()
    tick={'observation':state_input(obs,'offline joint chunk'),'observed_at':obs['observed_at']}
    base._wait_for_ticks=lambda *a,**k:[tick]
    action={key:[[*np.deg2rad(obs[arm+'_joints_deg']).tolist(),obs[arm+'_gripper']]]*2
            for arm,key in [('left','q_l_chunk'),('right','q_r_chunk')]}
    base._worker=SimpleNamespace(call=lambda *a,**k:{'ok':True,'result':{'action':action}})
    path=send(base.build_trajectory('offline joint chunk',obs,0))
    assert path[0]['step_id']==0 and len(path)>=1
    assert np.allclose(path[-1]['left_joints_deg'],obs['left_joints_deg'],atol=1e-12)


@pytest.mark.parametrize('arm', ['left', 'right'])
def test_longer_selected_plan_reaches_real_validator_with_exact_endpoints(bridge, arm):
    send, wire = bridge; obs = measured(); gen = geometry()
    adapter = SpotterAdapter(SimpleNamespace(model='offline'), SimpleNamespace(model='offline'), gen,
        robot_id=RID, camera_source=None, max_plan_steps=16, max_plan_rounds=6)
    result = dict(expectation='test exact fractions over a longer bounded plan', steps=[
        dict(op='gripper', arm=arm, value=value) for value in [0, .37, 1] * 4])
    try:
        first = 0
        for step in validate_plan(result, max_steps=adapter.max_plan_steps):
            path = send(adapter._primitive(step, obs, first))
            assert path[-1][arm+'_gripper'] == step['value']
            assert path[0]['step_id'] == first
            obs = {**obs, **path[-1], 'settled': True, 'observed_at': time.time()}
            first += len(path)
        assert len(wire) == 12
        with pytest.raises(ValueError): validate_plan(result, max_steps=8)
        assert len(wire) == 12  # Rejecting a smaller budget sends nothing else.
    finally: adapter.close_transport()
