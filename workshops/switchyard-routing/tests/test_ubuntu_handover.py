import json
import pytest
import ubuntu_handover_demo as demo
import incident_demo as core
import ubuntu_savings_demo as savings


def report():
    return dict(environment='Ubuntu 14.04.2 reported; running kernel 3.11.',
        contradictions=['Initially denied any extra command, later admitted interrupted do-release-upgrade -d.'],
        attempted_actions=['Corrected repository entries and tried package updates.'],
        successful_remedy='Helper advised sudo apt-get install linux-generic.',
        outcome='Customer reported that did it; issue reported resolved.',
        unknowns=['Post-reboot uname output is absent; kernel version not verified.'],
        evidence_ids=['U03','U09','U46','U59','U72','U78'])


def test_handover_preserves_full_source_and_marks_missing_pastes():
    case=demo.load_case()
    source=[json.loads(l) for l in (demo.DATA/'source.jsonl').read_text().splitlines()]
    visible=[r for rows in case['evidence'].values() for r in rows]
    assert len(source)==len(visible)==79
    assert [r['text'] for r in source]==[r['text'] for r in visible]
    assert 'post-reboot uname' in case['missing_evidence']


def test_handover_evaluator_requires_retrieved_contradiction_and_resolution():
    env=demo.HandoverTools(demo.load_case());tools={t.name:t for t in env.build()}
    for group in env.case['evidence']:tools['read_evidence'].invoke({'group':group})
    r=report()
    assert demo.grade(r,env.seen,env.events)['passed']
    assert not demo.grade(r,env.seen-{'U59'},env.events)['passed']
    r['successful_remedy']='Reinstall Ubuntu'
    assert not demo.grade(r,env.seen,env.events)['passed']
    r=report();r['unknowns']=[]
    assert not demo.grade(r,env.seen,env.events)['passed']


def test_handover_report_is_a_tool_and_executes_no_command():
    env=demo.HandoverTools(demo.load_case());tools={t.name:t for t in env.build()}
    assert set(tools)=={'read_ticket','read_evidence','submit_report'}
    tools['read_ticket'].invoke({})
    assert env.case['id'] in env.seen
    result=json.loads(tools['submit_report'].invoke(report()))
    assert result['changes_executed'] is False
    assert env.report==report()


def test_handover_normalizes_prose_lists_without_changing_meaning():
    env=demo.HandoverTools(demo.load_case());tool={t.name:t for t in env.build()}['submit_report']
    payload=report()
    for field in ('contradictions','attempted_actions','unknowns'):
        payload[field]=' '.join(payload[field])
    tool.invoke(payload)
    for field in ('contradictions','attempted_actions','unknowns'):
        assert env.report[field]==[payload[field]]
    assert env.report['evidence_ids']==payload['evidence_ids']


def test_missing_kernel_verification_in_outcome_counts_as_acknowledged():
    env=demo.HandoverTools(demo.load_case());tools={t.name:t for t in env.build()}
    for group in env.case['evidence']:tools['read_evidence'].invoke({'group':group})
    r=report();r['unknowns']=['Paste contents are unavailable.']
    r['outcome']='Customer reported success, but no post-reboot uname output verifies the running version.'
    assert demo.grade(r,env.seen,env.events)['passed']
    r['outcome']='Customer reported success.'
    assert not demo.grade(r,env.seen,env.events)['passed']


def test_super_vl_profile_and_prices_are_separate_from_nano_judge():
    settings=core.load_settings(core.ROOT/'configs/model-profiles/nemotron-super-vl-gpt-sol-nano-judge.toml',
        core.ROOT/'configs/routing/task-classifier.toml',savings.PRICING)
    assert settings.efficient.model=='nvidia/nvidia/nemotron-3.5-super-vl'
    assert settings.judge.model=='nvidia/nvidia/Nemotron-3-Nano-30B-A3B'
    assert settings.efficient.input_per_million==.25
    assert settings.efficient.output_per_million==.65
    assert settings.efficient.cached_input_per_million==.10
    assert settings.efficient.cache_write_per_million==.25
    assert settings.judge.input_per_million==.05
    assert settings.judge.output_per_million==.20
    catalog=savings.prices(settings)
    assert catalog[settings.efficient.model]['output_per_million']==.65
    assert catalog[settings.judge.model]['output_per_million']==.20
    usage=dict(input_tokens=1000,output_tokens=100,input_token_details={'cache_read':300,'cache_creation':200})
    assert core.usage_cost(usage,settings.efficient)==pytest.approx(.00027)


def test_super_vl_executor_and_judge_share_model_specific_rates():
    settings=core.load_settings(core.ROOT/'configs/model-profiles/nemotron-super-vl-gpt-sol.toml',
        core.ROOT/'configs/routing/task-classifier.toml',savings.PRICING)
    assert settings.efficient.model==settings.judge.model=='nvidia/nvidia/nemotron-3.5-super-vl'
    for endpoint in (settings.efficient,settings.judge):
        assert core.usage_cost(dict(input_tokens=1000000,output_tokens=1000000),endpoint)==pytest.approx(.90)


def test_unknown_efficient_model_cannot_inherit_nano_prices():
    catalog=savings.prices(None)
    result=core.price_demo_results([dict(mode='live',calls=[dict(model='new-unknown-model',
        usage=dict(input_tokens=100,output_tokens=100))])],catalog)[0]
    assert not result['cost_complete'] and result['cost_usd'] is None


def test_comparison_freezes_prices_for_every_attempt(monkeypatch,tmp_path):
    import asyncio
    settings=core.load_settings(core.ROOT/'configs/model-profiles/nemotron-super-vl-gpt-sol.toml',
        core.ROOT/'configs/routing/task-classifier.toml',savings.PRICING)
    settings.mode='live'
    monkeypatch.setattr(settings,'validate',lambda:None)
    original=savings.prices(settings)
    price_reads=[]
    def read_prices(_):
        price_reads.append(True)
        return original if len(price_reads)==1 else {}
    monkeypatch.setattr(savings,'prices',read_prices)
    async def fake_run(arm,settings,**kwargs):
        return dict(mode='live',arm=arm,passed=True,checks={},elapsed_seconds=0,
            calls=[dict(role='efficient',model=settings.efficient.model,status='ok',
                        usage=dict(input_tokens=1000,output_tokens=100))])
    monkeypatch.setattr(demo.ubuntu,'run_case',fake_run)
    snapshots=[]
    def fake_save(results,settings,phase,**kwargs):
        snapshots.append(kwargs['model_prices'])
        return tmp_path/'result.json'
    monkeypatch.setattr(demo,'save',fake_save)
    rows,_=asyncio.run(demo.compare(settings))
    assert len(price_reads)==1
    assert all(r['cost_complete'] for r in rows)
    assert all(r['cost_usd']==pytest.approx(.000315) for r in rows)
    assert all(p==original for p in snapshots)
