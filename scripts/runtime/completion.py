"""Objective-wide completion controls; trusted local workflow state, not a sandbox."""
import fnmatch
import json
from pathlib import Path
import subprocess
import time

from .common import Invalid, digest, inventory, load, locked, relative, save, validate
from .contracts import obj, array, TEXT

BUDGET = obj({name: {'type': 'integer', 'minimum': 0 if name in ('revisions', 'model_calls') else 1}
              for name in ('runs', 'revisions', 'model_calls', 'seconds')})
BUDGET['properties']['wall_seconds'] = {'type': 'integer', 'minimum': 1}
CHECK = obj({'id': TEXT, 'kind': {'enum': ['mechanical', 'behavior', 'document', 'full_suite', 'report']},
             'dependencies': array(TEXT), 'case_id': TEXT, 'test_ids': array(TEXT, 1),
             'profile': obj({'host': TEXT, 'model': {'type': ['string', 'null']},
                             'reasoning_effort': {'type': ['string', 'null']}})},
            required=['id', 'kind', 'dependencies'])
CONTRACT = obj({'objective_id': TEXT, 'goal': TEXT, 'project': TEXT,
                'scope': array(TEXT, 1), 'checks': array(CHECK, 1), 'budget': BUDGET,
                'checkpoints': array(obj({'id': TEXT, 'checks': array(TEXT, 1), 'depends_on': array(TEXT), 'lessons': array(TEXT)})),
                'delivery': obj({'kind': {'enum': ['local', 'git_push', 'report']},
                                 'authority': TEXT, 'remote': TEXT, 'ref': TEXT},
                                required=['kind', 'authority'])}, required=['objective_id', 'goal', 'project', 'scope', 'checks', 'budget', 'delivery'])


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
    checkpoints = definition.get('checkpoints', [])
    by_id = {row['id']: row for row in checkpoints}
    if len(by_id) != len(checkpoints):
        raise Invalid('Checkpoint IDs must be unique.')
    def visit(identifier, trail):
        if identifier in trail:
            raise Invalid('Cyclic checkpoint dependencies.')
        row = by_id[identifier]
        if set(row['checks']) - set(identifiers) or set(row['depends_on']) - set(by_id):
            raise Invalid('Checkpoint references unknown checks or dependencies.')
        for dependency in row['depends_on']:
            visit(dependency, {*trail, identifier})
    for identifier in by_id:
        visit(identifier, set())
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
    if not delivery and elapsed(state)['active_seconds'] >= state['contract']['budget']['seconds']:
        raise Invalid('Objective-wide active time budget exhausted; a new run does not reset it.')
    wall_cap = state['contract']['budget'].get('wall_seconds')
    if not delivery and wall_cap is not None and elapsed(state)['wall_seconds'] >= wall_cap:
        raise Invalid('Explicit wall-clock cap exhausted; waiting does not extend it.')


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
        raise Invalid(f"The run must use the completion workspace outside the project: workspace={state['workspace']}, project={state['contract']['project']}, requested_run={run}.")
    if request.get('source') and Path(request['source']).resolve() != Path(state['contract']['project']):
        raise Invalid('The run targets a different completion project.')
    if request.get('checkpoint'):
        component_eligible(state, request['checkpoint'], state['contract']['project'])
    elif any(g.get('resumed_unix') is None for g in state.get('user_gates', [])):
        raise Invalid('A user gate is waiting; name an independent eligible checkpoint or resume with actual authorization.')
    valid = {row['id'] for row in status_checks(state, state['contract']['project']) if row['valid']}
    incompatible = []
    for check in checkpoint_checks(state, request.get('checkpoint')):
        if check['id'] in valid:
            continue
        if check['kind'] == 'report' and request['operation'] not in ('audit', 'plan', 'specify'):
            incompatible.append({'check_id': check['id'], 'reason': 'read_only_report_in_write_checkpoint'})
        if check.get('profile') and request.get('host', {}).get('external_cli') is False:
            incompatible.append({'check_id': check['id'], 'reason': 'external_assessment_in_native_only_checkpoint'})
    if incompatible:
        raise Invalid('Completion checks cannot be fulfilled by this native run: ' + json.dumps(incompatible, sort_keys=True)
                      + '. Report checks accept completed read-only audit/specify/plan outcomes; bind package assertions as mechanical cases. Profile-bound checks need a separate host assessment; native-only observations omit profile. Use declared checkpoints for distinct stages. No run budget was consumed.')
    scope = state['contract']['scope']
    if any(not any(fnmatch.fnmatchcase(name, pattern) for pattern in scope) for name in request.get('allowed_paths', [])):
        raise Invalid('Request expands the frozen completion edit scope.')
    identity = {k: request.get(k) for k in ('operation', 'skill_name', 'brief', 'allowed_paths', 'preserve_literals', 'target_success_percent')}
    with locked(path.parent):
        state = read(path)
        _available(state)
        identities = state.setdefault('checkpoint_requests', {}) if request.get('checkpoint') else state
        identity_key = request.get('checkpoint') or 'request_identity'
        if identities.get(identity_key) not in (None, identity):
            raise Invalid('Request changes the frozen objective; classify it before expanding work.')
        if str(run) in state['runs']:
            raise Invalid('This run is already enrolled.')
        if state['usage']['runs'] >= state['contract']['budget']['runs']:
            raise Invalid('Objective-wide runs budget exhausted; a new directory does not reset it.')
        if request.get('checkpoint') and any(g.get('resumed_unix') is None for g in state.get('user_gates', [])):
            component_eligible(state, request['checkpoint'], state['contract']['project'])
            if not any(a['checkpoint'] == request['checkpoint'] and a.get('ended_unix') is None for a in state.get('activity_intervals', [])):
                state.setdefault('activity_intervals', []).append({'checkpoint': request['checkpoint'], 'started_unix': time.time(), 'ended_unix': None})
        state['usage']['runs'] += 1
        state['events'].append({'event': 'reserved', 'unit': 'runs', 'detail': str(run), 'at': time.time()})
        identities[identity_key] = identity
        state['runs'][str(run)] = {'status': 'enrolled'}
        save(path, state)
    return {'path': str(path), 'contract_sha256': state['contract_sha256']}


