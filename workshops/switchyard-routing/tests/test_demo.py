"""No external inference calls. HTTP integration tests bind to loopback only."""
import asyncio
import copy
import json
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import incident_demo as d


def test_cache_and_reasoning_accounting():
    ep=d.Endpoint('m','https://example.invalid/v1','KEY', input_per_million=10,
         output_per_million=30,cached_input_per_million=1,cache_write_per_million=12)
    usage=dict(input_tokens=1000,output_tokens=100,input_token_details={'cache_read':300,'cache_creation':100},
               output_token_details={'reasoning':80})
    assert d.usage_cost(usage,ep)==pytest.approx((600*10+300+100*12+100*30)/1e6)
    ep.cached_input_per_million=None
    assert d.usage_cost(usage,ep) is None
    assert d.usage_cost(None,ep) is None
    assert d.usage_cost({'input_tokens':2},ep) is None
    assert d.usage_cost({'input_tokens':2,'output_tokens':1,'input_token_details':{'cache_read':4}},ep) is None


def test_judge_guidance_preserves_original_capability_rubric_and_messages():
    messages=[d.SystemMessage(content='Original capability rubric'),d.AIMessage(content='Observed evidence')]
    prepared=d.judge_messages(messages)
    assert prepared[0].content.startswith('Original capability rubric\n\n')
    assert 'SUP-1, SUP-2, SUP-3, SUP-4, SUP-5 -> supported' in prepared[0].content
    assert 'none -> unmatched' in prepared[0].content
    assert messages[0].content=='Original capability rubric'
    assert prepared[1] is messages[1]
    assert isinstance(d.judge_messages(messages[1:])[0],d.SystemMessage)


def test_grade_requires_retrieved_decisive_evidence():
    _,_,rubrics=d.load_data(); rubric=rubrics['INC-004']
    report=dict(cause_code=rubric['cause_code'],action_code=rubric['action_code'],evidence_ids=rubric['required_evidence'],
       runbook_id=rubric['runbook_id'],root_cause='clock skew',resolution='synchronize time',verification_steps=['check offset','test token'])
    seen=set(rubric['required_evidence']+[rubric['runbook_id']])
    tools=['read_ticket','search_logs','inspect_metrics','read_runbook']
    assert d.grade(report,rubric,seen,tools)['passed']
    assert not d.grade(report,rubric,seen-{'INC-004-M1'},tools)['passed']
    report['cause_code']='expired_credential'
    assert not d.grade(report,rubric,seen,tools)['passed']


def test_rehearsal_real_switchyard_and_all_cases():
    async def run():
        settings=d.Settings(show_progress=False)
        # Every fixture can be retrieved, graded, and run through real stage routing.
        for case in d.load_data()[0]:
            r=await d.run_case(case['id'],'switchyard',settings)
            assert r['passed'], r
            assert r['routing_trace'] and len(r['calls'])==6
            assert r['cost_usd'] is None and not r['cost_complete']
        rows=await d.run_comparison(['INC-001','INC-004'],settings)
        assert d.summarize(rows).total_cost_usd.isna().all()
        assert d.summarize(rows).savings_vs_frontier.isna().all()
    asyncio.run(run())


def test_call_limit_stops_instead_of_returning_success():
    r=asyncio.run(d.run_case('INC-001','efficient_only',d.Settings(max_calls_per_task=2)))
    assert not r['passed'] and len(r['calls'])==2 and r['error_type']=='CallLimitError'


def test_paid_calls_require_explicit_live_toggle():
    with pytest.raises(ValueError,match='allow_paid_calls'):
        asyncio.run(d.run_case('INC-001','frontier_only',d.Settings(mode='live')))


