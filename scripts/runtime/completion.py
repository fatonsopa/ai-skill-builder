"""Objective-wide completion controls; trusted local workflow state, not a sandbox."""
import fnmatch
from pathlib import Path
import subprocess
import time

from .common import Invalid, digest, inventory, load, locked, relative, save, validate
from .contracts import obj, array, TEXT

BUDGET = obj({name: {'type': 'integer', 'minimum': 0 if name in ('revisions', 'model_calls') else 1}
              for name in ('runs', 'revisions', 'model_calls', 'seconds')})
CHECK = obj({'id': TEXT, 'kind': {'enum': ['mechanical', 'behavior', 'document', 'full_suite', 'report']},
             'dependencies': array(TEXT), 'case_id': TEXT, 'test_ids': array(TEXT, 1),
             'profile': obj({'host': TEXT, 'model': {'type': ['string', 'null']},
                             'reasoning_effort': {'type': ['string', 'null']}})},
            required=['id', 'kind', 'dependencies'])
CONTRACT = obj({'objective_id': TEXT, 'goal': TEXT, 'project': TEXT,
                'scope': array(TEXT, 1), 'checks': array(CHECK, 1), 'budget': BUDGET,
                'delivery': obj({'kind': {'enum': ['local', 'git_push', 'report']},
                                 'authority': TEXT, 'remote': TEXT, 'ref': TEXT},
                                required=['kind', 'authority'])})


def create(workspace, definition):
    validate(definition, CONTRACT)
    definition = dict(definition)
    workspace, project = Path(workspace).resolve(), Path(definition['project']).resolve()
    definition['project'] = str(project)
    registry = (workspace / '.skill-builder-completion').resolve()
    if not registry.is_relative_to(workspace) or registry.is_relative_to(project) or project.is_relative_to(registry):
        raise Invalid('Keep completion records outside the project.')
    for pattern in definition['scope']:
        relative(pattern)
    identifiers = [c['id'] for c in definition['checks']]
    if len(identifiers) != len(set(identifiers)):
        raise Invalid('Completion check IDs must be unique.')
    for check in definition['checks']:
        if check['kind'] != 'report' and not check['dependencies']:
            raise Invalid('Executable and document checks need explicit input dependencies.')
        for dependency in check['dependencies']:
            relative(dependency)
    delivery = definition['delivery']
    if delivery['kind'] == 'git_push' and (not delivery.get('remote') or not delivery.get('ref', '').startswith('refs/heads/')):
        raise Invalid('Authorized Git delivery needs its exact remote and branch ref.')
    with locked(registry):
        index_path = registry / 'projects.json'
        index = load(index_path) if index_path.exists() else {}
        key = digest(str(project))
        if key in index:
            previous = read(index[key])
            if previous['contract'] == definition:
                return {'policy': index[key], 'status': previous['phase'], 'reused_existing_objective': True}
            if previous['phase'] != 'delivered':
                raise Invalid('This project already has an unfinished objective. New files, IDs or versions cannot reset it.')
            if previous['contract']['objective_id'] == definition['objective_id']:
                raise Invalid('A completed objective ID cannot be reused to reset its history.')
        path = registry / (key + '-' + digest(definition['objective_id']) + '.json')
        if path.exists():
            raise Invalid('Objective history already exists; do not replace it.')
        state = {'schema_version': 1, 'workspace': str(workspace), 'contract': definition,
                 'contract_sha256': digest(definition), 'created_unix': time.time(),
                 'phase': 'working', 'usage': {'runs': 0, 'revisions': 0, 'model_calls': 0},
                 'runs': {}, 'receipts': {}, 'findings': [], 'events': []}
        save(path, state)
        index[key] = str(path)
        save(index_path, index)
    return {'policy': str(path), 'status': 'working', 'reused_existing_objective': False}


def read(path):
    state = load(path)
    if digest(state['contract']) != state['contract_sha256']:
        raise Invalid('The frozen completion contract changed.')
    return state


