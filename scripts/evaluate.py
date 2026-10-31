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


def distribution(root, profile="source"):
    path = Path(root) / "distribution.json"
    if path.is_symlink():
        raise ValueError("Distribution manifest must not be a symbolic link.")
    if not path.is_file():
        return None
    data = json.loads(path.read_text())
    if data.get("schema_version") != 1 or profile not in data.get("profiles", {}):
        raise ValueError("Unsupported distribution manifest or profile.")
    include = data["profiles"][profile].get("include")
    exclude = data.get("exclude", [])
    for values in [include, exclude]:
        if not isinstance(values, list) or not all(
            isinstance(value, str) and value and not value.startswith("/")
            and ".." not in Path(value).parts and "\\" not in value
            for value in values
        ):
            raise ValueError("Distribution paths must be explicit relative files or directory prefixes.")
    if not include:
        raise ValueError("A distribution profile needs explicit included paths.")
    return {"include": include, "exclude": exclude}


def selected(name, policy):
    if policy is None:
        return True
    def matches(pattern):
        return name.startswith(pattern) if pattern.endswith("/") else name == pattern
    return any(matches(value) for value in policy["include"]) and not any(matches(value) for value in policy["exclude"])


def hash_tree(root, profile="source"):
    result = {}
    root = Path(root)
    if root.is_symlink() or not root.is_dir():
        raise ValueError("Package must be an existing directory, not a symbolic link.")
    policy = distribution(root, profile)
    for folder, directories, filenames in os.walk(root):
        directories[:] = sorted(name for name in directories if name not in {".git", "__pycache__", ".venv"})
        if policy:
            def visit(name):
                prefix = (Path(folder) / name).relative_to(root).as_posix() + "/"
                excluded = any(prefix.startswith(value) for value in policy["exclude"] if value.endswith("/"))
                relevant = any(value.startswith(prefix) or prefix.startswith(value) for value in policy["include"])
                return relevant and not excluded
            directories[:] = [name for name in directories if visit(name)]
        for name in [*directories, *filenames]:
            path = Path(folder) / name
            if path.is_symlink():
                raise ValueError(f"Symbolic link in package: {path}")
        for filename in sorted(filenames):
            if filename == ".DS_Store":
                continue
            path = Path(folder) / filename
            if not selected(path.relative_to(root).as_posix(), policy):
                continue
            result[path.relative_to(root).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


def copy_package(source, destination, profile="source"):
    source, destination = Path(source), Path(destination)
    if destination.exists():
        raise ValueError("Copy destination already exists.")
    files = hash_tree(source, profile)
    destination.mkdir(parents=True)
    for name in files:
        target = destination / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source / name, target)
    readme = destination / "README.md"
    if profile == "runtime" and readme.is_file() and (destination / "documentation.json").is_file():
        text = readme.read_text()
        start, end = "<!-- repository:start -->", "<!-- repository:end -->"
        if start in text or end in text:
            if text.count(start) != 1 or text.count(end) != 1 or text.index(start) >= text.index(end):
                raise ValueError("Malformed repository-only README section.")
            before, rest = text.split(start, 1)
            _, after = rest.split(end, 1)
            text = before.rstrip() + "\n\n" + after.lstrip()
        readme.write_text(text.replace("<!-- skill-readme:source -->", "<!-- skill-readme:runtime -->"))
        record = destination / ".skill-builder.json"
        if record.exists():
            metadata = json.loads(record.read_text())
            for name in metadata.get("managed_hashes", {}):
                path = destination / name
                if not path.is_file():
                    raise ValueError(f"Runtime profile omitted required managed file: {name}")
                metadata["managed_hashes"][name] = hashlib.sha256(path.read_bytes()).hexdigest()
            write_json(record, metadata)
    return files


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


def check_case(package, case, allow_exec, remaining=None):
    result = {
        "id": case["id"], "critical": case["critical"],
        "status": "failed", "failures": [], "stdout": "", "stderr": "",
        "requirements": case["requirements"], "semantic": case["semantic"],
    }
    expected = case["expect"]
    exit_code = 0
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
    if not result["failures"]:
        result["status"] = "pending_review" if case["semantic"] else "passed"
    return result


