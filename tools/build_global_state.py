#!/usr/bin/env python3
"""
Build StegDB global state artifact from meta/aggregated_files.jsonl.

Inputs:
  meta/aggregated_files.jsonl  (JSON object per line, includes at least: repo, path OR file_path)

Outputs:
  meta/global_state.json
  meta/GLOBAL_STATE.md

Goal:
- Conversation-ready, machine-readable snapshot of what repos were actually seen
- What surfaces appear wired (by path markers)
- Enough to stop "starting from scratch" without needing screenshots
"""

from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple


STEGBDB_ROOT = Path(__file__).resolve().parents[1]
META_DIR = STEGBDB_ROOT / "meta"
AGG = META_DIR / "aggregated_files.jsonl"

OUT_JSON = META_DIR / "global_state.json"
OUT_MD = META_DIR / "GLOBAL_STATE.md"

# Marker prefixes -> "wired surface" flags
SURFACE_MARKERS = {
    "workflows": [".github/workflows/"],
    "governance": ["governance/"],
    "policy": ["policy/"],
    "audit": ["audit/"],
    "ledger": ["ledger/"],
    "telemetry": ["telemetry/"],
    "taskops": ["taskops/"],
    "trigger": ["trigger/"],
    "autopatch": ["autopatch/"],
    "roadmap": ["roadmap/"],
    "stegdb_overlay": ["StegDB/", "stegdb/"],
    "canonical": ["canonical/"],
    "tv": ["tv/", "TV/"],
}

def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()

def norm_path(p: str) -> str:
    return p.replace("\\", "/").lstrip("./")

def read_jsonl(path: Path) -> List[Dict[str, Any]]:
    if not path.exists() or path.stat().st_size == 0:
        return []
    rows: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                # ignore bad lines
                continue
            rows.append(obj)
    return rows

def get_repo(rec: Dict[str, Any]) -> str:
    return str(rec.get("repo") or rec.get("repo_name") or "UNKNOWN")

def get_path(rec: Dict[str, Any]) -> str:
    p = rec.get("path") or rec.get("file_path") or rec.get("relpath") or rec.get("name")
    if not p:
        return ""
    return norm_path(str(p))

def compute_surfaces(paths: Set[str]) -> Dict[str, bool]:
    out: Dict[str, bool] = {}
    for surface, prefixes in SURFACE_MARKERS.items():
        out[surface] = any(any(p.startswith(pref) for pref in prefixes) for p in paths)
    return out

def main() -> None:
    META_DIR.mkdir(exist_ok=True)

    rows = read_jsonl(AGG)
    if not rows:
        state = {
            "generated_at_utc": now_utc(),
            "note": "No aggregated metadata found. Likely repos were not cloned or per-repo meta/files.jsonl were not produced.",
            "repos_seen": [],
            "repo_count": 0,
        }
        OUT_JSON.write_text(json.dumps(state, indent=2), encoding="utf-8")
        OUT_MD.write_text(
            "# StegDB Global State\n\n"
            f"Generated: `{state['generated_at_utc']}`\n\n"
            "⚠ **No aggregated metadata found** (`meta/aggregated_files.jsonl` is empty or missing).\n\n"
            "This usually means the runner did not have other repos cloned, or per-repo validators did not emit `meta/files.jsonl`.\n",
            encoding="utf-8",
        )
        return

    per_repo_paths: Dict[str, Set[str]] = {}
    per_repo_count: Dict[str, int] = {}

    for rec in rows:
        repo = get_repo(rec)
        path = get_path(rec)
        per_repo_count[repo] = per_repo_count.get(repo, 0) + 1
        if repo not in per_repo_paths:
            per_repo_paths[repo] = set()
        if path:
            per_repo_paths[repo].add(path)

    repos = sorted(per_repo_count.keys(), key=lambda x: x.lower())

    repos_detail: List[Dict[str, Any]] = []
    for repo in repos:
        paths = per_repo_paths.get(repo, set())
        surfaces = compute_surfaces(paths)
        repos_detail.append(
            {
                "repo": repo,
                "records": per_repo_count.get(repo, 0),
                "surfaces": surfaces,
            }
        )

    global_state = {
        "generated_at_utc": now_utc(),
        "source": "meta/aggregated_files.jsonl",
        "repo_count": len(repos),
        "repos_seen": repos,
        "repos": repos_detail,
    }

    OUT_JSON.write_text(json.dumps(global_state, indent=2), encoding="utf-8")

    # Human summary
    lines: List[str] = []
    lines.append("# StegDB Global State (Self-Test Snapshot)\n\n")
    lines.append(f"Generated: `{global_state['generated_at_utc']}`\n\n")
    lines.append(f"- Repos seen: **{global_state['repo_count']}**\n")
    lines.append(f"- Source: `{global_state['source']}`\n\n")

    lines.append("## Repo Surfaces (wired by path markers)\n\n")
    lines.append("| Repo | Records | Workflows | Governance | Policy | Ledger | Audit | Telemetry | TaskOps | Trigger | Canonical |\n")
    lines.append("|---|---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|\n")
    for r in repos_detail:
        s = r["surfaces"]
        def yn(b: bool) -> str:
            return "✅" if b else "—"
        lines.append(
            f"| {r['repo']} | {r['records']} | {yn(s['workflows'])} | {yn(s['governance'])} | {yn(s['policy'])} | {yn(s['ledger'])} | {yn(s['audit'])} | {yn(s['telemetry'])} | {yn(s['taskops'])} | {yn(s['trigger'])} | {yn(s['canonical'])} |\n"
        )

    lines.append("\n## How to use this artifact\n\n")
    lines.append("Open and paste these into ChatGPT when you want **zero drift**:\n\n")
    lines.append("- `meta/GLOBAL_STATE.md`\n")
    lines.append("- `meta/global_state.json`\n\n")
    lines.append("Then ask: *“Validate wiring, identify missing enforcement links, and produce next actions.”*\n")

    OUT_MD.write_text("".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
