#!/usr/bin/env python
"""
StegDB multi-repo dependency evaluator.

- Reads aggregated metadata from: meta/aggregated_files.jsonl
- Optionally uses tools/repos_config.json to know about repos
- Writes:
    tools/dependency_graph.json   (lightweight summary)
    meta/dependency_status.json   (authoritative "brain verdict")

The prod gate (StegGuard) relies ONLY on dependency_status.json.
"""

from __future__ import annotations

import datetime as _dt
import json
import pathlib
import subprocess
import sys
from typing import Dict, Any

ROOT = pathlib.Path(__file__).resolve().parents[1]
META_DIR = ROOT / "meta"
TOOLS_DIR = ROOT / "tools"

AGGREGATED_PATH = META_DIR / "aggregated_files.jsonl"
GRAPH_PATH = TOOLS_DIR / "dependency_graph.json"
STATUS_PATH = META_DIR / "dependency_status.json"
REPOS_CONFIG_PATH = TOOLS_DIR / "repos_config.json"


def _now_iso() -> str:
    return _dt.datetime.utcnow().replace(tzinfo=_dt.timezone.utc).isoformat()


def _git_head_sha() -> str | None:
    try:
        sha = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            text=True,
        ).strip()
        return sha
    except Exception:
        return None


def _load_repos_config() -> Dict[str, Any]:
    """
    Optional configuration describing known repos.
    Expected shape (very simple for now):

    {
      "repos": [
        {"name": "CosDen"},
        {"name": "OtherRepo"}
      ]
    }
    """
    if not REPOS_CONFIG_PATH.exists():
        return {}

    try:
        data = json.loads(REPOS_CONFIG_PATH.read_text())
    except Exception:
        return {}

    repos: Dict[str, Any] = {}
    for entry in data.get("repos", []):
        name = entry.get("name")
        if name:
            repos[name] = entry
    return repos


def _summarise_aggregated_files() -> Dict[str, int]:
    """
    Look at meta/aggregated_files.jsonl and count records per repo.
    Each line is expected to be a JSON object with at least a "repo" field.
    """
    per_repo: Dict[str, int] = {}

    if not AGGREGATED_PATH.exists():
        # No aggregated data at all yet.
        return per_repo

    with AGGREGATED_PATH.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                # Skip bad lines; don't fail the whole run.
                continue

            repo_name = rec.get("repo") or "UNKNOWN"
            per_repo[repo_name] = per_repo.get(repo_name, 0) + 1

    return per_repo


def main() -> int:
    META_DIR.mkdir(exist_ok=True)
    TOOLS_DIR.mkdir(exist_ok=True)

    now = _now_iso()
    head_sha = _git_head_sha()
    repos_cfg = _load_repos_config()
    files_by_repo = _summarise_aggregated_files()

    # ------------------------------------------------------------
    # 1. Write a very simple dependency graph (for humans/tools)
    # ------------------------------------------------------------
    graph_doc: Dict[str, Any] = {
        "schema_version": 1,
        "generated_at": now,
        "stegdb_head_sha": head_sha,
        "repos": {
            name: {
                "files_indexed": files_by_repo.get(name, 0),
            }
            for name in sorted(files_by_repo.keys())
        },
    }

    GRAPH_PATH.write_text(json.dumps(graph_doc, indent=2, sort_keys=True), encoding="utf-8")
    print(f"📊 Wrote dependency graph to {GRAPH_PATH}")

    # ------------------------------------------------------------
    # 2. Build authoritative dependency_status.json
    # ------------------------------------------------------------
    repos_status: Dict[str, Any] = {}
    global_issues = []

    # Use either configured repos or whatever we saw in aggregated files.
    all_repo_names = set(files_by_repo.keys())
    all_repo_names.update(repos_cfg.keys())

    if not all_repo_names:
        global_issues.append({"repo": None, "reason": "no_repos_detected"})

    for repo_name in sorted(all_repo_names):
        files_count = files_by_repo.get(repo_name, 0)

        status = "ok" if files_count > 0 else "no_metadata"
        issues = []

        if files_count == 0:
            issues.append("no metadata records found for this repo")

        repos_status[repo_name] = {
            "status": status,
            "mode": "prod",  # later we can derive from config if needed
            "files_indexed": files_count,
            "issues": issues,
        }

        if status != "ok":
            global_issues.append(
                {"repo": repo_name, "reason": f"status_{status}"}
            )

    overall_status = "ok" if not global_issues else "degraded"

    status_doc: Dict[str, Any] = {
        "schema_version": 1,
        "generated_at": now,
        "stegdb_full_cycle_sha": head_sha,
        "overall_status": overall_status,
        "repos": repos_status,
        "issues": global_issues,
    }

    STATUS_PATH.write_text(json.dumps(status_doc, indent=2, sort_keys=True), encoding="utf-8")
    print(f"🧠 Wrote dependency status to {STATUS_PATH}")
    print(f"   overall_status={overall_status!r}, head_sha={head_sha}")

    # This script itself never hard-fails for "degraded"; the gate decides.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
