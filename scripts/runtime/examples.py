"""Preserve paired examples and validate split/provenance boundaries."""
import json
from pathlib import Path
import shutil

from .common import Invalid, digest, load, save


def extract(path):
    path = Path(path)
    if path.suffix.lower() == ".json":
        return {"format": "json", "value": load(path)}
    if path.suffix.lower() in {".txt", ".md"}:
        return {"format": "text", "value": path.read_text()}
    raise Invalid(f"Unsupported example format {path.suffix!r}; supported: JSON, UTF-8 text, Markdown.")


def ingest(manifest, output):
    manifest = Path(manifest).resolve()
    rows = load(manifest)
    if not isinstance(rows, list) or not rows:
        raise Invalid("Example manifest must contain at least one pair.")
    output = Path(output).resolve()
    if output.exists():
        raise Invalid("Example output already exists.")
    ids, families, contents, records = set(), {}, {}, []
    for row in rows:
        required = {"id", "source_family", "input", "output", "split", "provenance"}
        if set(row) != required or not all(isinstance(row[key], str) and row[key] for key in required):
            raise Invalid("Each example needs id, source_family, input, output, split, provenance.")
        if row["id"] in ids:
            raise Invalid("Duplicate example ID.")
        ids.add(row["id"])
        if row["split"] not in {"development", "regression", "protected"}:
            raise Invalid("Unknown example split.")
        if row["provenance"] not in {"real", "synthetic"}:
            raise Invalid("Example provenance must be real or synthetic.")
        previous = families.setdefault(row["source_family"], row["split"])
        if previous != row["split"]:
            raise Invalid("Related examples cannot cross splits.")
        record = dict(row)
        for role in ["input", "output"]:
            path = (manifest.parent / row[role]).resolve()
            if path.is_symlink() or not path.is_file():
                raise Invalid(f"Unreadable example: {path}")
            parsed = extract(path)
            key = digest(parsed)
            old_split = contents.setdefault((role, key), row["split"])
            if old_split != row["split"]:
                raise Invalid("Exact duplicate content cannot cross splits.")
            record[role] = {"original": str(path), "sha256": digest(path.read_bytes()), "extracted": parsed}
        records.append(record)
    output.mkdir(parents=True, mode=0o700)
    for index, record in enumerate(records):
        for role in ["input", "output"]:
            original = Path(record[role]["original"])
            relative = f"originals/{index:03}-{role}{original.suffix.lower()}"
            target = output / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(original, target)
            record[role]["copy"] = relative
    result = {
        "schema_version": 1, "pairs": records,
        "limits": [
            "Family labels are supplied, not inferred; semantic near duplicates still need review.",
            "Protected data must remain outside optimizing contexts; directory permissions are not a sandbox.",
        ],
        "independent_protected_families": len({
            row["source_family"] for row in records
            if row["split"] == "protected" and row["provenance"] == "real"
        }),
    }
    save(output / "examples.json", result)
    return result


def development_packet(path):
    bundle = load(Path(path) / "examples.json")
    return {
        "bundle_sha256": digest(bundle),
        "development_pairs": [row for row in bundle["pairs"] if row["split"] != "protected"],
        "independent_protected_families": bundle["independent_protected_families"],
        "limits": bundle["limits"],
    }