def test_reference_profile_shared_client_and_price_reuse(tmp_path, monkeypatch):
    monkeypatch.setenv('NVIDIA_BASE_URL','https://example.invalid/v1')
    monkeypatch.setenv('NVIDIA_API_KEY','not-exported')
    prices=tmp_path/'prices.toml'
    prices.write_text('''pricing_version = 1
[[rates]]
client = "nvidia"
model_id = "nvidia/nvidia/nemotron-3.5-lightning"
input_per_million = 0.2
output_per_million = 0.5
''')
    settings=d.load_settings(d.ROOT/'configs/model-profiles/nemotron-lightning-ultra.toml',
       d.ROOT/'configs/routing/task-classifier.toml',prices,mode='live',allow_paid_calls=True)
    settings.validate()
    assert settings.efficient == settings.judge
    assert settings.efficient.input_per_million == .2
    assert settings.frontier.input_per_million is None
    assert {getattr(settings,k).key_env for k in ('efficient','frontier','judge')} == {'NVIDIA_API_KEY'}
    assert settings.routing=='task_classifier' and settings.recent_window==3
    assert len(settings.config_sources)==3
    assert 'not-exported' not in json.dumps(d.asdict(settings))


def test_profile_alternative_and_no_env_needed_for_rehearsal(monkeypatch):
    monkeypatch.delenv('NVIDIA_BASE_URL',raising=False)
    settings=d.load_settings(d.ROOT/'configs/model-profiles/nemotron-nano-gpt-sol.toml',
       d.ROOT/'configs/routing/stage.toml')
    settings.validate()
    assert settings.routing=='stage'
    assert settings.efficient.model==settings.judge.model
    assert settings.efficient.model
    assert settings.frontier.model and settings.frontier.model!=settings.efficient.model
    assert settings.frontier.key_env=='NVIDIA_API_KEY'
    with pytest.raises(ValueError,match='NVIDIA_BASE_URL'):
        d.load_settings(d.ROOT/'configs/model-profiles/nemotron-nano-gpt-sol.toml',
          d.ROOT/'configs/routing/stage.toml',mode='live')


def test_unknown_strategy_and_native_format_fail_explicitly(tmp_path):
    profile=d.ROOT/'configs/model-profiles/nemotron-lightning-ultra.toml'
    strategy=tmp_path/'strategy.toml'
    original=(d.ROOT/'configs/routing/task-classifier.toml').read_text()
    strategy.write_text(original.replace('mode = "capability"','mode = "escalation"'))
    with pytest.raises(ValueError,match='not escalation'):
        d.load_settings(profile,strategy)
    strategy.write_text(original.replace('base_threshold','typo_threshold'))
    with pytest.raises(ValueError,match='Unknown fields'):
        d.load_settings(profile,strategy)
    unsupported=tmp_path/'profile.toml'
    unsupported.write_text(profile.read_text().replace('openai_chat','anthropic_messages'))
    with pytest.raises(ValueError,match='openai_chat'):
        d.load_settings(unsupported,d.ROOT/'configs/routing/stage.toml')


def test_toml_stage_picker_reaches_real_switchyard(tmp_path):
    strategy=tmp_path/'strategy.toml'
    strategy.write_text((d.ROOT/'configs/routing/stage.toml').read_text().replace('efficient_first','capable_first'))
    settings=d.load_settings(d.ROOT/'configs/model-profiles/nemotron-lightning-ultra.toml',strategy)
    r=asyncio.run(d.run_case('INC-001','switchyard',settings))
    assert r['passed']
    assert {x['selected_model'] for x in r['routing_trace']}=={'frontier'}


def test_summary_counts_failures_and_requires_matched_tasks():
    def row(cid,arm,cost,passed):
        return dict(case_id=cid,arm=arm,cost_usd=cost,passed=passed,cost_complete=True,
                    mode='live',elapsed_seconds=2,calls=[{'role':'frontier'}])
    rows=[row('1','frontier_only',1,True),row('2','frontier_only',1,False),
          row('1','switchyard',.2,True),row('2','switchyard',.3,False)]
    table=d.summarize(rows).set_index('arm')
    assert table.loc['Switchyard','cost_per_pass_usd']==.5
    assert table.loc['Switchyard','savings_vs_frontier']==.75
    assert d.summarize(rows[:-1]).set_index('arm').loc['Switchyard','savings_vs_frontier'] is None or \
           d.pd.isna(d.summarize(rows[:-1]).set_index('arm').loc['Switchyard','savings_vs_frontier'])
    rows[0]['mode']='rehearsal'
    with pytest.raises(ValueError,match='combine'):
        d.summarize(rows)


