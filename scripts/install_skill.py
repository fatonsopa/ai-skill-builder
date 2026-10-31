#!/usr/bin/env python3
"""Install the skill repository or make a host-upload ZIP."""
import argparse
import json
from pathlib import Path
import re
import sys
import os
import tempfile
import zipfile

from evaluate import copy_package, hash_tree


def skill_name(source):
    source = Path(source).resolve()
    text = (source / "SKILL.md").read_text()
    header = text.split("---\n", 2)
    match = re.search(r"^name:\s*['\"]?([a-z0-9]+(?:-[a-z0-9]+)*)['\"]?\s*$", header[1], re.M) if len(header) == 3 and not header[0] else None
    if not match:
        raise ValueError("The source needs valid SKILL.md name metadata.")
    return match[1]


def install(source, host, destination=None):
    source = Path(source).resolve()
    name = skill_name(source)
    base = Path.home() / (".agents/skills" if host == "codex" else ".claude/skills")
    destination = Path(destination).expanduser().resolve() if destination else base / name
    if destination.is_relative_to(source) or source.is_relative_to(destination):
        raise ValueError("Installation destination must be separate from the source.")
    files = copy_package(source, destination, profile="runtime")
    return {"status": "installed", "name": name, "host": host, "destination": str(destination), "files": len(files)}


def make_archive(source, output):
    source, output = Path(source).resolve(), Path(output).expanduser().resolve()
    name = skill_name(source)
    if output.is_relative_to(source):
        raise ValueError("Write the upload ZIP outside the source folder.")
    before = hash_tree(source)
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="skill-upload-") as folder:
        stage = Path(folder) / name
        copy_package(source, stage, profile="runtime")
        files = hash_tree(stage)
        descriptor = os.open(output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        try:
            with os.fdopen(descriptor, "wb") as stream, zipfile.ZipFile(stream, "w", zipfile.ZIP_DEFLATED) as archive:
                for relative in sorted(files):
                    archive.write(stage / relative, f"{name}/{relative}")
            if hash_tree(source) != before:
                raise ValueError("Source changed during packaging.")
        except Exception:
            output.unlink(missing_ok=True)
            raise
    return {"status": "packaged", "name": name, "path": str(output), "files": len(files)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--host", choices=["codex", "claude-code"])
    action.add_argument("--archive", type=Path, help="Create an upload ZIP outside the source folder.")
    parser.add_argument("--destination", type=Path)
    parser.add_argument("--source", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    if args.archive and args.destination:
        parser.error("--destination is only used with --host.")
    try:
        result = make_archive(args.source, args.archive) if args.archive else install(args.source, args.host, args.destination)
        print(json.dumps(result, indent=2))
        return 0
    except (OSError, ValueError) as error:
        print(json.dumps({"error": str(error)}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
