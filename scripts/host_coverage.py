#!/usr/bin/env python3
"""Freeze required host/case coverage and assess bound, reviewed actual captures."""
import argparse
import hashlib
import json
from pathlib import Path

from repository_files import inventory
from provider_results import claude_result_error


def digest(value):
    data = value if isinstance(value, bytes) else json.dumps(value, sort_keys=True, ensure_ascii=False).encode()
    return hashlib.sha256(data).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def save_new(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as stream:
        stream.write(json.dumps(value, indent=2, ensure_ascii=False) + '\n')


def freeze(package, config):
    package = Path(package).resolve()
    hosts = config.get('required_hosts')
    if not isinstance(hosts, list) or not hosts or len(set(hosts)) != len(hosts) or any(h not in {'codex', 'claude-code', 'chatgpt', 'claude'} for h in hosts):
        raise ValueError('Declare unique required host IDs before testing.')
    selected = []
    for source in config['case_files']:
        path = (package / source['path']).resolve()
        if not path.is_relative_to(package):
            raise ValueError('Case files must belong to the skill.')
        cases = [json.loads(line) for line in path.read_text().splitlines() if line.strip()] if path.suffix == '.jsonl' else read(path)
        ids = source.get('ids')
        if ids is not None and (not ids or set(ids) - {c['id'] for c in cases}):
            raise ValueError('A declared case selection is empty or unknown.')
        cases = [c for c in cases if c['id'] in ids] if ids is not None else [c for c in cases if c.get('kind') == 'behavior']
        verify_delivery = source.get('verify_delivery', False)
        if type(verify_delivery) is not bool:
            raise ValueError('verify_delivery must be a boolean.')
        selected.extend({'id': c['id'], 'case_sha256': digest(c), **({'verify_delivery': True} if verify_delivery else {})} for c in cases)
    if not selected or len({c['id'] for c in selected}) != len(selected):
        raise ValueError('Declare nonempty, unique matrix cases.')
    profiles = config.get('profiles', [])
    if not isinstance(profiles, list) or any(not isinstance(p, dict) for p in profiles):
        raise ValueError('Profiles must be an array of host configuration objects.')
    if profiles and ({p.get('host') for p in profiles} != set(hosts) or len(profiles) != len(hosts) or any(set(p) != {'host', 'model', 'reasoning_effort'} or any(p[k] is not None and (not isinstance(p[k], str) or not p[k].strip()) for k in ('model', 'reasoning_effort')) for p in profiles)):
        raise ValueError('Profiles must declare one model/effort configuration per required host; unknown identities stay null.')
    result = {'schema_version': 1, 'subject': str(package), 'package_hashes': inventory(package), 'required_hosts': hosts, 'profiles': profiles, 'cases': selected}
    return {**result, 'plan_sha256': digest(result)}



def public_delivery_match(report_path, attempt_id):
    """Compare an actual final host message with its one captured delivery receipt."""
    report_path = Path(report_path).resolve()
    report = read(report_path)
    rows = [row for row in report['attempts'] if row['id'] == attempt_id]
    if len(rows) != 1 or rows[0]['status'] != 'pending_review':
        raise ValueError('A completed actual capture is required for delivery comparison.')
    row = rows[0]
    case = (report_path.parent / attempt_id).resolve()
    if not case.is_relative_to(report_path.parent):
        raise ValueError('Attempt path escapes the report.')
    workspace = case / 'workspace'
    receipts = []
    for name, sha in row.get('workspace_hashes', {}).items():
        if not name.endswith('/delivery.json'):
            continue
        path = (workspace / name).resolve()
        if not path.is_relative_to(workspace) or digest(path.read_bytes()) != sha:
            raise ValueError('Captured delivery receipt changed.')
        data = read(path)
        if isinstance(data, dict) and 'message_sha256' in data:
            receipts.append(data)
    handoffs = {(item['message'], item['message_sha256'], item['destination'], item['output_sha256']) for item in receipts}
    if len(handoffs) != 1:
        raise ValueError('Require exactly one distinct captured delivery handoff.')
    receipt = receipts[0]
    expected = receipt['message']
    if not isinstance(expected, str) or not expected.strip() or digest(expected.encode()) != receipt['message_sha256']:
        raise ValueError('Delivery message does not match its receipt hash.')
    destination = Path(receipt['destination']).resolve()
    if not destination.is_relative_to(workspace) or digest(destination.read_bytes()) != receipt['output_sha256']:
        raise ValueError('Delivered document changed or escapes the captured workspace.')
    rel = str(destination.relative_to(workspace))
    if row.get('workspace_hashes', {}).get(rel) != receipt['output_sha256']:
        raise ValueError('Delivered document was not captured.')
    events_path = case / 'public-events.json'
    messages = []
    for event in read(events_path):
        if report['execution_host'] == 'codex' and event.get('type') == 'item.completed' and event.get('item', {}).get('type') == 'agent_message':
            messages.append(event['item']['text'])
        elif report['execution_host'] == 'claude-code' and event.get('type') == 'assistant':
            text = '\n'.join(part['text'] for part in event.get('message', {}).get('content', []) if part.get('type') == 'text')
            if text:
                messages.append(text)
    if not messages:
        raise ValueError('No actual public assistant message was captured.')
    actual = messages[-1]
    passed = actual.rstrip('\r\n') == expected.rstrip('\r\n')
    return {'passed': passed, 'expected_sha256': receipt['message_sha256'], 'actual_sha256': digest(actual.encode()),
            'public_events_sha256': digest(events_path.read_bytes()),
            'findings': [] if passed else ['Actual final host text differs from the finalized message.'],
            'limits': ['Exact handoff consistency is not proof of factual meaning or independent provider identity.']}


def assess(plan, package, bundles):
    captured = {k: v for k, v in plan.items() if k != 'plan_sha256'}
    if digest(captured) != plan['plan_sha256'] or inventory(package) != plan['package_hashes']:
        raise ValueError('The frozen matrix or skill artifact changed; start a versioned plan.')
    expected = {c['id']: c['case_sha256'] for c in plan['cases']}
    cells = {(host, case): [] for host in plan['required_hosts'] for case in expected}
    seen, actual, observed_profiles = set(), [], {}
    frozen_profiles = {p['host']: (p['model'], p['reasoning_effort']) for p in plan.get('profiles', [])}
    for bundle in bundles:
        report_path = Path(bundle['report']).resolve()
        report_bytes = report_path.read_bytes()
        report_hash = digest(report_bytes)
        if report_hash in seen:
            raise ValueError('A report was supplied twice.')
        seen.add(report_hash)
        report = json.loads(report_bytes)
        host = report.get('execution_host')
        if host not in plan['required_hosts'] or report['package_hashes'] != plan['package_hashes']:
            raise ValueError('Report host or artifact does not match the matrix.')
        config_path = report_path.parent / 'config.json'
        config = read(config_path) if config_path.is_file() else {}
        if config and report.get('config_sha256') != digest(config):
            raise ValueError('Captured execution configuration changed after the run.')
        models = {r.get('requested_model', report.get('requested_model')) for r in report['attempts']}
        if len(models) > 1:
            raise ValueError('One report must use a single requested model configuration.')
        profile = (report.get('requested_model') or next(iter(models), None), report.get('reasoning_effort', config.get('reasoning_effort')))
        if host in frozen_profiles and profile != frozen_profiles[host]:
            raise ValueError('Report model/effort differs from the frozen host profile.')
        if host in observed_profiles and observed_profiles[host] != profile:
            raise ValueError('Do not merge different model/effort profiles; assess them separately.')
        observed_profiles[host] = profile
        review = read(bundle['review']) if bundle.get('review') else None
        judgments = {}
        if review:
            reviewer = review.get('reviewer', {})
            if review.get('report_sha256') != report_hash or not all(isinstance(reviewer.get(k), str) and reviewer[k].strip() for k in ('kind', 'identity', 'method')):
                raise ValueError('Review must bind the exact report and identify its actual reviewer.')
            for judgment in review['cases']:
                if judgment['attempt_id'] in judgments or type(judgment.get('accepted')) is not bool or not judgment.get('rationale'):
                    raise ValueError('Reviews need unique attempts, boolean verdicts and evidence-based reasons.')
                judgments[judgment['attempt_id']] = judgment
        for row in report['attempts']:
            identifier = row['case_id']
            if identifier not in expected or row['case_sha256'] != expected[identifier]:
                raise ValueError('Report case or frozen criteria does not match the matrix.')
            status = row['status']
            verdict = 'not_run' if status in {'not_run', 'infrastructure_failure'} else 'failed'
            if status == 'pending_review':
                if row.get('exit_code') != 0 or row.get('provenance', {}).get('host') != host or not isinstance(row.get('output'), str) or not row['output'].strip():
                    raise ValueError('Successful transport needs actual output and matching host provenance.')
                events_path = report_path.parent / row['id'] / 'public-events.json'
                if Path(row['public_events']).resolve() != events_path.resolve():
                    raise ValueError('Public capture must belong to this actual attempt.')
                events = read(events_path)
                if not events or (host == 'claude-code' and not any(e.get('type') == 'result' for e in events)) or (host == 'codex' and not any(e.get('type') == 'thread.started' for e in events)):
                    raise ValueError('The expected host public trace is missing.')
                if host == 'claude-code' and any(claude_result_error(e) for e in events if e.get('type') == 'result'):
                    raise ValueError('An error result cannot be submitted as successful task output.')
                workspace = report_path.parent / row['id'] / 'workspace'
                for name, sha in row.get('workspace_hashes', {}).items():
                    path = (workspace / name).resolve()
                    if not path.is_relative_to(workspace.resolve()) or digest(path.read_bytes()) != sha:
                        raise ValueError('An actual task artifact changed after capture.')
                for name, link in row.get('workspace_links', {}).items():
                    path = workspace / name
                    if not path.is_symlink() or str(path.resolve()) != link['target']:
                        raise ValueError('A task link changed after capture.')
                    if link['kind'] == 'controlled_skill':
                        installed = report_path.parent / row['id'] / 'runtime-skill'
                        if path.resolve() != installed.resolve() or inventory(installed) != row['runtime_hashes']:
                            raise ValueError('The controlled skill alias or runtime changed.')
                    elif link['kind'] != 'workspace' or not path.resolve().is_relative_to(workspace.resolve()) or not path.resolve().exists():
                        raise ValueError('A captured task link escapes the workspace.')
                verdict = 'pending_review'
                judgment = judgments.get(row['id'])
                if judgment:
                    if judgment.get('capture_sha256') != digest(row) or judgment.get('public_events_sha256') != digest(events_path.read_bytes()):
                        raise ValueError('A judgment is stale or bound to a different output/trace.')
                    verdict = 'passed' if judgment['accepted'] else 'failed'
                    if verdict == 'passed' and next(c for c in plan['cases'] if c['id'] == identifier).get('verify_delivery'):
                        if not public_delivery_match(report_path, row['id'])['passed']:
                            verdict = 'failed'
            record = {'host': host, 'case_id': identifier, 'attempt_id': row['id'], 'report': str(report_path), 'status': verdict, 'requested_model': row.get('requested_model', report.get('requested_model')), 'resolved_model': row.get('resolved_model')}
            record.update({k: row[k] for k in ('reason', 'failure_kind', 'provider_error') if k in row})
            cells[(host, identifier)].append(record)
            actual.append(record)
        if set(judgments) - {row['id'] for row in report['attempts']}:
            raise ValueError('Review refers to an unknown attempt.')
    latest = {cell: next((row['status'] for row in reversed(history) if row['status'] != 'not_run'), 'not_run') for cell, history in cells.items()}
    hosts = {}
    for host in plan['required_hosts']:
        values = [value for (h, _), value in latest.items() if h == host]
        evaluated = sum(v in {'passed', 'failed'} for v in values)
        accepted = values.count('passed')
        hosts[host] = {'planned': len(values), 'evaluated': evaluated, 'accepted': accepted, 'pending_review': values.count('pending_review'), 'not_run': values.count('not_run'), 'task_success_percent': 100 * accepted / evaluated if evaluated else None, 'coverage_percent': 100 * evaluated / len(values)}
    return {'schema_version': 1, 'accepted': all(v == 'passed' for v in latest.values()), 'plan_sha256': plan['plan_sha256'], 'profiles': {h: {'model': p[0], 'reasoning_effort': p[1]} for h, p in observed_profiles.items()}, 'hosts': hosts,
            'cells': [{'host': h, 'case_id': c, 'status': status} for (h, c), status in latest.items()], 'attempt_history': actual,
            'limits': ['Host/model provenance and semantic review identities are reported observations, not independent provider attestation.', 'These results cover only the declared cases, artifact and execution hosts. CLI coverage does not establish browser/mobile or every model compatibility.', 'Earlier attempts remain in attempt_history; the latest observed outcome determines each cell. Unstarted or unrun work cannot erase an earlier observed outcome.']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation', choices=['freeze', 'assess'])
    parser.add_argument('--package', type=Path, required=True)
    parser.add_argument('--config', type=Path)
    parser.add_argument('--plan', type=Path)
    parser.add_argument('--bundles', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    try:
        value = freeze(args.package, read(args.config)) if args.operation == 'freeze' else assess(read(args.plan), args.package, read(args.bundles))
        save_new(args.output, value)
        print(json.dumps({'output': str(args.output), 'accepted': value.get('accepted'), 'hosts': value.get('hosts')}))
        return 0 if args.operation == 'freeze' or value['accepted'] else 1
    except (ValueError, OSError, KeyError, TypeError) as error:
        print(json.dumps({'error': str(error)}))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