@pytest.fixture
def fake_endpoint(monkeypatch, tmp_path):
    monkeypatch.setattr(d, 'JUDGE_LOG_DIRECTORY', tmp_path / 'judge-logs')
    requests=[]
    state={'probability':.9,'error_model':None,'missing_usage':False,
           'judge_finish_reason':'stop','invalid_verdict':False,'judge_content':None}
    _,_,rubrics=d.load_data()
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args):
            pass
        def do_POST(self):
            payload=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            requests.append(payload)
            if payload['model']==state['error_model']:
                self.send_response(429); self.send_header('Content-Type','application/json');self.end_headers()
                self.wfile.write(b'{"error":{"message":"mock failure","type":"rate_limit"}}')
                return
            if payload.get('response_format'):
                schema=payload['response_format']['json_schema']['schema']
                assert 'p_solve' in schema['properties']
                content=json.dumps(dict(crux='Synthetic wiring test',primary_rule='SUP-99' if state['invalid_verdict'] else 'SUP-2',
                    capability_boundary='supported',p_solve=state['probability']))
                if state['judge_content'] is not None:
                    content=state['judge_content']
                message={'role':'assistant','content':content}
            else:
                text=json.dumps(payload['messages'])
                import re
                cid=re.search(r'INC-\d{3}',text)[0]
                rubric=rubrics[cid]
                index=sum(m['role']=='tool' for m in payload['messages'])
                report=dict(cause_code=rubric['cause_code'],action_code=rubric['action_code'],
                    root_cause=rubric['root_cause'],evidence_ids=rubric['required_evidence'],runbook_id=rubric['runbook_id'],
                    resolution=rubric['resolution'],verification_steps=['check service errors','check trusted metrics'])
                script=[('read_ticket',{}),('search_logs',{'query':''}),('inspect_metrics',{}),
                        ('search_runbooks',{'query':''}),('read_runbook',{'runbook_id':rubric['runbook_id']}),('submit_report',report)]
                name,args=script[index]
                message=dict(role='assistant',content=None,tool_calls=[dict(id=f'tool-{index}',type='function',
                    function=dict(name=name,arguments=json.dumps(args)))])
            response=dict(id=f'chatcmpl-{len(requests)}',object='chat.completion',created=1,model=payload['model'],
              choices=[dict(index=0,message=message,finish_reason='tool_calls' if 'tool_calls' in message else state['judge_finish_reason'])])
            if not state['missing_usage']:
                response['usage']=dict(prompt_tokens=100,completion_tokens=20,total_tokens=120,
                    prompt_tokens_details={'cached_tokens':10},completion_tokens_details={'reasoning_tokens':5})
            self.send_response(200);self.send_header('Content-Type','application/json');self.end_headers()
            self.wfile.write(json.dumps(response).encode())
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    monkeypatch.setenv('MOCK_KEY','not-a-real-secret')
    def ep(model):
        return d.Endpoint(model,f'http://127.0.0.1:{server.server_port}/v1','MOCK_KEY',1,2,.1,
                           price_source='mock fixture',price_date='2026-10-09')
    settings=d.Settings(mode='live',allow_paid_calls=True,efficient=ep('mock-efficient'),frontier=ep('mock-frontier'),
          judge=ep('mock-judge'),show_progress=False,task_timeout_seconds=30)
    yield settings,requests,state
    server.shutdown();server.server_close();thread.join()


