import json
from types import SimpleNamespace

from spotter_yam.vlm import TwoStageSupervisor, VisionSupervisor
from spotter_yam.repair_contract import repair_example, repair_schema
from test_vlm import provider


def test_stage_roles_are_independent_and_readiness_checks_both():
    calls = []
    def stage(name):
        return SimpleNamespace(model=name, **{method: (lambda *a, _m=method, **k: calls.append((name, _m)))
            for method in ('ready', 'screen', 'judge', 'repair', 'locate', 'verify')})
    value = TwoStageSupervisor(stage('qwen/qwen3.8-27b'), stage('openai/gpt-6.1-sol'))
    value.ready(); value.screen('task', []); value.judge('task', [], {}); value.locate('task', [])
    value.repair('task', [], {}); value.verify('task', [], {})
    assert calls[:3] == [('qwen/qwen3.8-27b', 'ready'), ('openai/gpt-6.1-sol', 'ready'), ('qwen/qwen3.8-27b', 'screen')]
    assert all(name == 'openai/gpt-6.1-sol' for name, _ in calls[3:])


def test_sol_repair_uses_supported_parameters_strict_current_point_names_and_real_image_example():
    plan = {'why': 'restage', 'expectation': 'above object', 'steps': [{'op': 'policy'}]}
    with provider(plan) as (endpoint, requests):
        value = VisionSupervisor(endpoint, 'openai/gpt-6.1-sol', 'test-key', api_style='openrouter', use_repair_example=True)
        assert value.repair('CURRENT TASK', [], {'grounding': {'points': {'CURRENT BLOCK': {}, 'CURRENT PLATE': {}}}}) == plan
        body = requests[0][3]
        assert 'temperature' not in body and body['reasoning'] == {'effort': 'low'}
        schema = body['response_format']['json_schema']
        assert schema['strict'] is True
        variants = schema['schema']['properties']['steps']['items']['anyOf']
        point = next(x for x in variants if x['properties']['op']['enum'] == ['move_to_point'])
        assert point['properties']['point']['enum'] == ['CURRENT BLOCK', 'CURRENT PLATE']
        assert not any(x['properties']['op']['enum'] in (['move_to'], ['nudge']) for x in variants)
        assert [m['role'] for m in body['messages']] == ['system', 'user', 'assistant', 'user']
        assert len([x for x in body['messages'][1]['content'] if x['type'] == 'image_url']) == 3
        assert 'not an executed or successful demonstration' in body['messages'][1]['content'][0]['text']
        assert 'CURRENT TASK' in body['messages'][-1]['content'][0]['text']


def test_grounding_without_points_never_offers_a_hallucinated_target():
    variants = repair_schema({'grounding': {'points': {}}})['properties']['steps']['items']['anyOf']
    assert not any('point' in x['properties'] or 'xyz' in x['properties'] for x in variants)
    assert len(repair_example()) == 2


def test_scene_screener_names_concrete_failures_without_assuming_every_stationary_object_failed():
    with provider({'flag': False, 'risk': 0, 'why': 'initial approach'}) as (endpoint, requests):
        value = VisionSupervisor(endpoint, 'qwen/qwen3.8-27b', 'key', api_style='openrouter')
        value.screen('put block onto plate', [])
        prompt = requests[0][3]['messages'][0]['content']
        assert 'not RoboTwin or RoboCasa' in prompt
        assert 'repeated failed attempts' in prompt and 'first approach is normal' in prompt
