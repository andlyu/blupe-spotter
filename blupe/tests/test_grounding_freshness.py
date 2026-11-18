"""Review probe: expired scene data must not authorize ungrounded XY repair.

Uses the repository's actual geometry, canonical validator and serialized-wire
transport spy. No physical session or model inference is used.
"""
from types import SimpleNamespace

import pytest

from spotter_yam.grounding import RepairGrounding
from spotter_yam.policy import SpotterAdapter, validate_plan
from remote_yam.robocurve_trajectory import NAMES
from test_control_contract import bridge, geometry, measured
from test_grounding import ground, Snapshot


@pytest.mark.parametrize('arm', ['left', 'right'])
@pytest.mark.parametrize('op', ['move_to', 'nudge'])
def test_expired_depth_does_not_authorize_raw_xy_packet(bridge, arm, op):
    send, wire = bridge
    obs, gen = measured(), geometry()
    current = dict(zip(NAMES, map(float, gen.observe(obs)[1])))
    xyz = [current[arm + '_' + axis] + (.035 if axis == 'x' else 0)
           for axis in ('x', 'y', 'z')]
    step = ({'op': op, 'arm': arm, 'xyz': xyz} if op == 'move_to'
            else {'op': op, 'arm': arm, 'dxyz': [.035, 0, 0]})
    refreshes = []
    def unavailable(**kwargs):
        refreshes.append(kwargs)
        raise ValueError('Fresh paired depth unavailable')
    grounding = RepairGrounding(SimpleNamespace(capture=unavailable), lambda report: None)
    grounding.snapshot = SimpleNamespace(age=lambda: 6.)
    points = {'old surface': {side: [current[side + '_' + axis] for axis in ('x', 'y', 'z')]
                              for side in ('left', 'right')}}
    adapter = SpotterAdapter(SimpleNamespace(model='offline'), SimpleNamespace(model='offline'),
                             gen, robot_id=obs['jetson_id'], camera_source=None)
    rejected = None
    try:
        try:
            result = grounding.resolve({'expectation': 'approach visible object', 'steps': [step]}, points)
            action = validate_plan(result)[0]
            send(adapter._primitive(action, obs, 0))
        except ValueError as exc:
            rejected = exc
        assert wire == [], (f'{op}/{arm}: {len(wire)} serialized actuator packet reached the intercepted '
                            f'transport despite 6-second-old depth; fresh-capture calls={len(refreshes)}')
        assert rejected is not None
    finally:
        adapter.close_transport()


@pytest.mark.parametrize('op', ['move_to', 'nudge'])
@pytest.mark.parametrize('changed', [None, 'rgb', 'depth', 'calibration'])
def test_raw_moves_refresh_all_surfaces_after_slow_planning(op, changed):
    import numpy as np
    value, _, _, points = ground()
    value.snapshot.age = lambda: 6.
    fresh = Snapshot(); fresh.metadata = {**fresh.metadata, 'captured_at': 102.}
    if changed == 'rgb': fresh.rgb = np.full_like(fresh.rgb, 255)
    elif changed == 'depth': fresh.measure = lambda *args, arm: {'point_base_m': [.7, 0, .2]}
    elif changed == 'calibration': fresh.metadata['calibration_id'] = 'different'
    value.source.capture = lambda **kwargs: fresh
    step = ({'op': op, 'arm': 'left', 'xyz': [.3, 0, .1]} if op == 'move_to'
            else {'op': op, 'arm': 'left', 'dxyz': [.03, 0, 0]})
    if changed:
        with pytest.raises(ValueError, match='changed'): value.resolve({'steps': [step]}, points)
    else:
        assert value.resolve({'steps': [step]}, points)['steps'] == [step]
        assert value.snapshot is fresh and value.last_refresh['points']


def test_missing_depth_blocks_raw_xy_but_keeps_clearance_lift():
    value, _, _, _ = ground()
    with pytest.raises(ValueError, match='measured scene'):
        value.resolve({'steps': [{'op': 'move_to', 'arm': 'left', 'xyz': [.3, 0, .1]}]}, {})
    step = {'op': 'lift', 'arm': 'left', 'dz': .04, 'intent': 'clearance'}
    assert value.resolve({'steps': [step]}, {})['steps'] == [step]
