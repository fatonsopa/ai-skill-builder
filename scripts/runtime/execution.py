"""Validate declared execution contracts and bind review to loaded instruction bytes.

These checks reject missing links; domain adequacy and host load completeness still
require source-grounded review and actual execution on each claimed host.
"""
from pathlib import Path
import json
import yaml
from .common import Invalid, digest, inside, relative

EVENTS = {'drift', 'revocation', 'late_result', 'lost_return', 'followup'}


def unique(rows, key, label):
    values = [row[key] for row in rows]
    if len(values) != len(set(values)):
        raise Invalid('Duplicate ' + label)
    return set(values)


def check_execution(spec, plan, legacy_paths=()):
    design = plan['execution']
    bindings = design['bindings']
    unique(bindings, 'id', 'input binding')
    if design['file_workflow'] and not bindings:
        raise Invalid('File workflows need origins, roots, access and version bindings.')
    if not design['file_workflow'] and bindings:
        raise Invalid('Non-file workflows cannot declare file bindings.')
    documents = design['document_context']
    unique(documents['sources'], 'id', 'reference document ID')
    if not documents['applicable'] and documents['sources']:
        raise Invalid('Inapplicable document context cannot declare governing sources.')
    roles = design.get('roles', [])
    role_names = {role['id'] for role in roles} if design['mode'] == 'multi' else {'primary'}
    requirement_names = {row['id'] for row in spec['requirements']}
    for source in documents['sources']:
        if not source['roles'] or set(source['roles']) - role_names:
            raise Invalid('Reference documents must route to known responsible roles.')
        if set(source['requirements']) - requirement_names:
            raise Invalid('Reference document maps an unknown requirement.')
        if source['status'] == 'available' and not source['sections']:
            raise Invalid('Available reference documents need assigned sections or criterion IDs.')
        if source['requirements'] and (source['status'] != 'available' or source['authority'] != 'agreed'):
            raise Invalid('Missing, stale, conflicting or unapproved documents cannot establish acceptance requirements.')
    if design['mode'] == 'single':
        if roles or design.get('coverage') or design.get('lifecycle') or design.get('final_owner'):
            raise Invalid('A single-agent design must not hide a multi-role contract.')
        return
    if len(roles) < 2:
        raise Invalid('A multi-agent design needs its lead and at least one executing specialist.')
    names = unique(roles, 'id', 'role ID')
    if design.get('final_owner') not in names:
        raise Invalid('Declare a known final-response owner.')
    resources = {r['path'] for r in plan['resources']} | {'SKILL.md', 'AGENTS.md', 'CLAUDE.md', 'README.md'}
    binding_access = {row['id']: row['access'] for row in bindings}
    layout = json.loads((Path(__file__).resolve().parents[2] / 'config/repository_layout.json').read_text())
    package_roots = set(layout['resource_directories']) | set(layout['required_root_files']) | set(layout['optional_root_files'])
    for role in roles:
        for asset in role['assets']:
            if Path(asset['path']).parts[0] not in package_roots and asset['path'] not in legacy_paths:
                raise Invalid('Host asset has no package root responsibility; keep source assets in allowed resource folders and install host configuration separately: ' + asset['path'])
        for field, access in [('read_roots', 'read'), ('write_roots', 'write')]:
            roots = role['authority'][field]
            if len(roots) != len(set(roots)) or any(binding_access.get(root) != access for root in roots):
                raise Invalid('Role path authority must reference declared binding IDs with matching access.')
        if role['recipient'] not in names | {'user'}:
            raise Invalid('Unknown role recipient: ' + role['id'])
        if role['recipient'] == 'user' and role['id'] != design['final_owner']:
            raise Invalid('Only the final owner may deliver to the user.')
        if role['id'] == design['final_owner'] and role['recipient'] != 'user':
            raise Invalid('The final owner must deliver to the user.')
        if not role['assets']:
            raise Invalid('Every executing role needs an explicit host asset.')
        unique(role['assets'], 'host', 'role host')
        for asset in role['assets']:
            for path in [role['method'], asset['path'], *asset['loaded_paths']]:
                relative(path)
                if path not in resources:
                    raise Invalid('Execution resource is not declared: ' + path)
    # A return chain must terminate at the user, not loop among workers.
    by_role = {r['id']: r for r in roles}
    for role in roles:
        seen, cursor = set(), role['id']
        while cursor != 'user':
            if cursor in seen:
                raise Invalid('Role return route has a cycle.')
            seen.add(cursor)
            cursor = by_role[cursor]['recipient']
    requirements = {r['id'] for r in spec['requirements']}
    coverage = design.get('coverage', [])
    if unique(coverage, 'requirement', 'coverage requirement') != requirements:
        raise Invalid('Map every requirement to roles and cases, including exclusions.')
    cases = {c['id']: c for c in plan['cases']}
    for row in coverage:
        if row['status'] != 'covered':
            raise Invalid('Excluded or unresolved requirements cannot satisfy acceptance; resolve scope before freezing.')
        if not row['roles'] or set(row['roles']) - names or not row['cases'] or set(row['cases']) - cases.keys():
            raise Invalid('Coverage needs known roles and cases.')
        if any(row['requirement'] not in cases[c]['requirements'] for c in row['cases']):
            raise Invalid('Coverage case does not test the mapped requirement.')
    for role in roles:
        assigned = {c for row in coverage if role['id'] in row['roles'] for c in row['cases']}
        if not any(cases[c]['kind'] == 'behavior' and cases[c]['critical'] and cases[c]['semantic'] for c in assigned):
            raise Invalid('Every role needs a critical behavioral task, including the lead.')
    lifecycle = design.get('lifecycle', [])
    if unique(lifecycle, 'event', 'lifecycle event') != EVENTS:
        raise Invalid('Assess drift, revocation, late results, lost returns and follow-ups.')
    for row in lifecycle:
        if set(row['cases']) - cases.keys():
            raise Invalid('Unknown lifecycle case.')
        if row['applicable'] and (not row['cases'] or not any(cases[c]['kind'] != 'behavior' for c in row['cases'])):
            raise Invalid('Applicable lifecycle transitions need executable regression cases.')
        if any(not cases[c]['critical'] for c in row['cases']):
            raise Invalid('Lifecycle checks must be critical.')
        if not row['applicable'] and row['cases']:
            raise Invalid('An inapplicable lifecycle event must not claim test coverage.')