def guard(state, *, delivery=False):
    binding = state.get('completion')
    if not binding:
        return  # Historical protocol runs retain their recorded contract.
    policy = read(binding['path'])
    if policy['contract_sha256'] != binding['contract_sha256'] and not budget_only_binding(policy, binding['contract_sha256']):
        raise Invalid('Run completion binding changed.')
    _available(policy, delivery=delivery)
    if not delivery:
        if state.get('request', {}).get('checkpoint'):
            component_eligible(policy, state['request']['checkpoint'], Path(state['run_directory']) / 'candidate' if state.get('run_directory') and (Path(state['run_directory']) / 'candidate').is_dir() else policy['contract']['project'])
        elif any(g.get('resumed_unix') is None for g in policy.get('user_gates', [])):
            raise Invalid('Waiting for actual user authorization.')


def budget_only_change(previous, current):
    return {k: v for k, v in previous.items() if k != 'budget'} == {k: v for k, v in current.items() if k != 'budget'}


def budget_only_binding(policy, captured_sha256):
    """Follow verified amendment history; a material change breaks the chain."""
    current, current_sha = policy['contract'], policy['contract_sha256']
    for amendment in reversed(policy.get('amendments', [])):
        if current_sha == captured_sha256:
            return True
        previous = amendment['previous_contract']
        if digest(previous) != amendment['previous_sha256'] or not budget_only_change(previous, current):
            return False
        current, current_sha = previous, amendment['previous_sha256']
    return current_sha == captured_sha256


def checkpoint_checks(policy, identifier=None):
    checks = policy['contract']['checks']
    if identifier is None:
        return checks
    declarations = {row['id']: row for row in policy['contract'].get('checkpoints', [])}
    if identifier not in declarations:
        raise Invalid('Unknown frozen checkpoint.')
    return [check for check in checks if check['id'] in declarations[identifier]['checks']]


def frozen_plan(policy, checkpoint=None):
    return policy.get('checkpoint_plans', {}).get(checkpoint, {}) if checkpoint else policy.get('plan', {})