def _available(state, *, delivery=False):
    if state['phase'] == 'delivered':
        raise Invalid('Objective delivered; do not reopen it for further improvement.')
    if state['phase'] == 'delivery_pending' and not delivery:
        raise Invalid('Required checks passed. Deliver now; log improvements as follow-ups.')
    if not delivery and time.time() - state['created_unix'] >= state['contract']['budget']['seconds']:
        raise Invalid('Objective-wide time budget exhausted; a new run does not reset it.')


def reserve(path, unit, *, detail):
    if unit not in ('runs', 'revisions', 'model_calls'):
        raise Invalid('Unknown completion budget unit.')
    path = Path(path)
    with locked(path.parent):
        state = read(path)
        _available(state)
        if state['usage'][unit] >= state['contract']['budget'][unit]:
            raise Invalid('Objective-wide ' + unit + ' budget exhausted; retain history and report the gap.')
        state['usage'][unit] += 1
        state['events'].append({'event': 'reserved', 'unit': unit, 'detail': detail, 'at': time.time()})
        save(path, state)  # Reserve before the work; interruptions still count.
    return state


def enroll(path, run, request):
    path, run = Path(path).resolve(), Path(run).resolve()
    state = read(path)
    if not run.is_relative_to(Path(state['workspace'])) or run.is_relative_to(Path(state['contract']['project'])):
        raise Invalid('The run must use the completion workspace outside the project.')
    if request.get('source') and Path(request['source']).resolve() != Path(state['contract']['project']):
        raise Invalid('The run targets a different completion project.')
    scope = state['contract']['scope']
    if any(not any(fnmatch.fnmatchcase(name, pattern) for pattern in scope) for name in request.get('allowed_paths', [])):
        raise Invalid('Request expands the frozen completion edit scope.')
    identity = {k: request.get(k) for k in ('operation', 'skill_name', 'brief', 'allowed_paths', 'preserve_literals', 'target_success_percent')}
    with locked(path.parent):
        state = read(path)
        _available(state)
        if state.get('request_identity') not in (None, identity):
            raise Invalid('Request changes the frozen objective; classify it before expanding work.')
        if str(run) in state['runs']:
            raise Invalid('This run is already enrolled.')
        if state['usage']['runs'] >= state['contract']['budget']['runs']:
            raise Invalid('Objective-wide runs budget exhausted; a new directory does not reset it.')
        state['usage']['runs'] += 1
        state['events'].append({'event': 'reserved', 'unit': 'runs', 'detail': str(run), 'at': time.time()})
        state['request_identity'] = identity
        state['runs'][str(run)] = {'status': 'enrolled'}
        save(path, state)
    return {'path': str(path), 'contract_sha256': state['contract_sha256']}


def guard(state, *, delivery=False):
    binding = state.get('completion')
    if not binding:
        return  # Historical protocol runs retain their recorded contract.
    policy = read(binding['path'])
    if policy['contract_sha256'] != binding['contract_sha256']:
        raise Invalid('Run completion binding changed.')
    _available(policy, delivery=delivery)


def freeze_plan(state, spec, plan):
    if not state.get('completion'):
        return
    path = Path(state['completion']['path'])
    with locked(path.parent):
        policy = read(path)
        frozen = {'spec': spec, 'plan': plan}
        if policy.get('plan') not in (None, frozen):
            raise Invalid('A new run cannot change frozen requirements, cases or definition of done.')
        checks = {c['id']: c for c in policy['contract']['checks']}
        case_ids = {c.get('case_id', c['id']) for c in checks.values()}
        if state['request']['operation'] not in ('audit', 'plan', 'specify') and any(c['id'] not in case_ids for c in plan['cases']):
            raise Invalid('Plan adds validation outside the frozen completion check list.')
        policy['plan'] = frozen
        save(path, policy)


def footprint(check, package):
    files = inventory(package)
    selected = {}
    for pattern in check['dependencies']:
        matches = {p: sha for p, sha in files.items() if fnmatch.fnmatchcase(p, pattern)}
        if not matches:
            raise Invalid('Completion dependency matches no file: ' + pattern)
        selected.update(matches)
    return selected