@pytest.mark.parametrize('probability,expected',[(.99,'efficient'),(.01,'frontier')])
def test_live_client_with_real_classifier_and_accounting(fake_endpoint,probability,expected):
    settings,requests,state=fake_endpoint;state['probability']=probability
    r=asyncio.run(d.run_case('INC-004','switchyard',settings))
    assert r['passed'], r
    assert len(r['calls'])==12, r['calls']
    assert sum(c['role']=='judge' for c in r['calls'])==6
    judge_requests=[q for q in requests if q.get('response_format')]
    executor_requests=[q for q in requests if not q.get('response_format')]
    assert all(any(d.JUDGE_OUTPUT_GUIDANCE in m.get('content','') for m in q['messages']) for q in judge_requests)
    assert all('Verdict formatting reminder:' not in json.dumps(q['messages']) for q in executor_requests)
    assert {x['selected_model'] for x in r['routing_trace']}=={expected}
    assert r['cost_complete'] and r['cost_usd']==pytest.approx(12*(90+1+40)/1e6)
    assert all((q.get('max_tokens') or q.get('max_completion_tokens'))<=settings.max_output_tokens for q in requests)
    assert all('answer key' not in json.dumps(q).lower() for q in requests)
    assert 'clock offset=+3600' not in json.dumps(requests[0])  # judge sees ticket, not hidden answers


def test_missing_usage_cannot_claim_savings(fake_endpoint):
    settings,requests,state=fake_endpoint;state['missing_usage']=True
    r=asyncio.run(d.run_case('INC-001','frontier_only',settings))
    assert r['passed'] and not r['cost_complete'] and r['cost_usd'] is None


def test_provider_failure_not_retried_or_priced_zero(fake_endpoint):
    settings,requests,state=fake_endpoint;state['error_model']='mock-frontier'
    r=asyncio.run(d.run_case('INC-001','frontier_only',settings))
    assert not r['passed'] and r['error_type'].endswith('RateLimitError')
    assert len(requests)==1 and r['cost_usd'] is None
    assert 'not-a-real-secret' not in json.dumps(r)


def test_wrapped_router_failure_displays_underlying_call_error(fake_endpoint, capsys, monkeypatch):
    settings,requests,state=fake_endpoint
    state['probability']=.01
    state['error_model']='mock-frontier'
    r=asyncio.run(d.run_case('INC-001','switchyard',settings))
    assert r['error_type']=='LibsyError'
    call_error=r['calls'][-1]['error_type']
    assert call_error.endswith('RateLimitError')
    monkeypatch.setattr(d,'display',lambda *args: None)
    d.show_case(r)
    output=capsys.readouterr().out
    assert f'Failed frontier call (mock-frontier): {call_error}' in output
    assert 'separate from the run failure' in output
    assert 'not-a-real-secret' not in output


@pytest.mark.parametrize('probability,expected',[(.99,'efficient'),(.01,'frontier')])
def test_selected_profile_routes_both_tiers(fake_endpoint, monkeypatch, probability, expected):
    base,requests,state=fake_endpoint
    state['probability']=probability
    monkeypatch.setenv('NVIDIA_BASE_URL',base.judge.base_url)
    monkeypatch.setenv('NVIDIA_API_KEY','not-a-real-secret')
    settings=d.load_settings(d.ROOT/'configs/model-profiles/nemotron-nano-gpt-sol.toml',
        d.ROOT/'configs/routing/task-classifier.toml', mode='live', allow_paid_calls=True)
    r=asyncio.run(d.run_case('INC-004','switchyard',settings))
    assert r['passed'] and r['error_type'] is None
    assert {route['selected_model'] for route in r['routing_trace']}=={expected}
    assert {q['model'] for q in requests if q.get('response_format')}=={settings.judge.model}
    assert all(q.get('chat_template_kwargs')=={'enable_thinking':False}
               for q in requests if q.get('response_format'))
    assert all('chat_template_kwargs' not in q for q in requests if not q.get('response_format'))
    assert all(q.get('temperature')==0 for q in requests
               if q['model'] in {settings.efficient.model,settings.judge.model})
    assert all('temperature' not in q for q in requests if q['model']==settings.frontier.model)
    assert {q['model'] for q in requests if not q.get('response_format')}=={getattr(settings,expected).model}
    assert all(c['classifier_verdict_valid'] for c in r['calls'] if c['role']=='judge')
    assert all((q.get('max_tokens') or q.get('max_completion_tokens'))==settings.max_output_tokens for q in requests)


