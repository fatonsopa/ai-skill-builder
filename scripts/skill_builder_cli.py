#!/usr/bin/env python3
"""Create and maintain skills through recorded, checked stages."""
import argparse
import json
from pathlib import Path
import sys
import tempfile
import shutil

from runtime import contracts, workflow, completion
from runtime.artifacts import check_package
from runtime.common import Invalid, load, locked, save
from runtime.examples import ingest
from runtime.hosts import route
from repository_files import compare_installation


def parser():
    result = argparse.ArgumentParser(description=__doc__)
    commands = result.add_subparsers(dest="command", required=True)
    policy = commands.add_parser('completion-init', help='Freeze one objective-wide scope, check list and cumulative budget.')
    policy.add_argument('--workspace', type=Path, required=True)
    policy.add_argument('--definition', type=Path, required=True)
    for name in ('completion-status', 'completion-record-check', 'completion-record-hosts', 'completion-finding', 'completion-amend', 'completion-delivered'):
        item = commands.add_parser(name)
        item.add_argument('--policy', type=Path, required=True)
        item.add_argument('--package', type=Path)
        if name == 'completion-record-check':
            item.add_argument('--check', required=True)
            item.add_argument('--evidence', type=Path, required=True)
        if name == 'completion-record-hosts':
            item.add_argument('--manifest', type=Path, required=True)
        if name == 'completion-amend':
            item.add_argument('--definition', type=Path, required=True)
            item.add_argument('--authority', required=True)
        if name == 'completion-finding':
            item.add_argument('--classification', choices=['blocker', 'follow_up', 'scope_change'], required=True)
            item.add_argument('--requirement', default='')
            item.add_argument('--text', required=True)
            item.add_argument('--check', action='append', default=[])
    documents = commands.add_parser("validate-documents", help="Accept every changed document through Technical Writer.")
    documents.add_argument("--run", type=Path, required=True)
    documents.add_argument("--manifest", type=Path, required=True)
    start = commands.add_parser("start", help="Capture a request and source snapshot.")
    start.add_argument("--request", type=Path, required=True)
    start.add_argument("--run", type=Path, required=True)
    for name in ["status", "packet", "recover", "replay", "budget"]:
        item = commands.add_parser(name)
        item.add_argument("--run", type=Path, required=True)
    submit = commands.add_parser("submit")
    submit.add_argument("--run", type=Path, required=True)
    submit.add_argument("--response", type=Path, required=True)
    evaluate = commands.add_parser("evaluate")
    evaluate.add_argument("--run", type=Path, required=True)
    evaluate.add_argument("--allow-exec", action="store_true", help="Execute reviewed candidate code; this is not a sandbox.")
    evaluate.add_argument("--baseline", action="store_true")
    evaluate.add_argument("--observations", type=Path, help="Actual performing-model observations bound to this candidate and cases.")
    revise = commands.add_parser("revise")
    revise.add_argument("--run", type=Path, required=True)
    revise.add_argument("--hypothesis", required=True)
    apply = commands.add_parser("apply")
    apply.add_argument("--run", type=Path, required=True)
    apply.add_argument("--destination", type=Path)
    layout = commands.add_parser("layout", help="Inspect the canonical repository structure and recommended moves.")
    layout.add_argument("--package", type=Path, required=True)
    check = commands.add_parser("check")
    check.add_argument("--package", type=Path, required=True)
    check.add_argument("--legacy", action="store_true")
    installation = commands.add_parser("check-installation", help="Compare the active installation with its reviewed source.")
    installation.add_argument("--package", type=Path, required=True)
    installation.add_argument("--installed", type=Path, required=True)
    schema = commands.add_parser("schema")
    schema.add_argument("phase", choices=["request", 'completion', *contracts.PHASES])
    trace = commands.add_parser("check-process", help="Grade captured workflow stages separately from final output.")
    trace.add_argument("--trace", type=Path, required=True)
    trace.add_argument("--expect", type=Path, required=True)
    feedback = commands.add_parser("feedback")
    feedback.add_argument("--run", type=Path, required=True)
    feedback.add_argument("--text", required=True)
    feedback.add_argument("--maintenance", action="store_true")
    examples = commands.add_parser("examples")
    examples.add_argument("--manifest", type=Path, required=True)
    examples.add_argument("--output", type=Path, required=True)
    model = commands.add_parser("model")
    model.add_argument("--run", type=Path, required=True)
    model.add_argument("--provider", choices=["host", "codex", "claude"], default="host")
    model.add_argument("--model")
    close = commands.add_parser("resolve-feedback")
    close.add_argument("--run", type=Path, required=True)
    close.add_argument("--id", required=True)
    close.add_argument("--classification", required=True)
    close.add_argument("--resolution-run", type=Path, required=True)
    close.add_argument("--case", required=True)
    benchmark = commands.add_parser("benchmark")
    benchmark.add_argument("--config", type=Path, required=True)
    benchmark.add_argument("--output", type=Path, required=True)
    grade = commands.add_parser("grade")
    grade.add_argument("--report", type=Path, required=True)
    grade.add_argument("--reviews", type=Path, required=True)
    extend = commands.add_parser("extend")
    extend.add_argument("--run", type=Path, required=True)
    extend.add_argument("--iterations", type=int, default=0)
    extend.add_argument("--seconds", type=int, default=0)
    extend.add_argument("--invocations", type=int, default=0)
    extend.add_argument("--reason", "--authorization-note", dest="authorization_note", required=True, help="Concrete reason for a bounded retry within the authorized task.")
    package = commands.add_parser("package")
    package.add_argument("--run", type=Path, required=True)
    package.add_argument("--package", type=Path, required=True)
    package.add_argument("--output", type=Path, required=True)
    package.add_argument("--version", default="0.2.0")
    readme = commands.add_parser("readme")
    readme.add_argument("--package", type=Path, required=True)
    readme.add_argument("--check", action="store_true")
    return result