def _retained_inputs_valid(receipt):
    proof = load(receipt['evidence'])
    retained = proof.get('retained_host_inputs')
    if retained is None:
        return True
    return all(Path(name).is_file() and digest(Path(name).read_bytes()) == sha
               for name, sha in retained['files'].items()) and all(
        Path(name).is_symlink() and str(Path(name).resolve()) == target
        for name, target in retained['links'].items()) and all(
        inventory(name) == hashes for name, hashes in retained['runtimes'].items())


def _host_inputs(manifest_path, manifest, bundles):
    # Seal the raw evidence graph assessed below, including linked runtime copies.
    result = {'files': {}, 'links': {}, 'runtimes': {}}
    def keep(path):
        path = Path(path).resolve()
        result['files'][str(path)] = digest(path.read_bytes())
    for path in (manifest_path, manifest['plan'], manifest['bundles']):
        keep(path)
    for bundle in bundles:
        report_path = Path(bundle['report']).resolve()
        keep(report_path)
        if bundle.get('review'):
            keep(bundle['review'])
        config = report_path.parent / 'config.json'
        if config.exists():
            keep(config)
        for row in load(report_path)['attempts']:
            if row['status'] != 'pending_review':
                continue
            attempt = report_path.parent / row['id']
            keep(attempt / 'public-events.json')
            for name in row.get('workspace_hashes', {}):
                keep(attempt / 'workspace' / name)
            for name, link in row.get('workspace_links', {}).items():
                result['links'][str(attempt / 'workspace' / name)] = link['target']
                if link['kind'] == 'controlled_skill':
                    runtime = attempt / 'runtime-skill'
                    result['runtimes'][str(runtime)] = inventory(runtime)
    return result


def status(path, package=None):
    state = read(path)
    result = {'objective_id': state['contract']['objective_id'], 'phase': state['phase'],
              'usage': state['usage'], 'budget': state['contract']['budget'],
              'elapsed_seconds': max(0, time.time() - state['created_unix']),
              'findings': state['findings'], 'checks': []}
    for check in state['contract']['checks']:
        receipt = state['receipts'].get(check['id'])
        try:
            valid = bool(receipt and package is not None and receipt['dependencies'] == footprint(check, package)
                         and Path(receipt['evidence']).is_file()
                         and digest(Path(receipt['evidence']).read_bytes()) == receipt['evidence_sha256']
                         and _retained_inputs_valid(receipt))
        except (Invalid, OSError):
            valid = False
        result['checks'].append({'id': check['id'], 'valid': valid,
                                 'action': 'retain_evidence' if valid else 'run_required_check',
                                 'fresh_current_artifact': bool(valid and receipt['observed_artifact'] == inventory(package)),
                                 'evidence_origin': receipt.get('origin') if receipt else None})
    result['next_action'] = 'deliver' if state['phase'] == 'delivery_pending' else 'complete_required_checks'
    return result


def authorize_case(path, case_id, package, *, case=None, profile=None, check_id=None):
    policy = read(path)
    _available(policy)
    checks = {c['id']: c for c in policy['contract']['checks']}
    identifier = check_id or case_id
    if identifier not in checks or checks[identifier]['kind'] != 'behavior' or checks[identifier].get('case_id', identifier) != case_id:
        raise Invalid('Model task is outside the frozen behavioral validation scope: ' + case_id)
    if checks[identifier].get('profile') and checks[identifier]['profile'] != profile:
        raise Invalid('Model task differs from its frozen host/model/effort profile.')
    row = next(r for r in status(path, package)['checks'] if r['id'] == identifier)
    if row['valid']:
        raise Invalid('This check has valid input-bound evidence; retain it instead of launching another model.')
    if case is not None:
        task = {k: case.get(k) for k in ('kind', 'critical', 'semantic', 'request', 'resources', 'fixtures', 'expect')}
        path = Path(path)
        with locked(path.parent):
            policy = read(path)
            expected = policy.setdefault('task_bindings', {}).get(identifier)
            if expected is not None and expected != digest(task):
                raise Invalid('Behavioral task or criteria changed after first authorization.')
            native = next((c for c in policy.get('plan', {}).get('plan', {}).get('cases', []) if c['id'] == case_id), None)
            if native and {k: native.get(k) for k in task} != task:
                raise Invalid('Behavioral task differs from the frozen native plan.')
            policy['task_bindings'][identifier] = digest(task)
            from host_coverage import digest as case_digest
            policy.setdefault('case_bindings', {})[identifier] = case_digest(case)
            save(path, policy)
    return reserve(path, 'model_calls', detail=identifier)


