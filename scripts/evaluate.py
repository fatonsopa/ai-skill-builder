#!/usr/bin/env python3
"""Portable evaluation runner. Command cases require explicitly reviewed code."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import os
import signal
import subprocess
import sys
import tempfile
import time
import math
import fcntl
from continuation import MAX_EXTENSIONS, extension as routine_extension


def json_hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode="w", dir=path.parent, delete=False) as stream:
        temporary = Path(stream.name)
        json.dump(value, stream, indent=2, ensure_ascii=False)
        stream.write("\n")
    os.replace(temporary, path)


def run_process(command, *, input, cwd, timeout):
    """Bound the whole process group, including children holding output pipes."""
    process = subprocess.Popen(
        command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, cwd=cwd, shell=False, start_new_session=True,
    )
    try:
        stdout, stderr = process.communicate(input=input, timeout=timeout)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        stdout, stderr = process.communicate()
        raise subprocess.TimeoutExpired(command, timeout, output=stdout, stderr=stderr)
    return subprocess.CompletedProcess(command, process.returncode, stdout, stderr)


from repository_files import inventory as hash_tree, copy_repository as copy_package



def metrics(attempts, planned):
    valid = [item for item in attempts if item["status"] in {"passed", "failed", "pending_review"}]
    accepted = sum(item["status"] == "passed" for item in valid)
    return {
        "planned": planned, "evaluated": len(valid), "accepted": accepted,
        "task_success_percent": 100 * accepted / len(valid) if valid else None,
        "coverage_percent": 100 * len(valid) / planned if planned else None,
        "critical_failures": sum(
            item.get("critical", False) and item["status"] == "failed" for item in attempts
        ),
        "unresolved_critical": sum(
            item.get("critical", False) and item["status"] not in {"passed", "failed"} for item in attempts
        ),
        "infrastructure_failures": sum(item["status"] == "infrastructure_failure" for item in attempts),
        "pending_review": sum(item["status"] == "pending_review" for item in attempts),
    }



def grade_process(trace, expected):
    """Check captured stages. Ordering is mechanical; evidence meaning needs review."""
    errors, observed = [], []
    allowed_provenance = {"authored_control", "historical_replay", "instrumented_execution", "host_observation"}
    provenance = trace.get("provenance") if isinstance(trace, dict) else None
    if not isinstance(provenance, dict) or provenance.get("kind") not in allowed_provenance or not isinstance(provenance.get("source"), str) or not provenance["source"].strip():
        errors.append("Identify trace provenance and its actual source; do not imply a fresh model run.")
    events = trace.get("events") if isinstance(trace, dict) else None
    if not isinstance(events, list) or not events:
        errors.append("A process check needs actual stage events, not just a final output or success flag.")
        events = []
    for event in events:
        if not isinstance(event, dict) or not isinstance(event.get("phase"), str) or not event["phase"].strip():
            errors.append("Malformed process event.")
            continue
        phase = event["phase"]
        observed.append(phase)
        if phase in expected["visible"] and event.get("visible") is not True:
            errors.append("Required user-visible handoff is missing: " + phase)
        if phase in expected["evidence"] and (not isinstance(event.get("evidence"), str) or not event["evidence"].strip()):
            errors.append("Missing stage evidence: " + phase)
    if observed != expected["order"]:
        errors.append("Process phases were omitted, reordered, repeated or undeclared; expected " + repr(expected["order"]) + ", observed " + repr(observed))
    return {"passed": not errors, "failures": errors, "observed_order": observed,
            "provenance": provenance, "trace": trace,
            "limits": "Checks recorded event order and declared evidence/visibility. Review actual artifacts and host observations for truth and completeness; authored controls and replay are not fresh model behavior."}


def process_metrics(attempts, suite):
    selected = {case["id"] for case in suite if case.get("workflow")}
    rows = [row for row in attempts if row["id"] in selected]
    valid = [row for row in rows if row["status"] in {"passed", "failed", "pending_review"}]
    accepted = sum(row["status"] == "passed" for row in valid)
    return {"planned": len(selected), "evaluated": len(valid), "accepted": accepted,
            "success_percent": 100 * accepted / len(valid) if valid else None,
            "coverage_percent": 100 * len(valid) / len(selected) if selected else None,
            "trace_checks": sum("process" in row for row in rows),
            "trace_failures": sum(row.get("process", {}).get("passed") is False for row in rows),
            "pending_review": sum(row["status"] == "pending_review" for row in rows),
            "limits": "Declared workflow-case results; not universal skill accuracy or proof of unobserved model behavior."}


def behavior_packet(package, case):
    """Inputs for a fresh performing context; expected answers are excluded."""
    package = Path(package).resolve()
    resources = {}
    for name in case.get("resources", []):
        path = (package / name).resolve()
        if not path.is_relative_to(package) or not path.is_file():
            raise ValueError("Behavioral resource is missing or outside the package: " + name)
        relative = path.relative_to(package)
        if relative.parts[0] in {'evals', 'tests', 'tools'} or relative.suffix == '.py' and (relative.name.startswith('test_') or relative.name.endswith('.test.py')):
            raise ValueError('Performing resources cannot include evaluation answers or development controls: ' + name)
        resources[name] = path.read_text()
    return {"case_id": case["id"], "case_sha256": json_hash(case), "package_hashes": hash_tree(package),
            "request": case["request"], "skill": (package / "SKILL.md").read_text(), "resources": resources,
            "role": "performing_agent", "instructions": "Use the actual skill for this task in a fresh context. Capture public messages, tool calls and artifacts. Do not claim tools ran when unavailable. Return the requested result; this packet does not contain the grader's expected answer."}


def observation_for(package, case, observations):
    """Bind imported performing-model evidence to the exact case and skill bytes."""
    if not observations:
        return None
    if not isinstance(observations, dict) or observations.get("package_hashes") != hash_tree(package):
        raise ValueError("Behavior observations belong to another skill version.")
    records = observations.get("observations", [])
    if not isinstance(records, list) or any(not isinstance(row, dict) for row in records):
        raise ValueError("Behavior observations must contain a list of captured records.")
    matches = [row for row in records if row.get("case_id") == case["id"]]
    if not matches:
        return None
    if len(matches) != 1:
        raise ValueError("Duplicate behavioral observations for one case.")
    row = matches[0]
    provenance = row.get("provenance", {})
    if row.get("case_sha256") != json_hash(case):
        raise ValueError("Behavior observation belongs to a different frozen input/case.")
    if not isinstance(provenance, dict) or provenance.get("kind") not in {"host_observation", "provider_cli"} or not isinstance(provenance.get("source"), str) or not provenance["source"].strip() or not isinstance(provenance.get("host"), str) or not provenance["host"].strip() or "model" not in provenance or (provenance["model"] is not None and (not isinstance(provenance["model"], str) or not provenance["model"].strip())):
        raise ValueError("Behavior tests require actual model observations with host/model/source provenance; controls and historical replay do not qualify.")
    if "output" not in row:
        raise ValueError("Behavior observation has no actual output.")
    if "execution_status" in row and row["execution_status"] != "completed":
        raise ValueError("The captured AI task did not complete successfully: " + str(row["execution_status"]))
    return row


def check_case(package, case, allow_exec, remaining=None, observations=None):
    result = {
        "id": case["id"], "critical": case["critical"],
        "status": "failed", "failures": [], "stdout": "", "stderr": "",
        "requirements": case["requirements"], "semantic": case["semantic"],
        "workflow": case.get("workflow"),
    }
    expected = case["expect"]
    exit_code = 0
    if case["kind"] == "behavior":
        try:
            observation = observation_for(package, case, observations)
        except (ValueError, TypeError, KeyError) as error:
            result["failures"].append(str(error))
            return result
        if observation is None:
            result.update(status="not_run", failures=["Run the actual AI task and capture its behavior; mechanical passes are not behavioral evidence."])
            return result
        output = observation["output"]
        result["stdout"] = output if isinstance(output, str) else json.dumps(output, ensure_ascii=False)
        result["observation"] = observation
    if case["kind"] == "command":
        if not allow_exec:
            result.update(status="not_run", failures=["Command execution requires --allow-exec after code review."])
            return result
        command = [sys.executable if part == "{python}" else part for part in case["command"]]
        raw_input = case.get("stdin", "")
        raw_input = raw_input if isinstance(raw_input, str) else json.dumps(raw_input, ensure_ascii=False)
        try:
            timeout = case.get("timeout_seconds", 30)
            process = run_process(command, input=raw_input, cwd=package, timeout=min(timeout, remaining) if remaining is not None else timeout)
            exit_code = process.returncode
            result.update(stdout=process.stdout, stderr=process.stderr)
        except subprocess.TimeoutExpired:
            result["failures"].append("Task exceeded its time limit.")
            return result
        except OSError as error:
            result.update(status="infrastructure_failure", failures=[str(error)])
            return result
    if exit_code != expected["exit_code"]:
        result["failures"].append(f"Exit code {exit_code}; expected {expected['exit_code']}.")
    if "stdout_text" in expected and result["stdout"] != expected["stdout_text"]:
        result["failures"].append("Standard output differs from the required literal.")
    if "stdout_json" in expected:
        try:
            if json.loads(result["stdout"]) != expected["stdout_json"]:
                result["failures"].append("JSON output differs from the expected value.")
        except (ValueError, TypeError):
            result["failures"].append("Standard output is not valid JSON.")
    literal_target = result["stdout"]
    if case["kind"] == "artifact" and "file" in expected:
        artifact = (package / expected["file"]).resolve()
        if artifact.is_relative_to(package.resolve()) and artifact.is_file():
            try:
                literal_target = artifact.read_text()
            except (UnicodeError, OSError):
                result["failures"].append("Artifact literal checks require readable text.")
    for literal in expected.get("contains", []):
        if literal not in literal_target:
            result["failures"].append(f"Missing required literal in output: {literal!r}.")
    if "file" in expected:
        path = (package / expected["file"]).resolve()
        if not path.is_relative_to(package.resolve()) or not path.is_file():
            result["failures"].append("Expected output file is missing or outside the package.")
        elif "file_json" in expected:
            try:
                if json.loads(path.read_text()) != expected["file_json"]:
                    result["failures"].append("File JSON differs from the expected value.")
            except (ValueError, OSError):
                result["failures"].append("Expected file is not readable JSON.")
    if "process" in expected:
        contract = expected["process"]
        try:
            if "trace_file" in contract:
                path = (package / contract["trace_file"]).resolve()
                if not path.is_relative_to(package.resolve()) or not path.is_file():
                    raise ValueError("The process trace must be a captured file inside the evaluated package.")
                trace = json.loads(path.read_text())
            else:
                trace = result.get("observation", {}).get("trace") if case["kind"] == "behavior" else json.loads(result["stdout"])
            result["process"] = grade_process(trace, contract)
            result["failures"].extend(result["process"]["failures"])
        except (OSError, ValueError, TypeError) as error:
            result["process"] = {"passed": False, "failures": ["Missing or malformed process trace: " + str(error)]}
            result["failures"].extend(result["process"]["failures"])
    if not result["failures"]:
        result["status"] = "pending_review" if case["semantic"] else "passed"
    return result


def evaluate(package, suite, allow_exec=False, max_seconds=None, observations=None):
    package = Path(package).resolve()
    suite_hash = hashlib.sha256(json.dumps(suite, sort_keys=True).encode()).hexdigest()
    original = hash_tree(package)
    attempts = []
    started = time.monotonic()
    with tempfile.TemporaryDirectory(prefix="skill-eval-") as folder:
        # Each case starts from the same exported package; effects cannot leak between cases.
        for index, case in enumerate(suite):
            remaining = max_seconds - (time.monotonic() - started) if max_seconds is not None else None
            if remaining is not None and remaining <= 0:
                attempts.append({
                    "id": case["id"], "critical": case["critical"], "status": "not_run",
                    "semantic": case["semantic"], "requirements": case["requirements"],
                    "failures": ["Run execution allowance exhausted."], "stdout": "", "stderr": "",
                })
                continue
            work = Path(folder) / str(index)
            copy_package(package, work)
            attempts.append(check_case(work, case, allow_exec, remaining, observations))
    return {
        "schema_version": 1, "mode": "fresh_processes" if allow_exec else "mechanical_only",
        "suite_sha256": suite_hash, "package_hashes": original,
        "elapsed_seconds": time.monotonic() - started,
        "attempts": attempts, "metrics": metrics(attempts, len(suite)),
        "process_metrics": process_metrics(attempts, suite),
        "mechanical_metrics": metrics([row for row in attempts if row["id"] in {case["id"] for case in suite if case["kind"] != "behavior"}], sum(case["kind"] != "behavior" for case in suite)),
        "behavioral_metrics": metrics([row for row in attempts if row["id"] in {case["id"] for case in suite if case["kind"] == "behavior"}], sum(case["kind"] == "behavior" for case in suite)),
        "execution_boundary": "Disposable working directory; not an operating-system sandbox.",
    }


def maintenance(package, directory, suite, allow_exec=False, review=None, extension=None, export=None, observations=None):
    """A child skill can maintain itself without a provider CLI or installed builder."""
    package, directory = Path(package).resolve(), Path(directory).resolve()
    if directory.is_relative_to(package) or package.is_relative_to(directory):
        raise ValueError("Maintenance records must be outside the candidate.")
    directory.mkdir(parents=True, exist_ok=True)
    with (directory / ".lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        state_path = directory / "state.json"
        files = hash_tree(package)
        if state_path.exists():
            state = json.loads(state_path.read_text())
            if json_hash(state["suite"]) != state["suite_sha256"]:
                raise ValueError("Frozen maintenance cases changed.")
            if json_hash({
                "suite": state["suite"], "target": state["policy"]["target_success_percent"],
                "allowed": state["policy"]["allowed_candidate_paths"],
            }) != state["objective_sha256"]:
                raise ValueError("Frozen maintenance objective changed.")
        else:
            policy = json.loads((package / "config/host_policy.json").read_text()).get("maintenance")
            if not policy:
                raise ValueError("Package needs a declared maintenance policy.")
            state = {
                "schema_version": 1, "suite": suite, "suite_sha256": json_hash(suite),
                "policy": policy, "initial_files": files, "attempts": [],
                "elapsed_seconds": 0, "best": None, "status": "active",
                "extensions": [],
                "stagnant_attempts": 0,
            }
            state["objective_sha256"] = json_hash({
                "suite": suite, "target": policy["target_success_percent"],
                "allowed": policy["allowed_candidate_paths"],
            })
            copy_package(package, directory / "baseline")
        if extension:
            if state["status"] == "target_met":
                raise ValueError("Target already met.")
            repeated = any(all(row.get(key) == value for key, value in extension.items()) for row in state["extensions"])
            if not repeated:
                receipt = routine_extension(state["extensions"], {"attempts": extension["iterations"], "seconds": extension["seconds"]}, extension["authorization_note"],
                    current={"attempts": state["policy"]["max_experiments"], "seconds": state["policy"]["max_seconds"]}, hard_limits=state["policy"].get("hard_limits"),
                    stalled=state["stagnant_attempts"] >= state["policy"].get("max_stagnant_experiments", 3))
                state["policy"]["max_experiments"] += extension["iterations"]
                state["policy"]["max_seconds"] += extension["seconds"]
                state["extensions"].append({**extension, **receipt})
            write_json(state_path, state)
            return state
        if export:
            if state["status"] != "target_met" or not state["best"]:
                raise ValueError("No accepted version is ready for export.")
            destination = Path(export).resolve()
            if destination.exists() or destination.is_relative_to(directory) or destination.is_relative_to(package):
                raise ValueError("Export needs a new destination outside the candidate and records.")
            if hash_tree(directory / state["best"]["copy"]) != state["best"]["files"]:
                raise ValueError("Accepted version changed before export.")
            copy_package(directory / state["best"]["copy"], destination)
            return {"status": "exported", "destination": str(destination), "files": hash_tree(destination)}
        if state["status"] == "target_met":
            return state
        differences = {
            name for name in state["initial_files"].keys() | files.keys()
            if state["initial_files"].get(name) != files.get(name)
        }
        if differences - set(state["policy"]["allowed_candidate_paths"]):
            raise ValueError("Candidate changed outside the frozen maintenance surface.")
        if review:
            if not state["attempts"] or state["status"] != "awaiting_review":
                raise ValueError("No observation is awaiting semantic review.")
            record = state["attempts"][-1]
            report_path = directory / record["report"]
            report = json.loads(report_path.read_text())
            if review.get("report_sha256") != json_hash(report) or files != report["package_hashes"]:
                raise ValueError("Review is stale or candidate changed.")
            labels = review.get("cases", [])
            pending = {row["id"] for row in report["attempts"] if row["status"] == "pending_review"}
            if len({row["id"] for row in labels}) != len(labels) or {row["id"] for row in labels} != pending:
                raise ValueError("Review every pending case exactly once.")
            if review.get("reviewer", {}).get("kind") not in {"human", "model"}:
                raise ValueError("Identify the reviewer and provenance.")
            by_id = {row["id"]: row for row in labels}
            for row in report["attempts"]:
                if row["id"] in by_id:
                    label = by_id[row["id"]]
                    if not isinstance(label.get("accepted"), bool) or not label.get("rationale"):
                        raise ValueError("Each review needs a verdict and rationale.")
                    row["status"] = "passed" if label["accepted"] else "failed"
                    row["review"] = {"reviewer": review["reviewer"], **label}
            report["metrics"] = metrics(report["attempts"], len(state["suite"]))
            report["process_metrics"] = process_metrics(report["attempts"], state["suite"])
            for layer, behavior in (("mechanical_metrics", False), ("behavioral_metrics", True)):
                ids = {case["id"] for case in state["suite"] if (case["kind"] == "behavior") == behavior}
                report[layer] = metrics([row for row in report["attempts"] if row["id"] in ids], len(ids))
            write_json(directory / record["review"], {"judgment": review, "graded_report": report})
        else:
            refresh = observations is not None and bool(state["attempts"]) and state["attempts"][-1]["files"] == files
            if state["status"] == "awaiting_review" and not refresh:
                raise ValueError("Finish the pending review or import bound observations for the unchanged candidate.")
            remaining = state["policy"]["max_seconds"] - state["elapsed_seconds"]
            experiments = sum(not row.get("evidence_refresh", False) for row in state["attempts"])
            if (not refresh and experiments >= state["policy"]["max_experiments"]) or remaining <= 0 or state["stagnant_attempts"] >= state["policy"].get("max_stagnant_experiments", 3):
                state.update(
                    status="needs_continuation",
                    proposal={
                        "ask_user": False, "extra_iterations": 2,
                        "extra_seconds": min(900, max(60, math.ceil(state["elapsed_seconds"] / max(1, len(state["attempts"])) * 2))),
                        "basis": "Observed results and execution time; host-model time is not measured.",
                        "automatic_extension": state["stagnant_attempts"] < state["policy"].get("max_stagnant_experiments", 3) and sum(row.get("automatic") is True for row in state["extensions"]) < MAX_EXTENSIONS,
                        "stagnant_attempts": state["stagnant_attempts"],
                    },
                )
                try:
                    routine_extension(state['extensions'], {'attempts': state['proposal']['extra_iterations'], 'seconds': state['proposal']['extra_seconds']}, 'Continue the same validation task after inspecting its recorded failures.',
                        current={'attempts': state['policy']['max_experiments'], 'seconds': state['policy']['max_seconds']}, hard_limits=state['policy'].get('hard_limits'),
                        stalled=state['stagnant_attempts'] >= state['policy'].get('max_stagnant_experiments', 3))
                except ValueError as error:
                    state['proposal'].update(automatic_extension=False, reason=str(error))
                write_json(state_path, state)
                return state
            report = evaluate(package, state["suite"], allow_exec, remaining, observations)
            index = len(state["attempts"])
            record = {"report": f"attempts/{index:03}.json", "review": f"attempts/{index:03}-review.json", "files": files, "evidence_refresh": refresh}
            state["attempts"].append(record)
            state["elapsed_seconds"] += report["elapsed_seconds"]
            write_json(directory / record["report"], report)
        score = report["metrics"]
        record["metrics"] = score
        if score["pending_review"]:
            state["status"] = "awaiting_review"
        elif score["coverage_percent"] < 100:
            # Retain incomplete checks without treating absent behavior as failed tuning.
            state["status"] = "awaiting_observations"
        else:
            valid = score["coverage_percent"] == 100 and not score["critical_failures"]
            better = not state["best"] or score["task_success_percent"] > state["best"]["metrics"]["task_success_percent"]
            if valid and better:
                copy = f"versions/{len(state['attempts']) - 1:03}"
                copy_package(package, directory / copy)
                state["best"] = {"copy": copy, "files": files, "metrics": score}
                state["stagnant_attempts"] = 0
            else:
                state["stagnant_attempts"] += 1
            target_met = state["best"] and state["best"]["metrics"]["task_success_percent"] >= state["policy"]["target_success_percent"]
            state["status"] = "target_met" if target_met else "active"
            record["keep"] = bool(valid and better)
        write_json(state_path, state)
        return state


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", type=Path, required=True)
    parser.add_argument("--suite", type=Path)
    parser.add_argument("--case", action="append", help="Run only these exact frozen case IDs.")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--behavior-packet", help="Export one performing-agent task without expected answers.")
    parser.add_argument("--observations", type=Path, help="Captured fresh AI behavior, bound to case and artifact hashes.")
    parser.add_argument("--allow-exec", action="store_true")
    parser.add_argument("--session", type=Path, help="Bounded local maintenance records outside the package.")
    parser.add_argument("--review", type=Path)
    parser.add_argument("--extra-iterations", type=int, default=0)
    parser.add_argument("--extra-seconds", type=int, default=0)
    parser.add_argument("--reason", "--authorization-note", dest="authorization_note", default="", help="Reason for a bounded retry within the current task.")
    parser.add_argument("--export-best", type=Path)
    args = parser.parse_args()
    suite = json.loads((args.suite or args.package / "evals/cases.json").read_text())
    if args.behavior_packet:
        matches = [case for case in suite if case["id"] == args.behavior_packet and case["kind"] == "behavior"]
        if len(matches) != 1:
            parser.error("Select one declared behavioral case.")
        print(json.dumps(behavior_packet(args.package, matches[0]), indent=2))
        return 0
    if args.case:
        known = {case["id"] for case in suite}
        if set(args.case) - known:
            parser.error("Unknown selected case ID.")
        suite = [case for case in suite if case["id"] in args.case]
    extension = None
    if args.extra_iterations or args.extra_seconds or args.authorization_note:
        extension = {"iterations": args.extra_iterations, "seconds": args.extra_seconds, "authorization_note": args.authorization_note}
    report = maintenance(
        args.package, args.session, suite, args.allow_exec,
        json.loads(args.review.read_text()) if args.review else None, extension, args.export_best,
        observations=json.loads(args.observations.read_text()) if args.observations else None,
    ) if args.session else evaluate(args.package, suite, args.allow_exec, observations=json.loads(args.observations.read_text()) if args.observations else None)
    rendered = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        args.output.write_text(rendered)
    else:
        print(rendered, end="")
    if args.session:
        return 0 if report["status"] in {"target_met", "exported"} else 1
    return 0 if report["metrics"]["accepted"] == len(suite) else 1


if __name__ == "__main__":
    sys.exit(main())
