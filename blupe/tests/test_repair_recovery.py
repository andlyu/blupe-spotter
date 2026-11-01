"""Reproduce dropped depth-recovery ownership and truncated repair budgets."""
from types import SimpleNamespace

import pytest

from spotter_yam.policy import validate_plan
from spotter_yam.repair_contract import repair_schema
from test_spotter import adapter, observation, finished


def test_sixteen_step_plan_is_legal_and_selected_smaller_budget_is_enforced():
    result = dict(expectation='complete the measured sequence', steps=[
        dict(op='gripper', arm='left', value=i % 2) for i in range(16)])
    assert len(validate_plan(result, max_steps=16)) == 16
    with pytest.raises(ValueError): validate_plan(result, max_steps=8)
    assert repair_schema({'max_plan_steps': 16})['properties']['steps']['maxItems'] == 16


def test_clearance_remeasures_before_handback_or_stale_pending_target(adapter):
    captures, plans = [], []
    def capture(task, history, supervisor, cancelled):
        captures.append(history[-1]['measured']['step_id'])
        return history, {'points': {} if len(captures) == 1 else {'fresh block': {}},
                         'omitted': [{'name': 'block', 'reason': 'no depth'}] if len(captures) == 1 else []}, {}
    adapter.grounding = SimpleNamespace(capture=capture, resolve=lambda result, points: result, close=lambda: None)
    def repair(task, history, context):
        plans.append(context)
        steps = ([dict(op='lift', arm='left', dz=.05, intent='clearance'),
                  dict(op='move_to', arm='left', xyz=[.9, 0, .2]), dict(op='policy')]
                 if len(plans) == 1 else [dict(op='move_to', arm='left', xyz=[.4, 0, .2]), dict(op='policy')])
        return dict(expectation='clear the view, then repair from fresh depth', steps=steps)
    adapter.supervisor.repair = repair
    adapter._chunks = 2
    adapter._future = (1, finished(dict(verdict='intervene', why='missed grasp and occluded depth')))
    adapter.build_trajectory('put block onto plate', observation(0), 0)
    adapter.trajectory_completed(observation(1), 1)
    adapter.build_trajectory('put block onto plate', observation(1), 1)
    assert captures == [0, 1]
    assert plans[1]['after_clearance'] is True and 'fresh block' in plans[1]['grounding']['points']
    assert not adapter.base.calls
    assert adapter.geometry.targets[-1][0]['left_x'] == .4
    assert not any(target.get('left_x') == .9 for target, _, _ in adapter.geometry.targets)


def test_cancelled_clearance_never_remeasures_or_dispatches_a_next_step(adapter):
    adapter._repair_context = dict(expectation='clear the view')
    adapter._primitive(dict(op='lift', arm='left', dz=.05, intent='clearance'), observation(), 0)
    adapter.cancelled = lambda: True
    adapter.grounding = SimpleNamespace(capture=lambda *a: pytest.fail('cancelled'), close=lambda: None)
    with pytest.raises(RuntimeError, match='cancelled'): adapter.build_trajectory('task', observation(1), 1)
    assert len(adapter.geometry.targets) == 1 and not adapter.base.calls


def test_previous_intervention_is_available_when_same_failure_returns(adapter):
    adapter._chunks = 2
    adapter._future = (1, finished(dict(verdict='intervene', why='missed grasp')))
    adapter.build_trajectory('move block', observation(0), 0)
    adapter.trajectory_completed(observation(1), 1)
    adapter.build_trajectory('move block', observation(1), 1)
    adapter._post_policy_expectation = None
    if adapter._future: adapter._future[1].result(timeout=2)
    adapter._future = (adapter._chunks, finished(dict(verdict='intervene', why='same missed grasp')))
    adapter.build_trajectory('move block', observation(2), 2)
    context = adapter.supervisor.plans[-1][1]
    assert context['repeated_intervention'] is True
    assert context['previous_repairs'][-1]['status'] == 'handed_back'
    assert context['previous_repairs'][-1]['intervention'] == 1


def test_segment_without_explicit_handback_keeps_repair_ownership(adapter):
    adapter._repair_context = dict(expectation='finish grasp before handback')
    adapter._primitive(dict(op='gripper', arm='left', value=0), observation(), 0)
    adapter.trajectory_completed(observation(1), 1)
    adapter.build_trajectory('move block', observation(1), 1)
    assert adapter.supervisor.plans and not adapter.base.calls


def test_recovery_remains_bounded_by_the_selected_round_limit(adapter):
    adapter.max_plan_rounds = 1
    adapter._rounds = 1
    adapter._repair_context = dict(expectation='clear view')
    adapter._primitive(dict(op='lift', arm='left', dz=.05, intent='clearance'), observation(), 0)
    adapter.grounding = SimpleNamespace(capture=lambda *a: pytest.fail('budget exhausted'), close=lambda: None)
    with pytest.raises(RuntimeError, match='plan budget'): adapter.build_trajectory('task', observation(1), 1)
    assert not adapter.base.calls