def native_case(policy, check_id, case_id):
    plans = [policy.get('plan', {})]
    plans += [plan for identifier, plan in policy.get('checkpoint_plans', {}).items()
              if check_id in {check['id'] for check in checkpoint_checks(policy, identifier)}]
    cases = [case for plan in plans for case in plan.get('plan', {}).get('cases', []) if case['id'] == case_id]
    if cases and any(case != cases[0] for case in cases):
        raise Invalid('Conflicting frozen cases share this completion check.')
    return cases[0] if cases else None


def freeze_plan(state, spec, plan):
    if not state.get('completion'):
        return
    path = Path(state['completion']['path'])
    with locked(path.parent):
        policy = read(path)
        frozen = {'spec': spec, 'plan': plan}
        checkpoint = state['request'].get('checkpoint')
        previous = frozen_plan(policy, checkpoint)
        if previous and previous != frozen:
            revision = (state.get('planning_revisions') or [{}])[-1]
            if not revision.get('metadata_only') or spec != previous['spec'] or revision['invalidated'].get('plan') != digest(previous['plan']):
                raise Invalid('A new run cannot change frozen requirements, cases or definition of done.')
            from .artifacts import check_plan_metadata_change
            check_plan_metadata_change(previous['plan'], plan)
            policy['events'].append({'event': 'plan_metadata_corrected', 'before_sha256': digest(previous),
                                     'after_sha256': digest(frozen), 'run_id': state['run_id'], 'at': time.time()})
        checks = {c['id']: c for c in checkpoint_checks(policy, checkpoint)}
        mechanical_ids = {identifier for c in checks.values() if c['kind'] == 'mechanical'
                          for identifier in [c['id'], *c.get('test_ids', [])]}
        behavior_ids = {c.get('case_id', c['id']) for c in checks.values() if c['kind'] == 'behavior'}
        if state['request']['operation'] not in ('audit', 'plan', 'specify'):
            unbound = []
            for case in plan['cases']:
                group = case.get('completion_check')
                if group is not None:
                    check = checks.get(group)
                    if case.get('kind', 'command') == 'behavior' or not check or check['kind'] != 'mechanical' or ('test_ids' in check and case['id'] not in check['test_ids']):
                        raise Invalid(f"Case {case['id']} has an invalid mechanical completion_check: {group}. Existing explicit test_ids and behavioral case_id bindings remain fixed.")
                elif case['id'] not in (behavior_ids if case.get('kind', 'command') == 'behavior' else mechanical_ids):
                    unbound.append(case['id'])
            if unbound:
                raise Invalid('Plan adds validation outside the frozen completion check list: '
                              + json.dumps({'unbound_case_ids': unbound,
                                            'declared_mechanical_ids': sorted(mechanical_ids),
                                            'declared_behavior_ids': sorted(behavior_ids)}, sort_keys=True)
                              + '. The plan was not frozen. Bind legitimate mechanical members to an existing group with completion_check; explicit test_ids remain fixed. Correct the response to the agreed checks. Use completion-amend only for an authorized material change; that amendment requires a new run with the same policy and retained budget.')
            scope = policy['contract']['scope']
            if any(not any(fnmatch.fnmatchcase(name, pattern) for pattern in scope) for name in plan.get('allowed_candidate_paths', [])):
                raise Invalid('Completion scope and dependencies are relative to the project root, not the workspace or destination prefix. Resolve the declared edit scope before production.')
        if checkpoint:
            policy.setdefault('checkpoint_plans', {})[checkpoint] = frozen
        else:
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
    document = proof.get('document_artifact')
    if document is not None and inventory(document['root']) != document['files']:
        return False
    report_source = proof.get('report_source')
    if report_source is not None and inventory(report_source['root']) != report_source['files']:
        return False
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
        for supplement in bundle.get('public_supplements', []):
            keep(supplement['path'])
        if bundle.get('reuse'):
            keep(bundle['reuse']['source_plan'])
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
            for dependency in row.get('dependencies', {}).values():
                result['runtimes'][dependency['path']] = dependency['files']
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
              'elapsed_seconds': elapsed(state)['wall_seconds'], **elapsed(state),
              'user_gates': state.get('user_gates', []), 'checkpoints': state.get('checkpoints', {}),
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
    if any(g.get('resumed_unix') is None and identifier in g['checks'] for g in policy.get('user_gates', [])):
        raise Invalid('Behavioral check is waiting for actual user authorization.')
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
            native = native_case(policy, identifier, case_id)
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
        ids = {r['id'] for plan in [policy.get('plan', {}), *policy.get('checkpoint_plans', {}).values()] for r in plan.get('spec', {}).get('requirements', [])}
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
        if all(c['valid'] for c in current['checks']) and not any(g.get('resumed_unix') is None for g in policy.get('user_gates', [])) and not any(f['classification'] == 'blocker' and not f['resolved'] for f in policy['findings']):
            policy['phase'] = 'delivery_pending'
            policy['delivery_artifact'] = inventory(package)
            save(path, policy)
    return status(path, package)