def evaluate(package, suite, allow_exec=False, max_seconds=None):
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
            attempts.append(check_case(work, case, allow_exec, remaining))
    return {
        "schema_version": 1, "mode": "fresh_processes" if allow_exec else "mechanical_only",
        "suite_sha256": suite_hash, "package_hashes": original,
        "elapsed_seconds": time.monotonic() - started,
        "attempts": attempts, "metrics": metrics(attempts, len(suite)),
        "execution_boundary": "Disposable working directory; not an operating-system sandbox.",
    }


def maintenance(package, directory, suite, allow_exec=False, review=None, extension=None, export=None):
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
            policy = json.loads((package / "host_policy.json").read_text()).get("maintenance")
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
            if not extension["authorization_note"].strip() or not any(extension[key] for key in ["iterations", "seconds"]):
                raise ValueError("A positive extension needs the user's actual authorization.")
            if any(extension[key] < 0 for key in ["iterations", "seconds"]):
                raise ValueError("Extensions cannot decrease limits.")
            if extension not in state["extensions"]:
                state["policy"]["max_experiments"] += extension["iterations"]
                state["policy"]["max_seconds"] += extension["seconds"]
                state["policy"]["max_stagnant_experiments"] = state["policy"].get("max_stagnant_experiments", 3) + extension["iterations"]
                state["extensions"].append(extension)
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
            write_json(directory / record["review"], {"judgment": review, "graded_report": report})
        else:
            if state["status"] == "awaiting_review":
                raise ValueError("Finish the pending review before another experiment.")
            remaining = state["policy"]["max_seconds"] - state["elapsed_seconds"]
            if len(state["attempts"]) >= state["policy"]["max_experiments"] or remaining <= 0 or state["stagnant_attempts"] >= state["policy"].get("max_stagnant_experiments", 3):
                state.update(
                    status="needs_user_extension",
                    proposal={
                        "ask_user": True, "extra_iterations": 2,
                        "extra_seconds": max(60, math.ceil(state["elapsed_seconds"] / max(1, len(state["attempts"])) * 2)),
                        "basis": "Observed results and execution time; host-model time is not measured.",
                        "automatic_extension": False,
                        "stagnant_attempts": state["stagnant_attempts"],
                    },
                )
                write_json(state_path, state)
                return state
            report = evaluate(package, state["suite"], allow_exec, remaining)
            index = len(state["attempts"])
            record = {"report": f"attempts/{index:03}.json", "review": f"attempts/{index:03}-review.json", "files": files}
            state["attempts"].append(record)
            state["elapsed_seconds"] += report["elapsed_seconds"]
            write_json(directory / record["report"], report)
        score = report["metrics"]
        record["metrics"] = score
        if score["pending_review"]:
            state["status"] = "awaiting_review"
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
    parser.add_argument("--output", type=Path)
    parser.add_argument("--allow-exec", action="store_true")
    parser.add_argument("--session", type=Path, help="Bounded local maintenance records outside the package.")
    parser.add_argument("--review", type=Path)
    parser.add_argument("--extra-iterations", type=int, default=0)
    parser.add_argument("--extra-seconds", type=int, default=0)
    parser.add_argument("--authorization-note", default="")
    parser.add_argument("--export-best", type=Path)
    args = parser.parse_args()
    suite = json.loads((args.suite or args.package / "evals/cases.json").read_text())
    extension = None
    if args.extra_iterations or args.extra_seconds or args.authorization_note:
        extension = {"iterations": args.extra_iterations, "seconds": args.extra_seconds, "authorization_note": args.authorization_note}
    report = maintenance(
        args.package, args.session, suite, args.allow_exec,
        json.loads(args.review.read_text()) if args.review else None, extension, args.export_best,
    ) if args.session else evaluate(args.package, suite, args.allow_exec)
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