def test_profile_provider_options_are_validated_and_isolated(tmp_path):
    original=(d.ROOT/'configs/model-profiles/nemotron-nano-gpt-sol.toml').read_text()
    path=tmp_path/'profile.toml'
    path.write_text(original.split('[roles.classifier.extra_body.chat_template_kwargs]')[0]
                    + '\nextra_body = "invalid"\n')
    with pytest.raises(ValueError,match='extra_body must be a table'):
        d.load_settings(path,d.ROOT/'configs/routing/task-classifier.toml')
    settings=d.load_settings(d.ROOT/'configs/model-profiles/nemotron-nano-gpt-sol.toml',
                             d.ROOT/'configs/routing/task-classifier.toml')
    assert settings.judge.extra_body=={'chat_template_kwargs':{'enable_thinking':False}}
    assert settings.efficient.extra_body==settings.frontier.extra_body=={}
    settings.judge.extra_body['chat_template_kwargs']['enable_thinking']=True
    again=d.load_settings(d.ROOT/'configs/model-profiles/nemotron-nano-gpt-sol.toml',
                          d.ROOT/'configs/routing/task-classifier.toml')
    assert again.judge.extra_body['chat_template_kwargs']['enable_thinking'] is False


def test_sampling_options_are_optional_and_validated(fake_endpoint):
    settings,requests,state=fake_endpoint
    settings.judge.temperature=0
    settings.judge.seed=41
    result=asyncio.run(d.run_case('INC-004','switchyard',settings))
    assert result['passed']
    assert all(q.get('temperature')==0 and q.get('seed')==41 for q in requests if q.get('response_format'))
    assert all('temperature' not in q and 'seed' not in q for q in requests if not q.get('response_format'))
    settings.judge.temperature=float('nan')
    with pytest.raises(ValueError,match='temperature'):
        settings.validate()
    settings.judge.temperature=0
    settings.judge.seed=True
    with pytest.raises(ValueError,match='seed must be an integer'):
        settings.validate()


def test_repeated_cost_summary_counts_failed_attempts_and_matches_baseline(monkeypatch):
    def result(arm,repeat,cost,passed):
        role='frontier' if arm=='frontier_only' else 'efficient'
        return dict(arm=arm,repeat=repeat,case_id='INC-005',mode='live',passed=passed,
            elapsed_seconds=1,cost_complete=True,cost_usd=cost,pricing_basis='Illustrative',
            calls=[dict(role=role,model=role,status='ok',cost_usd=cost)])
    results=[result('frontier_only',1,1,True),result('frontier_only',2,1,True),
             result('switchyard',1,.4,False),result('switchyard',2,.6,True)]
    summary=d.summarize(results).set_index('arm')
    routed=summary.loc['Switchyard']
    assert routed['total_cost_usd']==1
    assert routed['mean_cost_usd']==.5 and routed['min_cost_usd']==.4 and routed['max_cost_usd']==.6
    assert routed['cost_per_pass_usd']==1 and routed['pass_rate']==.5
    assert routed['savings_vs_frontier']==.5
    captured=[]
    monkeypatch.setattr(d,'display',captured.append)
    settings=d.Settings(efficient=d.Endpoint('efficient','',''),frontier=d.Endpoint('frontier','',''))
    d.show_demo_comparison(results,settings)
    row=captured[0].iloc[1]
    assert row['USD per pass']=='$1.00000' and row['Mean USD per attempt']=='$0.50000'
    assert row['Savings vs capable']=='50.0%'
    assert d.pd.isna(d.summarize(results[:-1]).set_index('arm').loc['Switchyard','savings_vs_frontier'])