def delivered(path, package):
    path = Path(path)
    with locked(path.parent):
        policy = read(path)
        if any(g.get('resumed_unix') is None for g in policy.get('user_gates', [])):
            raise Invalid('Delivery is waiting for actual user authorization.')
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
    checkpoint = state['request'].get('checkpoint')
    plan = frozen_plan(policy, checkpoint)
    for check in checkpoint_checks(policy, checkpoint):
        if check.get('profile'):
            continue  # A specific external profile needs its bound host assessment.
        result = rows.get(check.get('case_id', check['id']))
        if check['kind'] == 'document':
            passed = state.get('document_check', {}).get('passed') is True
        elif check['kind'] == 'report':
            passed = state['request']['operation'] in ('audit', 'plan', 'specify') and state.get('phase') == 'complete'
        elif check['kind'] == 'mechanical':
            members = [case['id'] for case in plan.get('plan', {}).get('cases', []) if case.get('completion_check') == check['id']]
            result = [rows.get(identifier) for identifier in check.get('test_ids', members or [check['id']])]
            passed = bool(result) and all(row and row.get('status') == 'passed' for row in result)
        else:
            passed = bool(result and result.get('status') == 'passed')
        if not passed:
            continue
        proof = {'run_id': state['run_id'], 'check_id': check['id'], 'result': result,
                 'native_review': review, 'document_check': state.get('document_check'), 'document_artifact': state.get('document_artifact'),
                 'report_data': state.get('data') if check['kind'] == 'report' else None,
                 'artifact': inventory(package)}
        if check['kind'] == 'report' and state.get('source'):
            baseline = root / 'baseline'
            if not baseline.is_dir() or inventory(baseline) != state.get('source_snapshot'):
                raise Invalid('Report evidence needs its unchanged captured source baseline.')
            proof['report_source'] = {'root': str(baseline.resolve()), 'files': state['source_snapshot']}
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
        native = native_case(policy, check['id'], identifier)
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
        budget_only = budget_only_change(state['contract'], definition)
        state.setdefault('amendments', []).append({'authority': authority.strip(),
            'previous_contract': state['contract'], 'previous_sha256': state['contract_sha256'],
            **({} if budget_only else {'previous_plan': state.get('plan'), 'previous_checkpoint_plans': state.get('checkpoint_plans'), 'previous_checkpoint_requests': state.get('checkpoint_requests'), 'previous_receipts': state['receipts']}),
            'usage': dict(state['usage']), 'at': time.time()})
        delivery = definition['delivery']
        if delivery['kind'] == 'git_push' and (not delivery.get('remote') or not delivery.get('ref', '').startswith('refs/heads/')):
            raise Invalid('Authorized Git delivery needs its exact remote and branch ref.')
        state.update(contract=definition, contract_sha256=digest(definition))
        if not budget_only:
            state.update(phase='working', receipts={})
            for key in ('plan', 'request_identity', 'checkpoint_plans', 'checkpoint_requests', 'checkpoints', 'task_bindings', 'case_bindings', 'delivery_artifact'):
                state.pop(key, None)
        save(path, state)
    return status(path)


