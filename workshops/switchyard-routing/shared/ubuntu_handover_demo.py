"""One agentic support task: compile an evidence-backed historical handover."""
from __future__ import annotations

import asyncio
import hashlib
import json
import random
from copy import deepcopy
from dataclasses import asdict
from datetime import datetime, timezone

from langchain_core.tools import tool
import incident_demo as core
import ubuntu_demo as ubuntu
import ubuntu_savings_demo as savings

DATA = ubuntu.DATA / 'handover'
PROMPT = '''Prepare a factual support handover from one historical Ubuntu conversation.
Use the read-only tools to inspect all available sections. Do not troubleshoot a live
machine, run commands, retrieve external links or invent missing paste contents.
The completed conversation, including its resolution, is evidence for this summarization
task. Identify contradictions between earlier and later statements, actions attempted,
the reported successful remedy, and what the transcript does not verify.
Finish by CALLING submit_report. A plain text answer does not complete the task.
Keep the report concise, about 220 words. Cite exact retrieved evidence IDs.
Treat old helper advice as historical evidence, not present-day installation guidance.'''
CONTRACT = '''Compile a handover for the next support engineer. All 79 transcript messages
are available through read_ticket and read_evidence. Read sections environment,
upgrade_history, remediation and confirmation. No external state or live repair is needed.
Use submit_report to record the environment, conflicting statements, attempted actions,
successful remedy, reported outcome, unresolved unknowns, and supporting evidence IDs.
The evaluator checks source-backed facts and citations, not an exact prose answer.
Distinguish a helper's predicted post-reboot kernel version from an observed version.
Do not claim a command was run in this replay.'''


def load_case():
    return json.loads((DATA/'case.json').read_text())


class HandoverTools(ubuntu.SupportTools):
    def build(self):
        @tool
        def read_ticket() -> str:
            """Read the historical opening problem and section index."""
            self.seen.add(self.case['id'])
            return self.record('read_ticket',{},dict(id=self.case['id'],summary=self.case['summary'],
                sections=list(self.case['evidence']),missing_evidence=self.case['missing_evidence']))

        @tool
        def read_evidence(group: str) -> str:
            """Read one section: environment, upgrade_history, remediation or confirmation."""
            rows=self.case['evidence'].get(group)
            if rows is None:
                return self.record('read_evidence',{'group':group},{'error':'Unknown section'})
            self.seen.update(r['id'] for r in rows)
            return self.record('read_evidence',{'group':group},rows)

        @tool(return_direct=True)
        def submit_report(environment: str, contradictions: list[str] | str, attempted_actions: list[str] | str,
                          successful_remedy: str, outcome: str, unknowns: list[str] | str,
                          evidence_ids: list[str]) -> str:
            """Submit the historical handover. Cite IDs and distinguish reported from verified results.

            Text fields contradictions, attempted_actions and unknowns accept prose or
            lists of strings. They are stored as lists without changing their meaning.
            """
            as_list=lambda value: [value] if isinstance(value,str) else value
            self.report=dict(environment=environment,contradictions=as_list(contradictions),
                attempted_actions=as_list(attempted_actions),successful_remedy=successful_remedy,
                outcome=outcome,unknowns=as_list(unknowns),evidence_ids=evidence_ids)
            return self.record('submit_report',{},dict(status='handover_recorded',changes_executed=False))
        return [read_ticket,read_evidence,submit_report]


def grade(report,seen,events):
    r=report or {};refs=set(r.get('evidence_ids',[]))
    environment=r.get('environment','').lower()
    contradictions=' '.join(r.get('contradictions',[])).lower()
    # Acknowledging missing verification in the outcome is semantically valid too.
    unknowns=(' '.join(r.get('unknowns',[]))+' '+r.get('outcome','')).lower()
    checks=dict(report_submitted=bool(report),
        all_sections={e['arguments'].get('group') for e in events if e['tool']=='read_evidence'}
            >= {'environment','upgrade_history','remediation','confirmation'},
        citations_retrieved=bool(refs) and refs<=seen,
        environment_evidence=bool(refs&{'U03','U41'}) and 'U09' in refs,
        contradictory_history_evidence={'U46','U59'}<=refs,
        remedy_and_confirmation_evidence={'U72','U78'}<=refs,
        version_mismatch='14.04' in environment and '3.11' in environment,
        interrupted_developer_upgrade='-d' in contradictions and any(w in contradictions for w in ('interrupt','ctrl','cancel','abort')),
        reports_historical_remedy='linux-generic' in r.get('successful_remedy',''),
        reported_success=any(w in r.get('outcome','').lower() for w in ('success','worked','resolved','that did it','fixed')),
        notes_missing_verification=any(w in unknowns for w in ('uname','post-reboot','after reboot','running kernel','rebooted kernel')))
    return dict(passed=all(checks.values()),checks=checks)