class RecordingLangSmithClient(d.LangSmithClient):
    """Use the real SDK run tree with in-memory writes, never a LangSmith server."""
    def __init__(self):
        super().__init__(api_url='http://127.0.0.1:1',api_key='fake-langsmith-key',
                         auto_batch_tracing=False,info={'instance_flags':{}})
        self.created=[]
        self.updated=[]
        self.flushed=0

    def create_run(self, name, inputs, run_type, **kwargs):
        self.created.append(dict(name=name,inputs=inputs,run_type=run_type,**kwargs))

    def update_run(self, run_id, **kwargs):
        self.updated.append(dict(id=run_id,**kwargs))

    def flush(self, *args, **kwargs):
        self.flushed+=1

    def get_run_url(self, *, run, **kwargs):
        return f'https://smith.example.test/trace/{run.id}'


@pytest.mark.parametrize('issue',[None,'truncated'])
def test_langsmith_captures_nested_judge_executor_tools_and_final_checks(fake_endpoint,monkeypatch,issue):
    settings,requests,state=fake_endpoint
    settings.enable_langsmith=True
    settings.langsmith_project='test-incident-traces'
    if issue=='truncated':state['judge_finish_reason']='length'
    client=RecordingLangSmithClient()
    monkeypatch.setattr(d,'LangSmithClient',lambda **kwargs:client)
    monkeypatch.setenv('LANGSMITH_API_KEY','fake-langsmith-key')
    r=asyncio.run(d.run_case('INC-004','switchyard',settings,
                           trace_metadata={'comparison_id':'comparison-test','repeat':2}))
    assert r['passed']
    assert r['langsmith_project']=='test-incident-traces'
    assert r['langsmith_trace_url'].endswith(r['langsmith_run_id'])
    assert client.flushed==1
    root=next(x for x in client.created if str(x['id'])==r['langsmith_run_id'])
    assert root['extra']['metadata']['repeat']==2
    assert root['extra']['metadata']['comparison_id']=='comparison-test'
    assert root['session_name']=='test-incident-traces'
    models=[x for x in client.created if x['run_type']=='llm' and x['name'].startswith(('judge:','efficient:','frontier:'))]
    assert len(models)==len(r['calls'])
    assert any(x['name'].startswith('judge:') for x in models)
    assert any(x['run_type']=='tool' and x['name']=='inspect_metrics' for x in client.created)
    # Every physical model call, including Rust-invoked judges, shares the root trace.
    assert all(str(x['trace_id'])==r['langsmith_run_id'] for x in models)
    end=next(x for x in client.updated if str(x['id'])==r['langsmith_run_id'])
    assert end['outputs']['passed'] is True and all(end['outputs']['checks'].values())
    assert len(end['outputs']['calls'])==len(r['calls'])
    if issue:
        assert any(x.get('error') for x in client.updated if x['id']!=root['id'])
        assert any(c.get('error_type')=='LengthFinishReasonError' for c in end['outputs']['calls'])
    assert 'not-a-real-secret' not in json.dumps(client.created+client.updated,default=str)


def test_langsmith_off_overrides_ambient_tracing_and_missing_key_is_explicit(monkeypatch):
    monkeypatch.setenv('LANGSMITH_TRACING','true')
    monkeypatch.delenv('LANGSMITH_API_KEY',raising=False)
    monkeypatch.delenv('LANGCHAIN_API_KEY',raising=False)
    def forbidden_client():raise AssertionError('Disabled tracing constructed a client')
    monkeypatch.setattr(d,'LangSmithClient',forbidden_client)
    settings=d.Settings(show_progress=False)
    result=asyncio.run(d.run_case('INC-004','switchyard',settings))
    assert result['passed'] and 'langsmith_run_id' not in result
    settings.enable_langsmith=True
    with pytest.raises(ValueError,match='LANGSMITH_API_KEY'):
        asyncio.run(d.run_case('INC-004','switchyard',settings))


