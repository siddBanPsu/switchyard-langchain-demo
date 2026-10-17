"""Exercise the real Switchyard classifier with fake transport, not fake routing."""
import asyncio
import importlib.util
import json
import sys
from pathlib import Path
import pytest

folder=Path(__file__).resolve().parents[1]/'examples/checkout-support/lightning-gpt-sol-judge'
sys.path.insert(0,str(folder.parent))
spec=importlib.util.spec_from_file_location('checkout_judge',folder/'judge.py')
judge=importlib.util.module_from_spec(spec);spec.loader.exec_module(judge)

@pytest.mark.parametrize('image,p_solve,tier',[(False,.95,'weak'),(True,.05,'strong'),(True,.99,'weak'),(False,None,'strong')])
def test_model_forecast_controls_actual_switchyard_target(monkeypatch,image,p_solve,tier):
    monkeypatch.setenv('NVIDIA_API_KEY','test-key');monkeypatch.setenv('NVIDIA_BASE_URL','https://example.invalid/v1')
    original=[judge.demo.image_message()] if image else [{'role':'user','content':'Extract supplied text.'}]
    async def transport(self,messages,**kwargs):
        is_judge=kwargs.get('kind')=='routing_judge'
        if is_judge:
            text=json.dumps(messages)
            assert 'data:image/' not in text
            value=dict(crux='Material requirement',primary_rule='SUP-1' if p_solve is not None and p_solve>=.75 else 'LIM-1',
                capability_boundary='supported' if p_solve is not None and p_solve>=.75 else 'unsupported',p_solve=p_solve)
        else:
            assert messages==original  # The actual image payload is never replaced by metadata.
            assert kwargs['selected_tier']==tier
            value={'ok':True}
        message={'role':'assistant','content':'not JSON' if is_judge and p_solve is None else json.dumps(value)}
        self.calls.append(dict(kind=kwargs['kind'],message=message,cost_usd=.001))
        return message
    monkeypatch.setattr(judge.demo.Engine,'call',transport)
    async def check():
        engine=judge.JudgeEngine('routed')
        await engine.call(original,kind='vision' if image else 'backend_text')
        assert engine.decisions[0]['selected_tier']==tier
        if p_solve is None:assert 'judge_issue' in engine.decisions[0]
        assert len(engine.calls)==2 and engine.calls[0]['role']=='judge' and engine.calls[1]['role']=='executor'
        assert sum(c['cost_usd'] for c in engine.calls)==pytest.approx(.002)
    asyncio.run(check())


def test_super_variant_declares_actual_capable_model(monkeypatch):
    monkeypatch.setenv('NVIDIA_API_KEY','test-key');monkeypatch.setenv('NVIDIA_BASE_URL','https://example.invalid/v1')
    engine=judge.JudgeEngine('routed',folder.parent/'lightning-super-vl-judge')
    assert engine.strong=='nvidia/nvidia/nemotron-3.5-super-vl'
    assert 'NVIDIA Nemotron 3.5 Super VL' in engine.judge_prompt
    assert 'GPT Sol' not in engine.judge_prompt
    assert engine.light==engine.config['roles']['judge']['model_id']


@pytest.mark.parametrize('variant',['lightning-gpt-sol-judge','lightning-super-vl-judge'])
def test_single_run_entrypoints_reject_repetitions(variant):
    path=folder.parent/variant/'run.py'
    spec=importlib.util.spec_from_file_location('single_run_'+variant.replace('-','_'),path)
    module=importlib.util.module_from_spec(spec)
    sys.path.insert(0,str(path.parent))
    spec.loader.exec_module(module)
    # Failure occurs before constructing an engine or looking up credentials.
    with pytest.raises(ValueError,match='exactly one'):
        asyncio.run(module.compare(repeats=2))
