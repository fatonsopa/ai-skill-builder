"""File and contract operations shared by the runner."""
import contextlib
import fcntl
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import tempfile

from jsonschema import Draft202012Validator, FormatChecker
from repository_files import inventory as hash_tree, copy_repository as copy_package


class Invalid(ValueError):
    """An operation cannot satisfy its declared contract."""


def digest(value):
    raw = value if isinstance(value, bytes) else json.dumps(
        value, sort_keys=True, ensure_ascii=False, separators=(",", ":")
    ).encode()
    return hashlib.sha256(raw).hexdigest()


def load(path):
    return json.loads(Path(path).read_text())


def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".write-", dir=path.parent)
    try:
        with os.fdopen(fd, "w") as stream:
            json.dump(value, stream, indent=2, ensure_ascii=False, allow_nan=False)
            stream.write("\n")
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def validate(value, schema):
    checker = FormatChecker()
    def formats(node):
        if isinstance(node, dict):
            found = {node["format"]} if isinstance(node.get("format"), str) else set()
            return found | set().union(*(formats(item) for item in node.values()))
        if isinstance(node, list):
            return set().union(*(formats(item) for item in node))
        return set()
    missing = formats(schema) - checker.checkers.keys()
    if missing:
        raise Invalid(f"Required format checks unavailable: {sorted(missing)}. Install the locked dependencies.")
    errors = sorted(
        Draft202012Validator(schema, format_checker=checker).iter_errors(value),
        key=lambda error: str(list(error.path)),
    )
    if errors:
        raise Invalid("; ".join(
            f"{'.'.join(map(str, error.path)) or 'value'}: {error.message}"
            for error in errors
        ))
    return value


def relative(value):
    path = PurePosixPath(value)
    if not value or "\\" in value or path.is_absolute() or ".." in path.parts:
        raise Invalid(f"Not a package-relative path: {value}")
    if value != path.as_posix() or value == ".":
        raise Invalid(f"Not a normalized file path: {value}")
    if any(part in {".git", "__pycache__", ".venv"} for part in path.parts):
        raise Invalid(f"Reserved package path: {value}")
    return path


def inside(root, name):
    relative(name)
    root = Path(root).resolve()
    path = root / name
    for ancestor in [path, *path.parents]:
        if ancestor == root:
            break
        if ancestor.is_symlink():
            raise Invalid(f"Symbolic links are not supported: {path}")
    if not path.resolve().is_relative_to(root):
        raise Invalid(f"Path leaves package: {name}")
    return path


def inventory(root, profile="source"):
    root = Path(root)
    if root.is_symlink():
        raise Invalid(f"Symbolic-link root is not supported: {root}")
    if not root.exists():
        return {}
    if not root.is_dir():
        raise Invalid(f"Expected directory: {root}")
    try:
        return hash_tree(root, profile)
    except ValueError as error:
        raise Invalid(str(error)) from error


@contextlib.contextmanager
def locked(root):
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    with (root / ".lock").open("a") as stream:
        fcntl.flock(stream, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(stream, fcntl.LOCK_UN)
