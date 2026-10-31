#!/usr/bin/env python3
"""Run repository regressions and validate both public distribution profiles."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from evaluate import copy_package, hash_tree
from runtime.artifacts import check_package


def main():
    suite = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"], cwd=ROOT)
    if suite.returncode:
        return suite.returncode
    findings = []
    profiles = {}
    with tempfile.TemporaryDirectory(prefix="skill-repository-check-") as folder:
        for profile in ("source", "runtime"):
            stage = Path(folder) / profile
            copy_package(ROOT, stage, profile=profile)
            check = check_package(stage)
            findings.extend(f"{profile}: {item}" for item in check["findings"])
            files = hash_tree(stage)
            forbidden = ("docs/internal/", ".git/", ".venv/", "dist/", "runs/", "validation/")
            findings.extend(f"{profile}: private file selected: {name}" for name in files if name == "AGENTS.md" or name.startswith(forbidden))
            if profile == "runtime":
                findings.extend(f"runtime: development file selected: {name}" for name in files if name.startswith(("tests/", "tools/")))
                process = subprocess.run([sys.executable, str(stage / "scripts/smoke_check.py")], capture_output=True, text=True)
                if process.returncode:
                    findings.append("Runtime self-check failed: " + process.stdout + process.stderr)
            profiles[profile] = {"files": len(files), "package_passed": check["passed"]}
    print(json.dumps({"passed": not findings, "profiles": profiles, "findings": findings}, indent=2))
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
