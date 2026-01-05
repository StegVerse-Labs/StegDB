#!/usr/bin/env python3
"""
Stamp StegVerse workflow headers with canonical version metadata.

Behavior:
- Reads stegverse.canonical.lock.json for sha256 + source.
- For each .github/workflows/*.yml:
  - Ensures a single canonical header comment exists immediately under `name: ...`
  - Header includes canonical sha + source + file path
- Safe: does not alter YAML structure beyond inserting/replacing a comment line.

Header format:
  # stegverse: canonical_sha256=<sha> source=<repo> path=<path>

Exit code:
  0 on success
  2 if lock file missing or invalid
"""
from __future__ import annotations

import json
import re
from pathlib import Path

LOCK = Path("stegverse.canonical.lock.json")
WF_DIR = Path(".github/workflows")

HEADER_RE = re.compile(r"^\s*#\s*stegverse:\s*(.+)\s*$")
NAME_RE = re.compile(r"^\s*name:\s*.+\s*$")

def load_lock() -> dict:
    if not LOCK.exists():
        raise SystemExit(2)
    try:
        data = json.loads(LOCK.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("lock not dict")
        if not data.get("sha256"):
            raise ValueError("missing sha256")
        return data
    except Exception:
        raise SystemExit(2)

def stamp_file(path: Path, sha: str, source: str) -> bool:
    original = path.read_text(encoding="utf-8").splitlines(True)

    # Find first `name:` line
    name_idx = None
    for i, line in enumerate(original):
        if NAME_RE.match(line):
            name_idx = i
            break

    # If no name, do nothing (still valid for some use cases, but we won't touch)
    if name_idx is None:
        return False

    desired = f"# stegverse: canonical_sha256={sha} source={source} path={path.as_posix()}\n"

    out = []
    changed = False

    out.extend(original[: name_idx + 1])

    # Decide what comes immediately after name:
    next_idx = name_idx + 1
    if next_idx < len(original) and HEADER_RE.match(original[next_idx]):
        # Replace existing header
        if original[next_idx] != desired:
            out.append(desired)
            changed = True
        else:
            out.append(original[next_idx])
        out.extend(original[next_idx + 1 :])
    else:
        # Insert header
        out.append(desired)
        changed = True
        out.extend(original[next_idx:])

    if changed:
        path.write_text("".join(out), encoding="utf-8")
    return changed

def main() -> int:
    lock = load_lock()
    sha = str(lock["sha256"]).strip()
    source = str(lock.get("canonical_source", "StegVerse-Labs/StegDB")).strip()

    if not WF_DIR.exists():
        return 0

    changed_any = False
    for wf in sorted(WF_DIR.glob("*.yml")) + sorted(WF_DIR.glob("*.yaml")):
        changed_any = stamp_file(wf, sha, source) or changed_any

    return 0

if __name__ == "__main__":
    raise SystemExit(main())