@pytest.mark.parametrize('issue',['truncated','invalid'])
def test_failed_judge_falls_back_and_warns_even_when_incident_passes(fake_endpoint, capsys, monkeypatch, issue):
    settings,requests,state=fake_endpoint
    state['judge_finish_reason']='length' if issue=='truncated' else 'stop'
    state['invalid_verdict']=issue=='invalid'
    r=asyncio.run(d.run_case('INC-004','switchyard',settings))
    assert r['passed'] and r['error_type'] is None
    assert {route['selected_model'] for route in r['routing_trace']}=={'frontier'}
    judge=[c for c in r['calls'] if c['role']=='judge']
    if issue=='truncated':
        assert all(c['error_type']=='LengthFinishReasonError' and c['output_tokens']==20 for c in judge)
        assert not r['cost_complete'] and r['known_partial_cost_usd']>0
    else:
        assert all(c['status']=='ok' and c['classifier_verdict_valid'] is False for c in judge)
    monkeypatch.setattr(d,'display',lambda *args: None)
    d.show_case(r)
    output=capsys.readouterr().out
    assert 'Classifier warning:' in output and 'Router fallback: 6 turn(s)' in output
    records=[json.loads(line) for line in Path(r['judge_log_path']).read_text().splitlines()]
    assert len(records)==len(judge)
    assert all(record['classifier_response'] for record in records)
    if issue=='truncated':
        assert all(record['finish_reason']=='length' and 'truncated' in record['classifier_issue'] for record in records)
    else:
        assert all('primary_rule/capability_boundary' in record['classifier_issue'] for record in records)


def test_judge_log_redacts_keys_and_excludes_headers(fake_endpoint):
    settings,requests,state=fake_endpoint
    state['judge_content']='Unusable verdict echoing not-a-real-secret and Bearer confidential-token'
    r=asyncio.run(d.run_case('INC-004','switchyard',settings))
    text=Path(r['judge_log_path']).read_text()
    assert 'not-a-real-secret' not in text and 'confidential-token' not in text
    assert '[REDACTED]' in text and 'Response is not a JSON verdict.' in text
    assert 'authorization' not in text.lower() and 'headers' not in text.lower()
    assert all('not-a-real-secret' not in c.get('classifier_response','') for c in r['calls'])


def test_audience_view_shows_router_failures_without_raw_diagnostics(fake_endpoint, monkeypatch, capsys):
    settings,requests,state=fake_endpoint
    state['judge_finish_reason']='length'
    r=asyncio.run(d.run_case('INC-004','switchyard',settings))
    captured=[]
    monkeypatch.setattr(d,'display',captured.append)
    d.show_demo_case(r,settings)
    d.show_demo_comparison([r],settings)
    text=capsys.readouterr().out
    assert '6 step(s) used the capable model' in text
    assert 'no dollar savings are claimed' in text
    assert 'classifier_response' not in text and 'Judge call' not in text
    assert 'Checks passed' in captured[0].data
    table=captured[-1]
    assert table.iloc[0]['Capable steps']==6 and table.iloc[0]['Router issues']==6
    assert 'mock-frontier' in table.iloc[0]['Approach'] or table.iloc[0]['Approach']=='Automatic routing'


def test_scenario_prices_include_judge_and_preserve_original_results(fake_endpoint, monkeypatch):
    settings,requests,state=fake_endpoint
    r=asyncio.run(d.run_case('INC-004','switchyard',settings))
    original=copy.deepcopy(r)
    prices={model:{'input_per_million':1,'output_per_million':2,'cached_input_per_million':.1}
            for model in ('mock-efficient','mock-frontier','mock-judge')}
    priced=d.price_demo_results([r],prices)
    assert r==original
    assert priced[0]['cost_usd']==pytest.approx(12*(90+1+40)/1e6)
    assert priced[0]['pricing_basis'].startswith('Illustrative')
    captured=[]
    monkeypatch.setattr(d,'display',captured.append)
    d.show_demo_comparison(priced,settings)
    assert captured[-1].iloc[0]['Illustrative USD']=='$0.00157'
    assert 'Efficient steps' in captured[-1].columns
    del prices['mock-judge']
    assert not d.price_demo_results([r],prices)[0]['cost_complete']
    for call in r['calls']:
        call.pop('usage',None)
    assert d.price_demo_results([r],prices)[0]['cost_usd'] is None
    with pytest.raises(ValueError,match='nonnegative'):
        d.price_demo_results([original],{'mock-judge':{'input_per_million':-1}})