def finding(path, classification, requirement, text, checks=()):
    if classification not in ('blocker', 'follow_up', 'scope_change') or not text.strip():
        raise Invalid('Classify and explain the finding.')
    path = Path(path)
    with locked(path.parent):
        policy = read(path)
        ids = {r['id'] for r in policy.get('plan', {}).get('spec', {}).get('requirements', [])}
        known_checks = {c['id'] for c in policy['contract']['checks']}
        if policy['phase'] == 'delivered' and classification == 'blocker':
            raise Invalid('Use a new objective for work after delivery; retain this completed history.')
        if classification == 'blocker' and (requirement not in ids or not checks or set(checks) - known_checks):
            raise Invalid('A blocker must reference an agreed requirement and affected frozen checks.')
        item = {'id': str(len(policy['findings']) + 1), 'classification': classification,
                'requirement': requirement, 'text': text.strip(), 'checks': list(checks), 'resolved': False}
        policy['findings'].append(item)
        if classification == 'blocker':
            for identifier in checks:
                policy['receipts'].pop(identifier, None)
            policy['phase'] = 'working'
        save(path, policy)
    return item


def record(path, identifier, package, evidence, *, origin='executed', native_passed=False):
    path, evidence = Path(path), Path(evidence).resolve()
    if evidence.is_relative_to(Path(package).resolve()):
        raise Invalid('Keep validation evidence outside the package.')
    with locked(path.parent):
        policy = read(path)
        _available(policy, delivery=True)
        checks = {c['id']: c for c in policy['contract']['checks']}
        if identifier not in checks:
            raise Invalid('Unknown required check.')
        check = checks[identifier]
        proof = load(evidence)
        if check['kind'] == 'behavior' and not native_passed:
            raise Invalid('Behavioral evidence needs the actual native semantic-review gate.')
        if not native_passed:
            if proof.get('passed') is not True:
                raise Invalid('Required check did not pass.')
            from run_tests import digest as artifact_digest
            if proof.get('artifact_sha256') != artifact_digest(inventory(package)):
                raise Invalid('Check report is not bound to the current artifact.')
            if check['kind'] not in ('mechanical', 'full_suite'):
                raise Invalid('Document/report checks require their native acceptance gate.')
            if not proof.get('results') or any(r.get('passed') is not True or r.get('exit_code') != 0 for r in proof['results']):
                raise Invalid('Retain the actual executed check results, not a summary flag.')
            if check['kind'] == 'mechanical':
                selected = {name.strip() for row in proof['results'] for name in row['id'].split(' + ')}
                if set(check.get('test_ids', [identifier])) - selected:
                    raise Invalid('Executed report does not contain this frozen required test selection.')
            if check['kind'] == 'full_suite' and proof.get('mode') != 'full':
                raise Invalid('A scoped test report is not a full-suite result.')
        policy['receipts'][identifier] = {'dependencies': footprint(check, package),
            'observed_artifact': inventory(package), 'evidence': str(evidence),
            'evidence_sha256': digest(evidence.read_bytes()), 'origin': origin}
        for item in policy['findings']:
            if item['classification'] == 'blocker' and item['checks'] and all(c in policy['receipts'] for c in item['checks']):
                item['resolved'] = True
        save(path, policy)
        current = status(path, package)
        if all(c['valid'] for c in current['checks']) and not any(f['classification'] == 'blocker' and not f['resolved'] for f in policy['findings']):
            policy['phase'] = 'delivery_pending'
            policy['delivery_artifact'] = inventory(package)
            save(path, policy)
    return status(path, package)


