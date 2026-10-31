"""Make an optional host-upload archive of the complete skill repository."""
import json
import os
from pathlib import Path
import re
import zipfile
import tempfile

import yaml

from .artifacts import check_package
from .common import Invalid, digest, inventory, copy_package


def package(source, output, version="0.2.0"):
    source, output = Path(source).resolve(), Path(output).resolve()
    if output.is_relative_to(source):
        raise Invalid("Archive cannot be part of its own source selection.")
    check = check_package(source)
    if not check["passed"]:
        raise Invalid("Package checks failed: " + "; ".join(check["findings"]))
    if not re.fullmatch(r"\d+\.\d+\.\d+(?:-[A-Za-z0-9.-]+)?", version):
        raise Invalid("Use an explicit semantic version.")
    metadata = yaml.safe_load((source / "SKILL.md").read_text().split("---\n", 2)[1])
    name = metadata["name"]
    before = inventory(source)
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="skill-release-") as folder:
        stage = Path(folder) / name
        source_files = copy_package(source, stage)
        staged_check = check_package(stage)
        if not staged_check["passed"]:
            raise Invalid("Repository archive is incomplete: " + "; ".join(staged_check["findings"]))
        files = inventory(stage)
        descriptor = os.open(output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        try:
            with os.fdopen(descriptor, "wb") as stream, zipfile.ZipFile(stream, "w", zipfile.ZIP_DEFLATED) as archive:
                for relative in sorted(files):
                    info = zipfile.ZipInfo(f"{name}/{relative}", (1980, 1, 1, 0, 0, 0))
                    info.compress_type = zipfile.ZIP_DEFLATED
                    archive.writestr(info, (stage / relative).read_bytes())
            if inventory(source) != before:
                raise Invalid("Source changed during packaging.")
        except Exception:
            output.unlink(missing_ok=True)
            raise
    return {
        "path": str(output), "sha256": digest(output.read_bytes()),
        "artifact": "repository", "source_files": source_files, "packaged_files": files,
        "version": version, "installed": False,
    }
