#!/usr/bin/env python3
"""
StegDB Repair Engine for StegVerse Repos
----------------------------------------

Phase 1: CosDen only (extensible to other repos later).

This script:

1) Reads StegDB/meta/aggregated_files.jsonl (created by ingest_repo_metadata.py)
2) Walks StegDB/canonical/cosden/ to find canonical CosDen files
3) Compares hashes with the latest known repo state
4) Writes a repair plan to:

    repairs/CosDen/repair_plan.json

The repair plan can then be consumed by a workflow in the CosDen repo to
copy canonical files into place and open a PR.

Usage (from StegDB root):

    python tools/repair_repos.py
"""

import json
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any
import hashlib


STEGBDB_ROOT = Path(__file__).resolve().parents[1]
AGGREGATE_META_FILE = STEGBDB_ROOT / "meta" / "aggregated_files.jsonl"

# Where canonical files live for CosDen
COSDEN_CANONICAL_ROOT = STEGBDB_ROOT / "canonical" / "cosden"

# Where to write repair plans
REPAIRS_ROOT = STEGBDB_ROOT / "repairs"


@dataclass
class FileRecord:
    repo: str
    path: str
    sha256: str
    valid_location: bool
    raw: Dict[str, Any]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def load_aggregated_metadata() -> Dict[str, Dict[str, FileRecord]]:
    """
    Load aggregated_files.jsonl into a mapping:
        repo -> path -> FileRecord
    """
    index: Dict[str, Dict[str, FileRecord]] = {}

    if not AGGREGATE_META_FILE.exists():
        print(f"❌ Aggregated metadata not found: {AGGREGATE_META_FILE}", file=sys.stderr)
        print("   Run tools/ingest_repo_metadata.py first.", file=sys.stderr)
        return index

    with AGGREGATE_META_FILE.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError as exc:
                print(f"⚠️ Skipping invalid JSON in aggregated metadata: {exc}", file=sys.stderr)
                continue

            repo = obj.get("repo")
            path = obj.get("path")
            sha256 = obj.get("sha256")
            if not repo or not path or not sha256:
                continue

            valid_location = bool(obj.get("valid_location", True))

            repo_map = index.setdefault(repo, {})
            repo_map[path] = FileRecord(
                repo=repo,
                path=path,
                sha256=sha256,
                valid_location=valid_location,
                raw=obj,
            )

    return index


def build_cosden_repair_plan(file_index: Dict[str, Dict[str, FileRecord]]) -> Dict[str, Any]:
    """
    Create a repair plan for the CosDen repo by comparing canonical files
    under canonical/cosden/ to the known repo state from aggregated_files.jsonl.
    """
    repo_name = "CosDen"  # the 'repo' field in aggregated metadata for CosDen
    repo_entries = file_index.get(repo_name, {})

    if not COSDEN_CANONICAL_ROOT.exists():
        print(f"⚠️ No canonical files found for CosDen at {COSDEN_CANONICAL_ROOT}")
        return {}

    actions: List[Dict[str, Any]] = []

    for path in COSDEN_CANONICAL_ROOT.rglob("*"):
        if path.is_dir():
            continue

        canonical_rel = path.relative_to(COSDEN_CANONICAL_ROOT).as_posix()  # e.g. src/CosDenOS/api.py
        canonical_hash = sha256_file(path)

        rec = repo_entries.get(canonical_rel)
        if rec is None:
            # File missing in repo: needs to be created
            actions.append(
                {
                    "type": "write_file",
                    "target_path": canonical_rel,
                    "canonical_relpath": canonical_rel,
                    "reason": "missing_in_repo",
                    "canonical_sha256": canonical_hash,
                }
            )
        elif rec.sha256 != canonical_hash:
            # File present but different: needs update
            actions.append(
                {
                    "type": "write_file",
                    "target_path": canonical_rel,
                    "canonical_relpath": canonical_rel,
                    "reason": "hash_mismatch",
                    "repo_sha256": rec.sha256,
                    "canonical_sha256": canonical_hash,
                }
            )
        else:
            # Hash matches: nothing to do
            continue

    if not actions:
        print("✅ No differences detected for CosDen – no repair plan needed.")
        return {}

    now = datetime.now(timezone.utc).isoformat()

    plan = {
        "repo": repo_name,
        "generated_at": now,
        "canonical_root": "canonical/cosden",
        "actions": actions,
    }
    return plan


def write_repair_plan(repo: str, plan: Dict[str, Any]) -> None:
    if not plan:
        return

    REPAIRS_ROOT.mkdir(exist_ok=True)
    target_dir = REPAIRS_ROOT / repo
    target_dir.mkdir(exist_ok=True)
    plan_path = target_dir / "repair_plan.json"

    with plan_path.open("w", encoding="utf-8") as f:
        json.dump(plan, f, indent=2)

    rel = plan_path.relative_to(STEGBDB_ROOT)
    print(f"🛠️ Wrote repair plan for {repo} to {rel}")


def main() -> None:
    print("\n🛠️ StegDB Repair Engine (Phase 1: CosDen)\n")

    file_index = load_aggregated_metadata()
    if not file_index:
        print("No metadata loaded; aborting.")
        sys.exit(1)

    # Build plan for CosDen
    plan = build_cosden_repair_plan(file_index)
    if plan:
        write_repair_plan("CosDen", plan)
    else:
        print("No repair actions required for CosDen.")

    print("\nDone.\n")


if __name__ == "__main__":
    main()
