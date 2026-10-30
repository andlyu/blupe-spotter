import json
from pathlib import Path

import pytest

from spotter_yam.motion import retime


def fixture():
    return json.loads((Path(__file__).parent / 'fixtures/rejected-dreamzero.json').read_text())


def largest_step(points, observation):
    previous = observation
    distances = []
    for point in points:
        distances.extend(abs(a-b) for side in ('left','right')
                         for a,b in zip(previous[side+'_joints_deg'],point[side+'_joints_deg']))
        previous = point
    return max(distances)


def test_rejected_hardware_packet_is_retimed_without_changing_policy_targets():
    saved = fixture()
    raw, obs, start = saved['points'], saved['observation'], saved['first_step_id']
    assert largest_step(raw,obs) > 9  # Actual gateway rejection in trial ep_bfc81ebb65c34c24.
    output = retime(raw,obs,start,8.1)
    assert largest_step(output,obs) <= 8.1 + 1e-12
    assert [p['step_id'] for p in output] == list(range(start,start+len(output)))
    # Every original target, including grippers, remains in order and exact.
    targets = [{k:v for k,v in p.items() if k!='step_id'} for p in raw]
    found = 0
    for point in output:
        if {k:v for k,v in point.items() if k!='step_id'} == targets[found]:
            found += 1
            if found == len(targets):break
    assert found == len(targets)
    assert len(output) > len(raw)


def test_oversized_retiming_rejects_entire_packet():
    saved=fixture()
    with pytest.raises(ValueError,match='packet budget'):
        retime(saved['points'],saved['observation'],2999,8.1)


def test_cancelled_retiming_returns_no_partial_path():
    saved=fixture()
    with pytest.raises(RuntimeError,match='cancelled'):
        retime(saved['points'],saved['observation'],0,8.1,cancelled=lambda:True)
