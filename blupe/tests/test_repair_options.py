"""Visitor-specific repair settings reach the adapter before queue admission."""
import json
from pathlib import Path
import subprocess
from threading import RLock
from types import SimpleNamespace

import pytest

from playground import HostedRunner, RequestError
from spotter_yam.app import SpotterApp
from spotter_yam.limits import repair_limits
from spotter_yam.repair_contract import repair_example, repair_schema
from test_spotter import adapter


@pytest.mark.parametrize('value', [None, [], '16', {'max_plan_steps': True}, {'max_plan_steps': 0},
    {'max_plan_steps': 33}, {'max_plan_steps': 1.5}, {'max_plan_rounds': 13},
    {'max_plan_rounds': -1}, {'max_plan_rounds': float('nan')}, {'unknown': 1}])
def test_invalid_api_limits_reject_before_provider_or_queue(value):
    with pytest.raises(RequestError): SpotterApp.launch_limits({'spotter': value})


def test_defaults_and_explicit_boundary_values():
    assert repair_limits() == dict(max_plan_steps=16, max_plan_rounds=6)
    assert repair_limits(dict(max_plan_steps=1, max_plan_rounds=12)) == dict(max_plan_steps=1, max_plan_rounds=12)
    assert repair_schema({'max_plan_steps': 32})['properties']['steps']['maxItems'] == 32


def test_launch_passes_selected_limits_without_changing_next_visitor(monkeypatch, adapter):
    app = object.__new__(SpotterApp)
    captured = []
    def launch(self, visitor, payload, **kwargs):
        kwargs['provider_transform'](adapter)
        captured.append((payload, adapter.public_config()))
        return dict(attempt_id='offline')
    monkeypatch.setattr(HostedRunner, 'launch', launch)
    app.launch(SimpleNamespace(), dict(provider='spotter',spotter=dict(max_plan_steps=24,max_plan_rounds=9)))
    assert captured[0][0]['run_duration_s'] == 600
    assert captured[0][1]['max_plan_steps'] == 24 and captured[0][1]['max_plan_rounds'] == 9
    app.launch(SimpleNamespace(), dict(provider='spotter',run_duration_s=120))
    assert captured[1][0]['run_duration_s'] == 120
    assert captured[1][1]['max_plan_steps'] == 16 and captured[1][1]['max_plan_rounds'] == 6
    adapter._rounds = 1
    with pytest.raises(ValueError,match='before a run'): adapter.configure_limits(max_plan_steps=32,max_plan_rounds=12)


def test_full_example_contains_grasp_check_transport_release_and_withdrawal():
    response=json.loads(repair_example()[1]['content'])
    steps=response['steps']
    assert any(s['op']=='gripper' and s['value']==0 for s in steps)
    check=next(i for i,s in enumerate(steps) if s.get('intent')=='grasp_check')
    assert any(s.get('point')=='plate unoccupied surface' for s in steps[check+1:])
    assert steps[-3]['op']=='gripper' and steps[-3]['value']==1
    assert steps[-2]['intent']=='clearance'
    assert len(json.loads(repair_example(max_steps=3)[1]['content'])['steps'])==3


def test_actual_limits_and_model_roles_are_retained_in_run_configuration(monkeypatch, adapter):
    app=object.__new__(SpotterApp)
    adapter.configure_limits(max_plan_steps=24,max_plan_rounds=9)
    controller=SimpleNamespace(_lock=RLock(),_run_configuration={'provider':'spotter'},
        status=lambda:{'provider':adapter.public_config()})
    visitor=SimpleNamespace(lock=RLock(),controller=controller)
    monkeypatch.setattr(HostedRunner,'remember_runner',lambda *a:None)
    app.remember_runner(visitor)
    assert controller._run_configuration['spotter']==dict(max_plan_steps=24,max_plan_rounds=9,max_interventions=8)
    assert controller._run_configuration['underlying_models']['base_model']==adapter.base.model


def test_browser_settings_serialize_only_selected_spotter_run(tmp_path):
    script=Path(__file__).resolve().parents[1]/'static/site.js'
    code="""
const vm=require('node:vm'), fs=require('node:fs'), assert=require('node:assert/strict');
const fields={provider:{value:'spotter'},spotterRepairSteps:{value:'24'},spotterRepairRounds:{value:'9'}};
const context={window:{},document:{getElementById:id=>fields[id]}};
vm.createContext(context); vm.runInContext(fs.readFileSync(process.argv[1],'utf8'),context);
const payload=()=>JSON.parse(JSON.stringify(context.window.yamApplication.runPayload()));
assert.deepEqual(payload(),{spotter:{max_plan_steps:24,max_plan_rounds:9}});
fields.spotterRepairSteps.value='33'; assert.throws(payload,/1–32/);
fields.spotterRepairSteps.value=''; assert.throws(payload,/1–32/);
fields.provider.value='dream'; assert.deepEqual(payload(),{});
fields.provider.value='spotter'; delete fields.spotterRepairSteps; assert.deepEqual(payload(),{});
"""
    subprocess.run(['node','-e',code,str(script)],check=True,capture_output=True,text=True)
