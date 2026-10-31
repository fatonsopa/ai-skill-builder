#!/usr/bin/env python3
"""Run repository regressions and validate an isolated complete installation."""
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
    with tempfile.TemporaryDirectory(prefix="skill-repository-check-") as folder:
        stage = Path(folder) / "skill-builder"
        copy_package(ROOT, stage)
        check = check_package(stage)
        findings.extend(check["findings"])
        files = hash_tree(stage)
        forbidden = ("docs/internal/", ".git/", ".venv/", "dist/", "runs/", "validation/")
        findings.extend("Private file copied: " + name for name in files if name == "AGENTS.md" or name.startswith(forbidden))
        process = subprocess.run([sys.executable, str(stage / "scripts/smoke_check.py")], capture_output=True, text=True)
        if process.returncode:
            findings.append("Installed self-check failed: " + process.stdout + process.stderr)
        print(json.dumps({"passed": not findings, "repository_files": len(files), "findings": findings}, indent=2))
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
