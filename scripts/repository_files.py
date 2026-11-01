"""Public repository inventory and copies; the repository is the skill artifact."""
import hashlib
import os
from pathlib import Path
import re
import shutil

ROOT = Path(__file__).resolve().parents[1]
PRIVATE_DIRS = {".git", ".venv", "__pycache__", ".pytest_cache", "node_modules", "dist", "runs", "validation"}


def inventory(root, profile=None):
    root = Path(root)
    if root.is_symlink() or not root.is_dir():
        raise ValueError("Use an existing repository directory, not a symbolic-link source.")
    result = {}
    for folder, directories, files in os.walk(root):
        relative = Path(folder).relative_to(root)
        directories[:] = sorted(name for name in directories if name not in PRIVATE_DIRS and not (relative.as_posix() == "docs" and name == "internal"))
        for name in [*directories, *files]:
            path = Path(folder) / name
            if path.is_symlink():
                raise ValueError("Unexpected symbolic link inside the repository: " + str(path))
        for name in sorted(files):
            if name in {".DS_Store", ".lock"} or name.endswith(".pyc") or relative == Path(".") and name.startswith(".env"):
                continue
            path = Path(folder) / name
            result[path.relative_to(root).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


def compare_installation(source, installed):
    source = Path(source).expanduser().resolve()
    active = Path(installed).expanduser().absolute()
    resolved = active.resolve()
    expected = inventory(source)
    if "SKILL.md" not in expected:
        raise ValueError("Installation comparison needs a source with root SKILL.md.")
    actual = inventory(resolved) if resolved.is_dir() else {}
    missing = sorted(set(expected) - set(actual))
    extra = sorted(set(actual) - set(expected))
    changed = sorted(name for name in set(expected) & set(actual) if expected[name] != actual[name])
    return {"passed": not (missing or extra or changed), "source": str(source),
            "installed_path": str(active), "resolved_path": str(resolved), "linked": active.is_symlink(),
            "missing": missing, "unexpected": extra, "changed": changed,
            "limits": "Compares public artifact files; does not establish host activation or task behavior."}


def copy_repository(root, destination, profile=None):
    root, requested = Path(root).resolve(), Path(destination).expanduser()
    if requested.exists() or requested.is_symlink():
        raise ValueError("Destination must be new and separate from the repository.")
    destination = requested.resolve()
    if destination.is_relative_to(root) or root.is_relative_to(destination):
        raise ValueError("Destination must be new and separate from the repository.")
    files = inventory(root)
    destination.mkdir(parents=True)
    for name in files:
        target = destination / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(root / name, target)
    if inventory(root) != files:
        raise ValueError("Repository changed during copy.")
    return files


def skill_name(root):
    text = (Path(root) / "SKILL.md").read_text()
    pieces = text.split("---\n", 2)
    match = re.search(r"^name:\s*['\"]?([a-z0-9]+(?:-[a-z0-9]+)*)['\"]?\s*$", pieces[1], re.M) if len(pieces) == 3 and not pieces[0] else None
    if not match:
        raise ValueError("The repository root needs SKILL.md with valid name metadata.")
    return match[1]