def replay(root):
    """Rebuild recorded artifacts without model calls, commands, or live application."""
    from runtime.common import digest, validate
    state = workflow.read_state(root)
    previous = None
    events = Path(root) / "events.jsonl"
    for line in events.read_text().splitlines():
        item = json.loads(line)
        stored = item.pop("sha256")
        if item["previous"] != previous or digest(item) != stored:
            raise Invalid("Event chain is inconsistent.")
        previous = stored
    responses = []
    for path in sorted((Path(root) / "responses").glob("*.json")):
        response = load(path)
        validate(response, contracts.response_schema(response["phase"], state.get("protocol_version", 1)))
        if response["run_id"] != state["run_id"] or digest(response) not in state["accepted_responses"]:
            raise Invalid("Captured response does not match the recorded run.")
        responses.append({"phase": response["phase"], "sha256": digest(response)})
    if [item["sha256"] for item in responses] != state["accepted_responses"]:
        raise Invalid("Response records are missing or out of order.")
    with tempfile.TemporaryDirectory(prefix="skill-replay-") as temporary:
        target = Path(temporary) / "run"
        request = dict(state["request"])
        if request.get("source"):
            request["source"] = str((Path(root) / "baseline").resolve())
        workflow.start(target, request, protocol_version=state.get("protocol_version", 1), replay_only=True)
        for path in sorted((Path(root) / "responses").glob("*.json")):
            original = load(path)
            current_state = workflow.read_state(target)
            if original["phase"] == "produce" and current_state["phase"] != "produce":
                workflow.revise(target, "Replay of recorded experiment.")
            if original["phase"] == "review":
                current_state = workflow.read_state(target)
                archive = Path(root) / "packets" / (original["packet_sha256"] + ".json")
                captured = load(archive) if archive.is_file() else None
                if captured is None and state.get("evaluation_record"):
                    raise Invalid("Archived review packet is missing.")
                if captured is not None:
                    actual = digest({key: value for key, value in captured.items() if key != "packet_sha256"})
                    if actual != original["packet_sha256"] or captured.get("packet_sha256") != actual:
                        raise Invalid("Archived review packet changed.")
                report = captured.get("evaluation") if captured else None
                if report is None:
                    report = load(Path(root) / "evaluations" / f"{current_state['experiment']:03}.json")
                package = target / "candidate"
                actual_files = workflow.inventory(package)
                if actual_files != report["package_hashes"]:
                    changed = sorted(name for name in set(actual_files) | set(report["package_hashes"]) if actual_files.get(name) != report["package_hashes"].get(name))
                    raise Invalid("Replayed artifacts differ from captured evaluation inputs: " + repr(changed))
                current_state.update(
                    replay_only=True, technical_writer=state["technical_writer"],
                    document_validation=captured.get("document_validation") if captured else None,
                    evaluation=report,
                    package_check=check_package(package, full=request["operation"] in {"create", "rebuild"}, structure=request.get("repair_structure", False)),
                    phase="review", status="awaiting_ai",
                )
                save(target / "state.json", current_state)
            current_packet = workflow.packet(target)
            adapted = {
                **original, "run_id": current_packet["run_id"],
                "packet_sha256": current_packet["packet_sha256"],
            }
            workflow.submit(target, adapted)
        rebuilt = workflow.read_state(target)
        files = workflow.inventory(target / "candidate")
    return {
        "run_id": state["run_id"], "responses": responses,
        "objective_sha256": state.get("objective_sha256"),
        "mode": "mechanical_replay", "fresh_model_calls": 0, "live_side_effects": 0,
        "rebuilt_files": files, "rebuilt_status": rebuilt["status"],
        "note": "Regenerates artifacts from captured AI responses; evaluation observations are replayed, not new measurements. Delivery is not repeated.",
    }


