"""Matched explicit-use model observations; no automatic discovery claim."""
import json
from pathlib import Path
import time

from .adapters import sample
from .common import Invalid, digest, inside, inventory, load, save, validate
from .contracts import ANY, BOOL, NUMBER, STRINGS, TEXT, array, obj
from evaluate import metrics

CONFIG = obj({
    "subject": TEXT,
    "models": array(obj({
        "provider": {"enum": ["codex", "claude"]}, "model": TEXT,
        "repetitions": {"type": "integer", "minimum": 1},
    }), 1),
    "cases": array(obj({
        "id": TEXT, "request": ANY, "resources": STRINGS,
        "expected": ANY, "semantic": BOOL, "critical": BOOL,
        "split": {"enum": ["development", "regression", "protected"]},
    }), 1),
    "compare_without_skill": BOOL,
    "max_invocations": {"type": "integer", "minimum": 0},
    "max_seconds": {"type": "integer", "minimum": 1},
    "acceptance_ledger": TEXT,
}, required=["subject", "models", "cases", "compare_without_skill", "max_invocations", "max_seconds"])


def aggregate(attempts):
    groups = {}
    for row in attempts:
        key = f"{row['provider']}:{row['model']}:{row['condition']}"
        groups.setdefault(key, []).append(row)
    return {key: metrics(rows, len(rows)) for key, rows in groups.items()}


def benchmark(config_path, output):
    config_path = Path(config_path).resolve()
    config = validate(load(config_path), CONFIG)
    output = Path(output).resolve()
    if output.exists():
        raise Invalid("Benchmark output already exists; preserve prior attempts.")
    subject = (config_path.parent / config["subject"]).resolve()
    if subject.is_relative_to(output) or output.is_relative_to(subject):
        raise Invalid("Benchmark output must be separate from the subject.")
    before = inventory(subject)
    if "SKILL.md" not in before:
        raise Invalid("Subject needs SKILL.md.")
    if len({case["id"] for case in config["cases"]}) != len(config["cases"]):
        raise Invalid("Duplicate benchmark case ID.")
    model_keys = [(row["provider"], row["model"]) for row in config["models"]]
    if len(set(model_keys)) != len(model_keys):
        raise Invalid("Model configurations must have unique provider/model identities.")
    protected = any(case["split"] == "protected" for case in config["cases"])
    if protected and config["max_invocations"]:
        if not config.get("acceptance_ledger"):
            raise Invalid("Protected evaluation needs a one-use acceptance ledger.")
        ledger = (config_path.parent / config["acceptance_ledger"]).resolve()
        if ledger.is_relative_to(subject):
            raise Invalid("Acceptance ledger cannot be inside the candidate.")
        if ledger.exists():
            raise Invalid("Acceptance cases have been exposed; use new protected cases or classify them as regressions.")
        save(ledger, {"config_sha256": digest(config), "subject": before, "status": "reserved"})
    resources = {}
    for case in config["cases"]:
        for name in case["resources"]:
            path = inside(subject, name)
            if not path.is_file():
                raise Invalid(f"Missing benchmark resource: {name}")
            resources[name] = path.read_text()
    output.mkdir(parents=True, mode=0o700)
    conditions = ["with_skill", "without_skill"] if config["compare_without_skill"] else ["with_skill"]
    planned = [
        (model, case, condition, repetition)
        for model in config["models"]
        for case in config["cases"]
        for condition in conditions
        for repetition in range(1, model["repetitions"] + 1)
    ]
    attempts, calls, execution_block = [], 0, None
    started = time.monotonic()
    for index, (model, case, condition, repetition) in enumerate(planned, 1):
        row = {
            "id": f"OBS-{index:04}", "provider": model["provider"], "model": model["model"],
            "case_id": case["id"], "condition": condition, "repetition": repetition,
            "critical": case["critical"], "semantic": case["semantic"], "status": "not_run",
        }
        remaining = config["max_seconds"] - (time.monotonic() - started)
        if execution_block:
            row.update(reason="Provider usage limit stopped this batch; no further invocation or fallback.",
                       provider_error=execution_block)
        elif calls < config["max_invocations"] and remaining > 0:
            payload = {"request": case["request"]}
            if condition == "with_skill":
                payload["skill"] = (subject / "SKILL.md").read_text()
                payload["resources"] = {name: resources[name] for name in case["resources"]}
            calls += 1
            result = sample(model["provider"], model["model"], payload, min(remaining, 300))
            row["observation"] = result
            if result.get("provider_error"):
                row.update(provider_error=result["provider_error"], failure_kind=result.get("failure_kind", "provider_error"))
                if result["provider_error"]["kind"] == "usage_limit":
                    execution_block = result["provider_error"]
            if result["status"] == "response_validated":
                row["status"] = "pending_review" if case["semantic"] else (
                    "passed" if result["response"] == case["expected"] else "failed"
                )
            else:
                row["status"] = "infrastructure_failure" if result["status"] == "infrastructure_failure" else "failed"
        attempts.append(row)
        save(output / f"{row['id']}.json", row)
    if inventory(subject) != before:
        raise Invalid("Subject changed during comparison; observations cannot establish acceptance.")
    report = {
        "schema_version": 1, "config_sha256": digest(config), "subject_hashes": before,
        "mode": "explicit_instruction_use", "models": config["models"],
        "attempts": attempts, "by_model_and_condition": aggregate(attempts),
        "model_invocations": calls, "elapsed_seconds": time.monotonic() - started,
        "execution_block": execution_block,
        "limits": [
            "Explicit instruction loading is not host discovery.",
            "Requested model IDs are recorded; aliases are not independently resolved.",
            "CLI invocation counts are not billing caps or provider request counts.",
            "CLI modes do not establish complete isolation from private files; use reviewed inputs and verified external isolation when required.",
        ],
    }
    save(output / "report.json", report)
    return report


def grade(report_path, reviews_path):
    report_path = Path(report_path)
    report = load(report_path)
    reviews = load(reviews_path)
    if reviews.get("report_sha256") != digest(report):
        raise Invalid("Reviews belong to another report version.")
    if reviews.get("reviewer", {}).get("kind") not in {"human", "model"}:
        raise Invalid("Identify reviewer kind and provenance.")
    expected = {row["id"] for row in report["attempts"] if row["status"] == "pending_review"}
    rows = reviews.get("cases", [])
    if len({row["id"] for row in rows}) != len(rows) or {row["id"] for row in rows} != expected:
        raise Invalid("Cover every pending observation exactly once.")
    by_id = {row["id"]: row for row in rows}
    for row in report["attempts"]:
        if row["id"] in by_id:
            label = by_id[row["id"]]
            if not isinstance(label.get("accepted"), bool) or not label.get("rationale"):
                raise Invalid("Each judgment needs a boolean verdict and rationale.")
            row["review"] = {"reviewer": reviews["reviewer"], **label}
            row["status"] = "passed" if label["accepted"] else "failed"
    report["by_model_and_condition"] = aggregate(report["attempts"])
    # Retain the original observations and grade file; never replace an earlier judgment.
    target = report_path.with_name("graded-" + digest(reviews)[:12] + ".json")
    if target.exists():
        raise Invalid("This judgment has already been retained.")
    report["grade_source_sha256"] = digest(reviews)
    save(target, report)
    return report
