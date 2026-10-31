from types import SimpleNamespace
import numpy as np
import pytest

from spotter_yam.grounding import RepairGrounding


class Snapshot:
    metadata = {'captured_at': 101., 'calibration_id': 'fit', 'camera': 'top'}
    calibration = {'quality': {'status': 'experimental_requires_fresh_validation'}}
    rgb = np.zeros((480, 640, 3), dtype=np.uint8)
    def image(self): return b'paired-native-image'
    def age(self): return .5
    def measure(self, u, v, *, arm):
        assert (u, v) == (286, 146)
        return {'point_base_m': [.49, -.21 if arm == 'left' else .41, .05],
                'captured_at': 101., 'calibration_id': 'fit'}


def ground(snapshot=None, selection=None):
    source = SimpleNamespace(capture=lambda **kwargs: snapshot or Snapshot())
    selector = SimpleNamespace(locate=lambda *args: selection or {
        'points': [{'name': 'block', 'point_1000': [447, 304]}]})
    value = RepairGrounding(source, lambda report: None)
    history, context, points = value.capture('move object', [{'frames': (),
        'measured': {'observed_at': 100.}}], selector, lambda: False)
    return value, history, context, points


def test_pixel_uses_paired_native_image_and_named_arm_transform():
    value, history, context, points = ground()
    assert history[-1]['frames'][0].jpeg == b'paired-native-image'
    assert context['image_size'] == [640, 480]
    assert context['quality']['status'] == 'experimental_requires_fresh_validation'
    result = value.resolve({'expectation': 'grasp', 'steps': [
        {'op': 'move_to_point', 'arm': 'left', 'point': 'block', 'offset': [0, 0, .06]}]}, points)
    assert result['steps'] == [{'op': 'move_to', 'arm': 'left',
                               'xyz': pytest.approx([.49, -.21, .11])}]


@pytest.mark.parametrize('step', [
    {'op': 'move_to', 'arm': 'left', 'xyz': [.3, 0, .1]},
    {'op': 'move_to_point', 'arm': 'right', 'point': 'invented', 'offset': [0, 0, 0]},
    {'op': 'move_to_point', 'arm': 'left', 'point': 'block', 'offset': [0, 0, float('nan')]},
    {'op': 'move_to_point', 'arm': 'left', 'point': 'block', 'offset': [.4, 0, 0]},
    {'op': 'nudge', 'arm': 'left', 'dxyz': [.1, 0, 0]},
])
def test_unguarded_absolute_or_ungrounded_horizontal_targets_are_rejected(step):
    value, _, _, points = ground()
    with pytest.raises(ValueError): value.resolve({'steps': [step]}, points)


@pytest.mark.parametrize('selection', [
    {'points': [{'name': 'block', 'point_1000': [1001, 146]}]},
    {'points': [{'name': 'block', 'point_1000': [447.5, 304]}]},
    {'points': [{'name': 'block', 'point_1000': [447, 304]}, {'name': 'block', 'point_1000': [447, 304]}]},
])
def test_bad_pixels_and_ambiguous_names_never_become_motion(selection):
    with pytest.raises(ValueError): ground(selection=selection)


def test_depth_preceding_settled_feedback_is_rejected():
    old = Snapshot(); old.metadata = {**old.metadata, 'captured_at': 99.}
    with pytest.raises(ValueError, match='settled'): ground(snapshot=old)


def test_grounded_plan_ages_out_and_cannot_be_reused_after_slow_inference():
    value, _, _, points = ground()
    value.snapshot.age = lambda: 6.
    with pytest.raises(ValueError, match='aged'):
        value.resolve({'steps': [{'op': 'move_to_point', 'arm': 'left', 'point': 'block',
                                 'offset': [0, 0, .06]}]}, points)


def test_policy_handback_needs_no_expired_geometric_target():
    value, _, _, points = ground()
    value.snapshot.age = lambda: 6.
    assert value.resolve({'steps': [{'op': 'policy'}]}, points)['steps'] == [{'op': 'policy'}]


@pytest.mark.parametrize('steps', [None, ['not an action']])
def test_non_action_json_values_become_recoverable_validation_errors(steps):
    value, _, _, points = ground()
    with pytest.raises(ValueError, match='action objects'):
        value.resolve({'steps': steps}, points)


def test_slow_plan_refreshes_and_checks_the_selected_surface_before_motion():
    value, _, _, points = ground()
    value.snapshot.age = lambda: 6.
    fresh = Snapshot(); fresh.metadata = {**fresh.metadata, 'captured_at': 102.}
    value.source.capture = lambda **kw: fresh
    result = value.resolve({'steps': [{'op': 'move_to_point', 'arm': 'right',
        'point': 'block', 'offset': [0, 0, .06]}]}, points)
    assert result['steps'][0]['xyz'] == pytest.approx([.49, .41, .11])
    assert value.snapshot is fresh


def test_changed_scene_during_planning_does_not_authorize_the_old_target():
    value, _, _, points = ground()
    value.snapshot.age = lambda: 6.
    fresh = Snapshot(); fresh.metadata = {**fresh.metadata, 'captured_at': 102.}
    fresh.rgb = np.full((480, 640, 3), 255, dtype=np.uint8)
    value.source.capture = lambda **kw: fresh
    with pytest.raises(ValueError, match='changed'):
        value.resolve({'steps': [{'op': 'move_to_point', 'arm': 'right',
            'point': 'block', 'offset': [0, 0, .06]}]}, points)


@pytest.mark.parametrize('change', ['depth', 'calibration'])
def test_changed_geometry_cannot_pass_refresh_using_unchanged_rgb(change):
    value, _, _, points = ground()
    value.snapshot.age = lambda: 6.
    fresh = Snapshot(); fresh.metadata = {**fresh.metadata, 'captured_at': 102.}
    if change == 'calibration': fresh.metadata['calibration_id'] = 'different-fit'
    else:
        fresh.measure = lambda *a, arm: {'point_base_m': [.6, 0, .1]}
    value.source.capture = lambda **kw: fresh
    with pytest.raises(ValueError, match='changed'):
        value.resolve({'steps': [{'op': 'move_to_point', 'arm': 'left',
            'point': 'block', 'offset': [0, 0, .06]}]}, points)