def instruction_bundles(root, plan):
    root = Path(root)
    design = plan['execution']
    if design['mode'] == 'single':
        # Declared single-agent mode still needs a semantic omission review.
        return []
    bundles = []
    for role in design['roles']:
        for asset in role['assets']:
            paths = list(dict.fromkeys([asset['path'], *asset['loaded_paths'], role['method']]))
            files = {}
            for name in paths:
                path = inside(root, name)
                if not path.is_file():
                    raise Invalid('Missing loaded instruction: ' + name)
                files[name] = {'sha256': digest(path.read_bytes()), 'text': path.read_text()}
            # Claude preloading the root skill must expose that entry point for review.
            text = files[asset['path']]['text']
            if asset['host'] == 'claude-code' and text.startswith('---\n'):
                parts = text.split('---\n', 2)
                meta = yaml.safe_load(parts[1]) if len(parts) == 3 else None
                if not isinstance(meta, dict):
                    raise Invalid('Malformed Claude role metadata.')
                tools = meta.get('tools')
                if tools is not None and role['authority']['may_delegate']:
                    allowed = [value.strip() for value in tools.split(',')] if isinstance(tools, str) else tools
                    if not isinstance(allowed, list) or not any(isinstance(value, str) and (value == 'Agent' or value.startswith('Agent(')) for value in allowed):
                        raise Invalid('Claude delegating role explicitly omits the Agent tool; use a parent-dispatch contract or permit supported delegation.')
                if meta.get('skills'):
                    skill_parts = (root / 'SKILL.md').read_text().split('---\n', 2)
                    name = yaml.safe_load(skill_parts[1])['name']
                    if name in meta['skills'] and 'SKILL.md' not in paths:
                        raise Invalid('Claude preloads the root skill but omits it from effective instructions.')
                    if any(value != name for value in meta['skills']):
                        raise Invalid('External preloaded skills need captured local guidance before instruction review.')
            payload = {'role': role['id'], 'host': asset['host'], 'contract': role, 'files': files}
            bundles.append({**payload, 'bundle_sha256': digest(payload)})
    return bundles


def review_execution(root, plan, review):
    bundles = instruction_bundles(root, plan)
    result = review['execution_review']
    rows = result['instruction_reviews']
    expected = {(b['role'], b['host']): b['bundle_sha256'] for b in bundles}
    keys = [(r['role'], r['host']) for r in rows]
    if len(keys) != len(set(keys)) or set(keys) != set(expected):
        raise Invalid('Review each role/host combined instruction bundle exactly once.')
    if any(row['bundle_sha256'] != expected[(row['role'], row['host'])] for row in rows):
        raise Invalid('Combined instruction review is stale.')
    return result['accepted'] and all(row['accepted'] for row in rows)
