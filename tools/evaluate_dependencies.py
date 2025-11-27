#!/usr/bin/env python3
"""
StegDB multi-repo dependency evaluator.

Inputs:
- meta/aggregated_files.jsonl  (from full-cycle)
- tools/repos_config.json      (declares known repos)

Output:
- meta/dependency_status.json
"""

import json
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent.parent
META = ROOT / "meta"
TOOLS = ROOT / "tools"
NOW = datetime.now(timezone.utc).isoformat()


def load_json(path: Path):
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        return {"_error": f"failed_to_parse:{type(e).__name__}", "_details": str(e)}


def count_aggregated_records() -> int:
    agg = META / "aggregated_files.jsonl"
    if not agg.is_file():
        return 0
    return sum(1 for _ in agg.open("r", encoding="utf-8"))


def load_repos_config():
    cfg_path = TOOLS / "repos_config.json"
    cfg = load_json(cfg_path) or {}
    return cfg.get("repos") or {}


def evaluate():
    repos_cfg = load_repos_config()
    aggregated_count = count_aggregated_records()

    issues = []
    repos_status = {}

    if not repos_cfg:
        issues.append({
            "repo": "_stegdb",
            "severity": "warning",
            "message": "repos_config.json is empty or missing; no multi-repo deps defined."
        })

    # Very simple signal for now:
    # - if aggregated_files.jsonl is missing / empty, global is "degraded"
    # - per-repo we just mark "unknown" but include that as a warning
    if aggregated_count == 0:
        issues.append({
            "repo": "_stegdb",
            "severity": "error",
            "message": "aggregated_files.jsonl missing or empty; run full-cycle in StegDB."
        })
        global_ok = False
    else:
        global_ok = True

    for name, cfg in repos_cfg.items():
        critical = bool(cfg.get("critical", False))

        # For now we only know that the repo is registered; we’ll refine later
        status = "ok" if aggregated_count > 0 else "unknown"

        repos_status[name] = {
            "status": status,
            "critical": critical,
        }

        if critical and aggregated_count == 0:
            issues.append({
                "repo": name,
                "severity": "error",
                "message": "critical repo registered but no aggregated metadata present."
            })
            global_ok = False

    result = {
        "generated_at": NOW,
        "global_ok": global_ok,
        "aggregated_records": aggregated_count,
        "repos": repos_status,
        "issues": issues,
    }

    META.mkdir(parents=True, exist_ok=True)
    (META / "dependency_status.json").write_text(
        json.dumps(result, indent=2), encoding="utf-8"
    )

    print(f"[StegDB] Wrote dependency_status.json (global_ok={global_ok})")


if __name__ == "__main__":
    evaluate()
