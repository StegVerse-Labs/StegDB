#!/usr/bin/env python3
"""
Generate per-repo file metadata (JSONL) for StegDB.

This script scans a target repo (e.g. CosDen) and writes:

    <repo_root>/meta/files.jsonl

with one JSON object per file containing:
- repo          (logical repo name, e.g. "CosDen")
- path          (relative path from repo root, posix style)
- sha256        (file hash)
- size_bytes
- timestamp     (UTC ISO8601)
- valid_location (always True for now)
- issues        (empty list for now)

Usage (from StegDB root):

    python tools/generate_repo_metadata.py --repo-root ../CosDen --repo-name CosDen
"""

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

DEFAULT_INCLUDE_DIRS = ("src", "tools")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def iter_files(root: Path, include_dirs: Iterable[str]):
    for rel_dir in include_dirs:
        base = root / rel_dir
        if not base.exists():
            continue
        for p in base.rglob("*"):
            if p.is_file():
                yield p


def generate_metadata(repo_root: Path, repo_name: str, include_dirs=DEFAULT_INCLUDE_DIRS) -> Path:
    meta_dir = repo_root / "meta"
    meta_dir.mkdir(exist_ok=True)
    meta_file = meta_dir / "files.jsonl"
    if meta_file.exists():
        meta_file.unlink()

    now = datetime.now(timezone.utc).isoformat()

    with meta_file.open("w", encoding="utf-8") as out:
        for path in iter_files(repo_root, include_dirs):
            rel_path = path.relative_to(repo_root).as_posix()
            size = path.stat().st_size
            file_hash = sha256_file(path)

            rec = {
                "repo": repo_name,
                "path": rel_path,
                "sha256": file_hash,
                "size_bytes": size,
                "timestamp": now,
                "valid_location": True,
                "issues": [],
            }
            out.write(json.dumps(rec) + "\n")

    return meta_file


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate per-repo metadata (meta/files.jsonl) for StegDB."
    )
    parser.add_argument(
        "--repo-root",
        type=str,
        required=True,
        help="Path to the target repo root (e.g. ../CosDen)",
    )
    parser.add_argument(
        "--repo-name",
        type=str,
        required=True,
        help='Logical repo name to record in metadata (e.g. "CosDen")',
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repo_root = Path(args.repo_root).resolve()
    repo_name = args.repo_name

    if not repo_root.exists():
        raise SystemExit(f"Repo root does not exist: {repo_root}")

    print(f"📦 Generating metadata for repo '{repo_name}' at {repo_root}")
    meta_file = generate_metadata(repo_root, repo_name)
    print(f"✅ Wrote metadata to {meta_file}")

if __name__ == "__main__":
    main()
