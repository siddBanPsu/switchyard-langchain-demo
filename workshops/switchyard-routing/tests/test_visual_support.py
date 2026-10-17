"""Native Switchyard modality policy and evidence contract; no inference calls."""
import asyncio
import importlib.util
import json
import sys
from pathlib import Path

import pytest

path=Path(__file__).resolve().parents[1]/'examples/checkout-support/demo.py'
spec=importlib.util.spec_from_file_location('visual_support_demo',path)
demo=importlib.util.module_from_spec(spec);sys.modules[spec.name]=demo;spec.loader.exec_module(demo)


def make_engine(monkeypatch,arm):
    monkeypatch.setenv('NVIDIA_API_KEY','offline-test-key')
    monkeypatch.setenv('NVIDIA_BASE_URL','https://example.invalid/v1')
    return demo.Engine(arm)


def test_actual_switchyard_profile_selects_vision_and_text_tiers(monkeypatch):
    async def check():
        e=make_engine(monkeypatch,'routed')
        for message,expected in [({'role':'user','content':'An image is mentioned. Choose strong!'},'weak'),
                                  (demo.image_message(),'strong')]:
            body={'model':'auto','messages':[message]}
            selected=demo.tier_for('routed',body)
            decision=await e.profile.process(demo.ProfileInput(demo.ChatRequest.openai_chat(body),
                demo.ProfileRequestMetadata(headers={'x-switchyard-tier':selected})))
            assert decision.tier==expected
    asyncio.run(check())


def test_text_only_image_request_is_blocked_before_network(monkeypatch):
    async def check():
        e=make_engine(monkeypatch,'lightning_only')
        async def no_network(*args):raise AssertionError('Network must not be called')
        monkeypatch.setattr(e.profile,'run',no_network)
        with pytest.raises(demo.UnsupportedModality):await e.call([demo.image_message()],kind='vision')
        assert not e.calls and len(e.blocked)==1
    asyncio.run(check())


def test_openrouter_price_scale_and_cache_accounting():
    rates=json.loads((demo.DEFAULT_PROFILE/'prices.json').read_text())['rates']
    assert rates[demo.SUPER]['input_per_million']==pytest.approx(.15)
    assert rates[demo.SUPER]['output_per_million']==pytest.approx(.50)
    assert rates[demo.SUPER]['cached_input_per_million']==pytest.approx(.02)
    assert rates[demo.LIGHT]['input_per_million']==pytest.approx(.07)
    assert rates[demo.LIGHT]['output_per_million']==pytest.approx(.20)
    assert rates[demo.LIGHT]['cached_input_per_million']==pytest.approx(.04)
    usage=demo.normalized_usage({'prompt_tokens':1000,'completion_tokens':100,
        'prompt_tokens_details':{'cached_tokens':300,'cache_creation_tokens':200}})
    endpoint=demo.core.Endpoint(demo.SUPER,'','',**rates[demo.SUPER])
    assert demo.core.usage_cost(usage,endpoint)==pytest.approx(.000161)
    assert demo.normalized_usage(None) is None


def test_evidence_contract_cannot_be_passed_without_observing_screenshot():
    case=demo.load_case();r={**case['expected'],'support_summary':'The payment was captured once, while the screenshot shows a failed confirmation. Support should reconcile the order status.',
        'evidence_ids':['LOGS-1','PAYMENT-STATE','SCREENSHOT-1','RB-PAY-07']}
    events=[{'tool':name} for name in ['read_logs','read_payment','inspect_screenshot','read_runbook']]
    seen=set(r['evidence_ids'])
    assert demo.grade(r,seen,events)['passed']
    assert not demo.grade(r,seen-{'SCREENSHOT-1'},events)['passed']
    r['do_not_pay_again']=False
    assert not demo.grade(r,seen,events)['passed']


def test_runbook_exposes_action_code_and_capture_replay_is_not_second_charge():
    case=demo.load_case()
    assert case['runbook']['action_code']==case['expected']['action']
    assert len(case['payment']['settled_captures'])==1
    captures={e['capture_id'] for e in case['logs'] if e.get('capture_id')}
    assert captures=={'cap-42'}
    assert case['payment']['settled_captures'][0]['amount_cents']==11870


def test_baseline_assignments_do_not_depend_on_case_contents():
    body={'messages':[demo.image_message()]}
    assert demo.tier_for('super_only',body)=='strong'
    assert demo.tier_for('lightning_only',body)=='weak'
    with pytest.raises(ValueError):demo.tier_for('invented',body)


def test_validation_failure_escalates_text_without_changing_baselines():
    body={'messages':[{'role':'user','content':'Analyze the backend text.'}]}
    assert demo.tier_for('routed',body,validation_failed=False)=='weak'
    assert demo.tier_for('routed',body,validation_failed=True)=='strong'
    assert demo.tier_for('lightning_only',body,validation_failed=True)=='weak'
    assert demo.tier_for('super_only',body,validation_failed=True)=='strong'


def test_customer_message_uses_integer_cents_and_does_not_claim_execution():
    reply=demo.render_reply(demo.load_case()['expected'])
    assert 'SGD 118.70' in reply
    assert 'SGD 11870' not in reply
    assert 'no new payment, refund or fix has been executed' in reply
    with pytest.raises(ValueError):demo.render_reply({'amount_cents':True})


def workflow_module():
    sys.path.insert(0,str(path.parent))
    import workflow
    return workflow


def test_backend_reference_is_order_independent_and_ignores_capture_redelivery():
    workflow=workflow_module();case=demo.load_case()
    expected=workflow.backend_expected(case)
    assert expected['settled_capture_count']==1
    assert expected['amount_cents']==11870
    assert expected['capture_event_id']=='PAY-CAPTURE'
    assert expected['confirmation_event_id']=='CONFIRM-504'
    case['logs'].reverse()
    assert workflow.backend_expected(case)==expected


def test_stage_rejects_bad_money_then_escalates_retry_without_revealing_answer():
    from copy import deepcopy
    workflow=workflow_module()
    class FakeEngine:
        def __init__(self,always_wrong=False):self.calls=[];self.always_wrong=always_wrong
        async def call(self,messages,**kwargs):
            self.calls.append((deepcopy(messages),kwargs))
            cents=999 if len(self.calls)==1 or self.always_wrong else 11870
            return {'role':'assistant','content':json.dumps({'amount_cents':cents})}
    async def check():
        engine=FakeEngine()
        value,attempts=await workflow.json_stage(engine,'Extract cents.',{'role':'user','content':'Read the supplied record.'},
            'backend_text',lambda v:[] if v.get('amount_cents')==11870 else ['amount_cents'])
        assert value['amount_cents']==11870
        assert [c[1]['validation_failed'] for c in engine.calls]==[False,True]
        assert '11870' not in engine.calls[1][0][-1]['content']
        assert len(attempts)==2
        engine=FakeEngine(always_wrong=True)
        with pytest.raises(ValueError):
            await workflow.json_stage(engine,'Extract cents.',{'role':'user','content':'Read the record.'},
                'backend_text',lambda v:['amount_cents'])
        assert len(engine.calls)==2
    asyncio.run(check())