def state_summary(state, root):
    """Keep full evidence on disk; repeated lifecycle output needs only progress."""
    result = {key: state[key] for key in ('run_id', 'phase', 'status', 'experiment', 'objective_sha256', 'elapsed_seconds', 'model_invocations', 'evaluation_record', 'baseline_evaluation_record', 'delivered', 'last_decision') if key in state}
    result.update(run=str(Path(root).resolve()), state_file=str((Path(root) / 'state.json').resolve()), operation=state['request']['operation'])
    if state.get('completion'):
        package = Path(root) / 'candidate'
        if not package.exists():
            package = Path(completion.read(state['completion']['path'])['contract']['project'])
        result['completion_policy'] = completion.status(state['completion']['path'], package)
    if state.get('evaluation'):
        for name in ('metrics', 'mechanical_metrics', 'behavioral_metrics', 'process_metrics'):
            if name in state['evaluation']:
                result[name] = state['evaluation'][name]
    if state.get('document_check'):
        result['document_check'] = state['document_check']
    if state.get('package_check'):
        result['package_check'] = {key: state['package_check'][key] for key in ('passed', 'findings')}
    return result


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        if args.command == 'completion-init':
            value = completion.create(args.workspace, load(args.definition))
        elif args.command.startswith('completion-'):
            package = args.package or Path(completion.read(args.policy)['contract']['project'])
            if args.command == 'completion-status':
                value = completion.status(args.policy, package)
            elif args.command == 'completion-record-check':
                value = completion.record(args.policy, args.check, package, args.evidence)
            elif args.command == 'completion-record-hosts':
                value = completion.record_hosts(args.policy, package, args.manifest)
            elif args.command == 'completion-amend':
                value = completion.amend(args.policy, load(args.definition), args.authority)
            elif args.command == 'completion-finding':
                value = completion.finding(args.policy, args.classification, args.requirement, args.text, args.check)
            else:
                value = completion.delivered(args.policy, package)
        elif args.command == "check-process":
            from evaluate import grade_process
            from runtime.common import validate
            expected = load(args.expect)
            validate(expected, contracts.PROCESS)
            value = grade_process(load(args.trace), expected)
        elif args.command == "layout":
            from repository_layout import check as inspect_layout
            value = inspect_layout(args.package)
        elif args.command == "check":
            value = check_package(args.package, full=not args.legacy)
        elif args.command == "check-installation":
            value = compare_installation(args.package, args.installed)
        elif args.command == "readme":
            from runtime.readme import check as check_readme, write as write_readme
            if not args.check:
                write_readme(args.package)
            value = check_readme(args.package)
        elif args.command == "schema":
            value = contracts.REQUEST if args.phase == "request" else completion.CONTRACT if args.phase == 'completion' else contracts.response_schema(args.phase)
        elif args.command == "examples":
            value = ingest(args.manifest, args.output)
        elif args.command == "benchmark":
            from runtime.benchmark import benchmark
            value = benchmark(args.config, args.output)
        elif args.command == "grade":
            from runtime.benchmark import grade
            value = grade(args.report, args.reviews)
        elif args.command == "package":
            from runtime.delivery import package
            with locked(args.run):
                value = package(args.package, args.output, version=args.version, run=args.run)
        else:
            with locked(args.run):
                if args.command == "start":
                    value = workflow.start(args.run, load(args.request))
                elif args.command == "status":
                    value = workflow.read_state(args.run)
                elif args.command == "packet":
                    value = workflow.packet(args.run)
                elif args.command == "validate-documents":
                    from runtime.technical_writer import validate_documents
                    value = validate_documents(args.run, args.manifest)
                elif args.command == "submit":
                    value = workflow.submit(args.run, load(args.response))
                elif args.command == "evaluate":
                    value = workflow.run_evaluation(args.run, args.allow_exec, args.baseline, args.observations)
                elif args.command == "revise":
                    value = workflow.revise(args.run, args.hypothesis)
                elif args.command == "apply":
                    value = workflow.apply(args.run, args.destination)
                elif args.command == "recover":
                    value = workflow.recover(args.run)
                elif args.command == "feedback":
                    value = workflow.feedback(args.run, args.text, args.maintenance)
                elif args.command == "replay":
                    value = replay(args.run)
                elif args.command == "model":
                    if args.provider == "host":
                        state = workflow.read_state(args.run)
                        value = {"status": "host_handoff", "route": route(state["request"].get("host")), "packet": workflow.packet(args.run)}
                    else:
                        from runtime.adapters import invoke
                        value = invoke(args.run, args.provider, args.model)
                elif args.command == "resolve-feedback":
                    value = workflow.resolve_feedback(args.run, args.id, args.classification, args.resolution_run, args.case)
                elif args.command == "budget":
                    value = workflow.budget(args.run)
                elif args.command == "extend":
                    value = workflow.extend_budget(args.run, args.iterations, args.seconds, args.invocations, args.authorization_note)
        if args.command not in {'packet', 'model', 'schema'} and isinstance(value, dict) and {'request', 'run_id', 'phase', 'status'} <= set(value):
            value = state_summary(value, args.run)
        print(json.dumps(value, ensure_ascii=False, indent=2))
        if args.command in {"check", "readme", "check-process", "check-installation"} and not value["passed"]:
            return 1
        if args.command == "model" and value["status"] not in {"response_validated", "host_handoff"}:
            return 1
        return 0
    except (Invalid, OSError, ValueError, KeyError) as error:
        print(json.dumps({"error": str(error), "type": type(error).__name__}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