def save(results,settings,phase,model_prices=None,pricing_file_sha256=None):
    folder=core.ROOT/'recordings/ubuntu-handover';folder.mkdir(parents=True,exist_ok=True)
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    config=asdict(settings)
    for role in ('efficient','frontier','judge'):
        if config[role]:config[role]['extra_body']={'configured':bool(config[role]['extra_body'])}
    metadata=dict(dataset='Ubuntu Chat Logs Corpus',phase=phase,settings=config,
        interface_revision='handover-v2: prose-or-list text fields normalized to lists',
        evaluation_revision='handover-v2: missing verification may be acknowledged in outcome or unknowns',
        efficient_enable_thinking_requested=(settings.efficient.extra_body.get('chat_template_kwargs') or {}).get('enable_thinking'),
        provenance=json.loads((savings.DATA/'provenance.json').read_text()),
        task='Historical support handover; complete conversation including remedy/outcome is intentionally visible.',
        prompt=PROMPT,opening_contract=CONTRACT,
        scenario_prices=deepcopy(savings.prices(settings) if model_prices is None else model_prices),
        pricing_source=str(savings.PRICING.relative_to(core.ROOT)),
        pricing_sha256=pricing_file_sha256 or hashlib.sha256(savings.PRICING.read_bytes()).hexdigest(),
        cache_write_assumption='Super VL and Lightning cache writes assumed ordinary input pricing for each exact model. Model-specific rates are frozen in scenario_prices; see pricing_source for rate provenance.',
        files_sha256={str(p.relative_to(core.ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
            for p in [DATA/'case.json',DATA/'source.jsonl',core.Path(__file__)]},
        limitations='Selected workshop example, not an unbiased benchmark. Mechanical checks plus human review. No live repair or general reliability claim. Illustrative rates, not invoices. Public-source memorization possible.')
    # Override the inherited diagnosis-cutoff description: this is a complete-record task.
    metadata['provenance']['adaptation']='All 79 original utterances grouped into four retrieval sections. Speaker fields relabelled; message text preserved. No paste contents fabricated. Outcome is available because the task is handover, not diagnosis prediction.'
    path=folder/f'{phase}-{stamp}.json'
    path.write_text(json.dumps(dict(metadata=metadata,results=results),indent=2)+'\n')
    return path


async def compare(settings,*,repeats=1,phase='pilot'):
    settings.validate()
    if settings.mode!='live' or repeats<1 or repeats*3>settings.max_suite_tasks:
        raise ValueError('Use live mode and a repeat count within the task limit.')
    snapshot=deepcopy(settings);results=[];case=load_case()
    model_prices=deepcopy(savings.prices(snapshot))
    pricing_file_sha256=hashlib.sha256(savings.PRICING.read_bytes()).hexdigest()
    jobs=[(arm,rep+1) for rep in range(repeats) for arm in core.ARMS]
    random.Random(41).shuffle(jobs)
    for arm,repeat in jobs:
        print(f'{phase} {len(results)+1}/{len(jobs)} · {core.LABELS[arm]} · {repeat}',flush=True)
        r=await ubuntu.run_case(arm,deepcopy(snapshot),case_data=case,system_prompt=PROMPT,
            opening_instruction=f"{case['summary']}\n\n{CONTRACT}",environment_factory=HandoverTools,
            report_grader=grade,on_event=ubuntu.progress)
        r.update(conversation_id='79.2',repeat=repeat,order=len(results)+1,phase=phase)
        r=core.price_demo_results([r],model_prices)[0];results.append(r)
        path=save(results,snapshot,phase,model_prices=model_prices,pricing_file_sha256=pricing_file_sha256)
        print(json.dumps(dict(arm=arm,passed=r['passed'],cost=r['cost_usd'],seconds=round(r['elapsed_seconds'],1),
            checks=r['checks'],roles=[c['role'] for c in r['calls'] if c['role']!='judge'],saved=str(path))),flush=True)
    return results,path


if __name__=='__main__':
    import argparse
    from dotenv import load_dotenv
    parser=argparse.ArgumentParser();parser.add_argument('--repeats',type=int,default=1)
    parser.add_argument('--phase',default='pilot');parser.add_argument('--allow-paid-calls',action='store_true')
    parser.add_argument('--efficient-no-thinking',action='store_true')
    parser.add_argument('--profile',type=core.Path,
        default=core.ROOT/'configs/model-profiles/nemotron-nano-gpt-sol.toml')
    args=parser.parse_args();load_dotenv(core.ROOT/'.env',override=True)
    settings=core.load_settings(args.profile,core.ROOT/'configs/routing/task-classifier.toml',
        savings.PRICING,mode='live',allow_paid_calls=args.allow_paid_calls)
    settings.enable_langsmith=False
    if args.efficient_no_thinking:
        settings.efficient.extra_body=deepcopy(settings.efficient.extra_body)
        settings.efficient.extra_body.setdefault('chat_template_kwargs',{})['enable_thinking']=False
    asyncio.run(compare(settings,repeats=args.repeats,phase=args.phase))
