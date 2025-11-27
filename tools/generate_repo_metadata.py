#!/usr/bin/env python3
"""
Generate per-repo file metadata for StegDB.

Usage (normally via run_full_cycle.py):

    python tools/generate_repo_metadata.py \
        --repo-name CosDen \
        --repo-root ../CosDen \
        --output repos/CosDen/files.jsonl

It walks the repo root, records relative paths, sizes, and SHA256 hashes
for all regular files (excluding .git and some common junk), and writes
JSONL records to the output file.

Each record:

{
  "repo": "CosDen",
  "path": "src/CosDenOS/api.py",
  "sha256": "...",
  "size_bytes": 1234
}
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Iterable


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


IGNORE_DIRS = {".git", ".github", "__pycache__", ".mypy_cache", ".pytest_cache"}
IGNORE_FILES = {".DS_Store"}


def iter_files(root: Path) -> Iterable[Path]:
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        parts = p.relative_to(root).parts
        if parts and parts[0] in IGNORE_DIRS:
            continue
        if p.name in IGNORE_FILES:
            continue
        yield p


def generate_metadata(repo_name: str, repo_root: Path, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)

    print(f"📝 Generating metadata for {repo_name} from {repo_root}")
    count = 0

    with output.open("w", encoding="utf-8") as out:
        for path in iter_files(repo_root):
            rel = path.relative_to(repo_root).as_posix()
            size = path.stat().st_size
            digest = sha256_file(path)
            rec = {
                "repo": repo_name,
                "path": rel,
                "sha256": digest,
                "size_bytes": size,
            }
            out.write(json.dumps(rec) + "\n")
            count += 1

    print(f"  ✓ Wrote {count} records to {output}")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--repo-name", required=True)
    p.add_argument("--repo-root", required=True)
    p.add_argument("--output", required=True)
    return p.parse_args()


def main() -> None:
    args = parse_args()
    repo_name = args.repo_name
    repo_root = Path(args.repo_root).resolve()
    output = Path(args.output).resolve()

    if not repo_root.exists():
        raise SystemExit(f"Repo root does not exist: {repo_root}")

    generate_metadata(repo_name, repo_root, output)


if __name__ == "__main__":
    main()