def delivered(path, package):
    path = Path(path)
    with locked(path.parent):
        policy = read(path)
        if policy['phase'] != 'delivery_pending' or inventory(package) != policy.get('delivery_artifact'):
            raise Invalid('Delivery requires the exact artifact with all required checks valid.')
        current = status(path, package)
        if not all(c['valid'] for c in current['checks']):
            raise Invalid('Delivery evidence changed.')
        target = Path(policy['contract']['project'])
        if target != Path(package).resolve() or inventory(target) != policy['delivery_artifact']:
            raise Invalid('The validated artifact has not been delivered to its agreed project.')
        delivery = policy['contract']['delivery']
        receipt = {'kind': delivery['kind'], 'artifact': policy['delivery_artifact']}
        if delivery['kind'] == 'git_push':
            head = subprocess.check_output(['git', '-C', str(target), 'rev-parse', 'HEAD'], text=True).strip()
            tracked = subprocess.check_output(['git', '-C', str(target), 'ls-tree', '-r', '--name-only', 'HEAD'], text=True).splitlines()
            if set(tracked) != set(policy['delivery_artifact']) or any(
                digest(subprocess.check_output(['git', '-C', str(target), 'show', 'HEAD:' + name])) != sha
                for name, sha in policy['delivery_artifact'].items()
            ):
                raise Invalid('The commit does not contain the exact validated public artifact.')
            remote = subprocess.check_output(['git', 'ls-remote', '--', delivery['remote'], delivery['ref']], text=True).split()
            if not remote or remote[0] != head:
                raise Invalid('The agreed remote branch does not contain the delivered commit.')
            receipt.update(commit=head, remote=delivery['remote'], ref=delivery['ref'])
        policy.update(phase='delivered', delivery_receipt=receipt)
        save(path, policy)
    return {'phase': 'delivered', 'receipt': receipt}


def delivery_ready(state, package):
    if not state.get('completion'):
        return
    path = state['completion']['path']
    policy = read(path)
    if policy['phase'] != 'delivery_pending' or inventory(package) != policy.get('delivery_artifact'):
        raise Invalid('Finish the frozen completion checks before delivery; do not add unrelated work.')
    if not all(c['valid'] for c in status(path, package)['checks']):
        raise Invalid('Completion evidence is stale.')


def sync_native(root, state, review=None):
    """Record accepted native outcomes; no generic JSON flag can approve behavior."""
    if not state.get('completion'):
        return
    root = Path(root)
    package = root / 'candidate' if (root / 'candidate').exists() else Path(state['source']) if state.get('source') else Path(read(state['completion']['path'])['contract']['project'])
    path = state['completion']['path']
    policy = read(path)
    if state.get('evaluation') and inventory(package) != state['evaluation']['package_hashes']:
        return
    rows = {c['id']: c for c in state.get('evaluation', {}).get('attempts', [])}
    for check in policy['contract']['checks']:
        if check.get('profile'):
            continue  # A specific external profile needs its bound host assessment.
        result = rows.get(check.get('case_id', check['id']))
        passed = result and result.get('status') == 'passed'
        passed = passed or (check['kind'] == 'document' and state.get('document_check', {}).get('passed') is True)
        passed = passed or (check['kind'] == 'report' and state['request']['operation'] in ('audit', 'plan', 'specify') and state.get('phase') == 'complete')
        if not passed:
            continue
        proof = {'run_id': state['run_id'], 'check_id': check['id'], 'result': result,
                 'native_review': review, 'document_check': state.get('document_check'),
                 'report_data': state.get('data') if check['kind'] == 'report' else None,
                 'artifact': inventory(package)}
        evidence = root / 'completion-evidence' / (digest(proof) + '.json')
        save(evidence, proof)
        record(path, check['id'], package, evidence, origin='native_accepted_evidence', native_passed=True)


