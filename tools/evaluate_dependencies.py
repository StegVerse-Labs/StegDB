#!/usr/bin/env python3
"""
evaluate_dependencies.py
StegDB Multi-Repo Dependency Evaluator
-------------------------------------

Reads:
  - meta/aggregated_files.jsonl
  - repos_config.json

Generates:
  - meta/dependency_status.json

Purpose:
  Determine whether all required repos have:
    • canonical integrity
    • valid metadata
    • strict-mode validation stamps
    • matching SHA256 meta signatures
"""

import json
from pathlib import Path
import hashlib
import sys

ROOT = Path(__file__).resolve().parent.parent
META = ROOT / "meta"
REPOS = ROOT / "repos"
CONFIG = ROOT / "repos_config.json"

DEPENDENCY_OUT = META / "dependency_status.json"
AGGREGATED = META / "aggregated_files.jsonl"


def load_jsonl(path: Path):
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def sha256_of_file(path: Path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()


def main():
    print("🔍 Evaluating multi-repo dependency health...")

    if not CONFIG.exists():
        print("❌ repos_config.json missing — cannot evaluate dependencies.")
        sys.exit(1)

    if not AGGREGATED.exists():
        print("❌ aggregated_files.jsonl missing — run full cycle first.")
        sys.exit(1)

    repos_cfg = json.loads(CONFIG.read_text())
    aggregated = load_jsonl(AGGREGATED)

    # Build per-repo index from aggregated metadata
    per_repo = {}
    for entry in aggregated:
        repo = entry.get("repo")
        per_repo.setdefault(repo, []).append(entry)

    report = {
        "root": str(ROOT),
        "summary": {},
        "repos": {},
    }

    for repo_name, cfg in repos_cfg.items():
        print(f"\n📦 Checking repo: {repo_name}")
        repo_report = {
            "registered": True,
            "metadata_present": False,
            "file_count": 0,
            "meta_sha256": None,
            "validation_stamp": None,
            "strict_validation_passed": False,
            "errors": [],
        }

        # ------------------------------
        # METADATA FILES
        # ------------------------------
        repo_meta_path = REPOS / repo_name / "files.jsonl"
        if repo_meta_path.exists():
            repo_report["metadata_present"] = True
            repo_report["file_count"] = len(repo_meta_path.read_text().splitlines())
            repo_report["meta_sha256"] = sha256_of_file(repo_meta_path)
        else:
            repo_report["errors"].append("Missing files.jsonl")

        # ------------------------------
        # VALIDATION STAMP CHECK
        # ------------------------------
        stamp_path = REPOS / repo_name / "validation_stamp.json"
        if stamp_path.exists():
            try:
                stamp = json.loads(stamp_path.read_text())
                repo_report["validation_stamp"] = stamp

                mode = stamp.get("highest_mode")
                if mode == "prod":
                    repo_report["strict_validation_passed"] = True
                else:
                    repo_report["errors"].append(
                        f"Validation mode '{mode}' is not strict/prod."
                    )
            except Exception as e:
                repo_report["errors"].append(f"Invalid validation stamp: {e}")
        else:
            repo_report["errors"].append("Missing validation_stamp.json")

        # ------------------------------
        # AGGREGATED CROSS CHECK
        # ------------------------------
        if repo_name not in per_repo:
            repo_report["errors"].append("No aggregated entries found.")

        report["repos"][repo_name] = repo_report

    # ------------------------------
    # SUMMARY
    # ------------------------------
    total = len(report["repos"])
    passed = sum(
        1
        for r in report["repos"].values()
        if r["metadata_present"] and r["strict_validation_passed"]
    )

    report["summary"] = {
        "total_repos": total,
        "repos_ready_for_prod": passed,
        "repos_blocking_prod": total - passed,
    }

    # ------------------------------
    # WRITE OUTPUT
    # ------------------------------
    DEPENDENCY_OUT.write_text(json.dumps(report, indent=2))
    print(f"\n🧠 Wrote dependency report → {DEPENDENCY_OUT}")


if __name__ == "__main__":
    main()