def test_scenario_prices_failed_judge_with_usage_but_preserves_unknown_cost(monkeypatch, capsys):
    result=dict(arm='switchyard',case_id='INC-005',mode='live',passed=True,
        elapsed_seconds=1,calls=[dict(call=7,role='judge',model='nano',status='error',
        error_type='LengthFinishReasonError',classifier_verdict_valid=False,
        usage=dict(input_tokens=1177,output_tokens=4000))])
    original=copy.deepcopy(result)
    prices={'nano':dict(input_per_million=.05,output_per_million=.20)}
    priced=d.price_demo_results([result],prices)
    assert result==original
    assert priced[0]['cost_complete']
    assert priced[0]['cost_usd']==pytest.approx(.00085885)
    captured=[]
    monkeypatch.setattr(d,'display',captured.append)
    settings=d.Settings(efficient=d.Endpoint('nano','',''),frontier=d.Endpoint('capable','',''))
    d.show_demo_comparison(priced,settings)
    assert captured[0].iloc[0]['Router issues']==1
    assert captured[0].iloc[0]['Illustrative USD']=='$0.00086'
    assert 'Failed requests with returned usage are included' in capsys.readouterr().out
    result['calls'][0]['usage']=None
    assert not d.price_demo_results([result],prices)[0]['cost_complete']
    assert d.price_demo_results([result],prices)[0]['cost_usd'] is None
    assert not d.price_demo_results([original],{})[0]['cost_complete']


def test_role_table_distinguishes_routing_judge_and_final_checker():
    efficient=d.Endpoint('provider/nano','https://example.invalid','KEY')
    capable=d.Endpoint('provider/capable','https://example.invalid','KEY')
    settings=d.Settings(mode='live',efficient=efficient,frontier=capable,judge=efficient)
    table=d.demo_role_table(settings).set_index('Role')
    assert table.loc['Routing judge','Model / checker']=='nano'
    assert table.loc['Efficient executor','Model / checker']=='nano'
    assert table.loc['Final checker','Model / checker']=='Python rules (no LLM)'
    settings.routing='stage'
    assert d.demo_role_table(settings).set_index('Role').loc['Routing judge','Model / checker']=='Not used in this mode'


def test_audience_comparison_labels_follow_recorded_models_not_changed_settings(monkeypatch):
    r=dict(arm='efficient_only',case_id='INC-004',mode='live',passed=True,cost_complete=False,
           cost_usd=None,elapsed_seconds=1,calls=[dict(role='efficient',model='provider/old-nano',status='ok')])
    settings=d.Settings(efficient=d.Endpoint('provider/new-model','',''),frontier=d.Endpoint('provider/capable','',''))
    captured=[]
    monkeypatch.setattr(d,'display',captured.append)
    d.show_demo_comparison([r],settings)
    assert captured[0].iloc[0]['Approach']=='old-nano only'


def test_audience_comparison_explains_failed_incident_checks(monkeypatch,capsys):
    r=dict(arm='efficient_only',case_id='INC-004',mode='live',passed=False,cost_complete=False,
        cost_usd=None,elapsed_seconds=1,calls=[dict(role='efficient',model='provider/nano',status='ok')],
        checks={'correct_cause':False,'report_complete':True})
    settings=d.Settings(efficient=d.Endpoint('provider/nano','',''),frontier=d.Endpoint('provider/capable','',''))
    monkeypatch.setattr(d,'display',lambda value:None)
    d.show_demo_comparison([r],settings)
    assert 'Needs review — nano only · INC-004: expected cause' in capsys.readouterr().out