def elapsed(state, now=None):
    now = time.time() if now is None else now
    wall = max(0, now - state['created_unix'])
    # Merge overlapping waits: two scopes waiting at once consume one wall interval.
    intervals = sorted((g['started_unix'], g.get('resumed_unix') or now) for g in state.get('user_gates', []))
    merged = []
    for start, end in intervals:
        if merged and start <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])
    waiting = sum(max(0, min(end, now) - max(start, state['created_unix'])) for start, end in merged)
    active = sorted((a['started_unix'], a.get('ended_unix') or now) for a in state.get('activity_intervals', []))
    active_merged = []
    for start, end in active:
        if active_merged and start <= active_merged[-1][1]:
            active_merged[-1][1] = max(active_merged[-1][1], end)
        else:
            active_merged.append([start, end])
    waiting -= sum(max(0, min(w_end, a_end, now) - max(w_start, a_start, state['created_unix']))
                   for w_start, w_end in merged for a_start, a_end in active_merged)
    return {'wall_seconds': wall, 'waiting_seconds': waiting, 'active_seconds': max(0, wall - waiting)}


def component_eligible(state, identifier, package):
    declarations = {row['id']: row for row in state['contract'].get('checkpoints', [])}
    if identifier not in declarations:
        raise Invalid('Unknown frozen checkpoint.')
    row = declarations[identifier]
    if any(g.get('resumed_unix') is None and set(g['checks']) & set(row['checks']) for g in state.get('user_gates', [])):
        raise Invalid('Checkpoint is waiting for user authorization.')
    valid = {c['id'] for c in status_checks(state, package) if c['valid']}
    for dependency in row['depends_on']:
        accepted = state.get('checkpoints', {}).get(dependency)
        if not accepted or not set(declarations[dependency]['checks']) <= valid:
            raise Invalid('Checkpoint dependency lacks current accepted evidence: ' + dependency)
    return row


def status_checks(state, package):
    # Use the existing receipt validity logic without inventing a second acceptance gate.
    results = []
    for check in state['contract']['checks']:
        receipt = state['receipts'].get(check['id'])
        try:
            valid = bool(receipt and receipt['dependencies'] == footprint(check, package)
                         and digest(Path(receipt['evidence']).read_bytes()) == receipt['evidence_sha256']
                         and _retained_inputs_valid(receipt))
        except (OSError, Invalid):
            valid = False
        results.append({'id': check['id'], 'valid': valid})
    return results


def checkpoint(path, identifier, package, lessons):
    path = Path(path)
    with locked(path.parent):
        state = read(path)
        _available(state)
        row = component_eligible(state, identifier, package)
        if set(lessons) != set(row['lessons']):
            raise Invalid('Reconcile applicable existing lessons before accepting this checkpoint.')
        valid = {c['id'] for c in status_checks(state, package) if c['valid']}
        if not set(row['checks']) <= valid:
            raise Invalid('Checkpoint is missing focused required evidence.')
        for activity in state.get('activity_intervals', []):
            if activity['checkpoint'] == identifier and activity.get('ended_unix') is None:
                activity['ended_unix'] = time.time()
        state.setdefault('checkpoints', {})[identifier] = {'accepted_unix': time.time(),
            'checks': row['checks'], 'lessons': list(lessons), 'artifact': inventory(package)}
        save(path, state)
    return status(path, package)


def user_wait(path, identifier, checks, reason):
    path = Path(path)
    with locked(path.parent):
        state = read(path)
        _available(state)
        if not reason.strip() or not identifier.strip() or not checks or set(checks) - {c['id'] for c in state['contract']['checks']}:
            raise Invalid('A user gate needs an ID, actual reason and known dependent checks.')
        if any(g['id'] == identifier for g in state.get('user_gates', [])):
            raise Invalid('User gate IDs cannot be reused.')
        state.setdefault('user_gates', []).append({'id': identifier, 'checks': list(checks),
            'reason': reason, 'started_unix': time.time(), 'resumed_unix': None})
        save(path, state)
    return status(path)


def user_resume(path, identifier, authorization):
    if not isinstance(authorization, dict) or set(authorization) != {'origin', 'instruction', 'message_reference'} or authorization['origin'] != 'user' or any(not isinstance(v, str) or not v.strip() for v in authorization.values()):
        raise Invalid('Resume needs the actual user instruction and message reference; quoted source approval cannot release a gate.')
    path = Path(path)
    with locked(path.parent):
        state = read(path)
        matches = [g for g in state.get('user_gates', []) if g['id'] == identifier and g['resumed_unix'] is None]
        if len(matches) != 1:
            raise Invalid('No matching pending user gate.')
        matches[0].update(resumed_unix=time.time(), authorization=authorization)
        save(path, state)
    return status(path)