def record_hosts(path, package, manifest):
    """Reuse the existing host guard instead of trusting a passing summary flag."""
    from host_coverage import assess, digest as case_digest
    manifest_path = Path(manifest).resolve()
    manifest = load(manifest_path)
    plan, bundles = load(manifest['plan']), load(manifest['bundles'])
    report = assess(plan, package, bundles)
    if not report['accepted']:
        raise Invalid('The declared host assessment has failed or missing outcomes.')
    policy = read(path)
    case_ids = {c['id'] for c in plan['cases']}
    evidence = Path(path).parent / ('host-assessment-' + digest(report) + '.json')
    save(evidence, {**report, 'retained_host_inputs': _host_inputs(manifest_path, manifest, bundles)})
    for check in policy['contract']['checks']:
        if check['kind'] != 'behavior' or check.get('case_id', check['id']) not in case_ids:
            continue
        identifier = check.get('case_id', check['id'])
        expected = policy.get('case_bindings', {}).get(check['id'])
        native = next((c for c in policy.get('plan', {}).get('plan', {}).get('cases', []) if c['id'] == identifier), None)
        if expected is None and native is not None:
            expected = case_digest(native)
        observed = next(c['case_sha256'] for c in plan['cases'] if c['id'] == identifier)
        if expected is None or expected != observed:
            raise Invalid('Host case differs from the frozen authorized task and criteria.')
        profile = check.get('profile')
        if profile and (profile not in plan['profiles'] or report['profiles'].get(profile['host']) != {k: profile[k] for k in ('model', 'reasoning_effort')}):
            raise Invalid('Host evidence does not match the frozen check profile.')
        record(path, check['id'], package, evidence, origin='reviewed_host_assessment', native_passed=True)
    return status(path, package)


def amend(path, definition, authority):
    """Explicit material replan: retain usage, elapsed time and previous contracts."""
    validate(definition, CONTRACT)
    definition = {**definition, 'project': str(Path(definition['project']).resolve())}
    if len({c['id'] for c in definition['checks']}) != len(definition['checks']):
        raise Invalid('Completion check IDs must be unique.')
    for pattern in definition['scope']:
        relative(pattern)
    for check in definition['checks']:
        if check['kind'] != 'report' and not check['dependencies']:
            raise Invalid('Checks need explicit input dependencies.')
        for dependency in check['dependencies']:
            relative(dependency)
    if not isinstance(authority, str) or not authority.strip():
        raise Invalid('Record the actual user instruction authorizing this scope or budget change.')
    path = Path(path)
    with locked(path.parent):
        state = read(path)
        if state['phase'] == 'delivered' or any(definition[k] != state['contract'][k] for k in ('objective_id', 'project')):
            raise Invalid('Amend only this unfinished objective; do not replace its identity.')
        if any(definition['budget'][k] < state['usage'][k] for k in state['usage']):
            raise Invalid('A material replan cannot erase already consumed budget.')
        state.setdefault('amendments', []).append({'authority': authority.strip(),
            'previous_contract': state['contract'], 'previous_sha256': state['contract_sha256'],
            'previous_plan': state.get('plan'), 'previous_receipts': state['receipts'],
            'usage': dict(state['usage']), 'at': time.time()})
        delivery = definition['delivery']
        if delivery['kind'] == 'git_push' and (not delivery.get('remote') or not delivery.get('ref', '').startswith('refs/heads/')):
            raise Invalid('Authorized Git delivery needs its exact remote and branch ref.')
        state.update(contract=definition, contract_sha256=digest(definition), phase='working', receipts={})
        for key in ('plan', 'request_identity', 'task_bindings', 'case_bindings', 'delivery_artifact'):
            state.pop(key, None)
        save(path, state)
    return status(path)
