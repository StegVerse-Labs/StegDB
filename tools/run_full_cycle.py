#!/usr/bin/env python3
"""
StegDB Full Cycle driver (multi-repo aware, MEGA mode).

For each configured repo:

  1) Export canonical snapshot (repo-specific script)
  2) Generate per-repo metadata files.jsonl
  3) Ingest all repos into meta/aggregated_files.jsonl
  4) Run repair_repos.py to generate repair plans
  5) Evaluate cross-repo dependency status

Usage:

  python tools/run_full_cycle.py --all
  python tools/run_full_cycle.py --repo CosDen
"""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Dict, Any, Iterable


STEGBDB_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = STEGBDB_ROOT / "tools" / "repos_config.json"


def load_config() -> Dict[str, Any]:
    with CONFIG_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def run(cmd: Iterable[str], cwd: Path | None = None) -> None:
    cmd_list = list(cmd)
    print(f"▶ Running: {' '.join(cmd_list)} (cwd={cwd or STEGBDB_ROOT})")
    subprocess.run(cmd_list, cwd=str(cwd or STEGBDB_ROOT), check=True)


def export_canonical(repo_name: str, cfg: Dict[str, Any]) -> None:
    local_clone = cfg["local_clone_dir"]

    if repo_name == "CosDen":
        script = STEGBDB_ROOT / "export_cosden_canonical.py"
        if not script.exists():
            print("⚠ export_cosden_canonical.py missing; skipping export.")
            return
        run(
            [
                "python",
                str(script),
                "--cosden-root",
                str((STEGBDB_ROOT / local_clone).resolve()),
            ],
            cwd=STEGBDB_ROOT,
        )
    else:
        print(f"⚠ No canonical export script wired for repo {repo_name}, skipping.")


def generate_metadata(repo_name: str, cfg: Dict[str, Any]) -> None:
    local_clone = cfg["local_clone_dir"]
    metadata_file = cfg["metadata_file"]

    run(
        [
            "python",
            "tools/generate_repo_metadata.py",
            "--repo-name",
            repo_name,
            "--repo-root",
            str(STEGBDB_ROOT / local_clone),
            "--output",
            metadata_file,
        ],
        cwd=STEGBDB_ROOT,
    )


def ingest_all_metadata() -> None:
    run(["python", "tools/ingest_repo_metadata.py"], cwd=STEGBDB_ROOT)


def run_repairs() -> None:
    script = STEGBDB_ROOT / "tools" / "repair_repos.py"
    if not script.exists():
        print("⚠ repair_repos.py not found; skipping repairs.")
        return
    run(["python", "tools/repair_repos.py"], cwd=STEGBDB_ROOT)


def evaluate_dependencies() -> None:
    script = STEGBDB_ROOT / "tools" / "evaluate_dependencies.py"
    if not script.exists():
        print("⚠ evaluate_dependencies.py not found; skipping dependency evaluation.")
        return
    run(["python", "tools/evaluate_dependencies.py"], cwd=STEGBDB_ROOT)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument("--all", action="store_true")
    group.add_argument("--repo", help="Single repo name (e.g., CosDen)")
    return p.parse_args()


def main() -> None:
    cfg = load_config()
    args = parse_args()

    if args.all:
        target_repos = list(cfg.keys())
    else:
        if args.repo not in cfg:
            raise SystemExit(f"Unknown repo {args.repo!r} (not in repos_config.json).")
        target_repos = [args.repo]

    print("🧠 StegDB Full Cycle (MEGA)")
    print(f"   Repos: {', '.join(target_repos)}")
    print()

    for repo_name in target_repos:
        rcfg = cfg[repo_name]
        print(f"===== {repo_name}: export canonical =====")
        export_canonical(repo_name, rcfg)

        print(f"===== {repo_name}: generate metadata =====")
        generate_metadata(repo_name, rcfg)
        print()

    print("===== Ingest all repo metadata =====")
    ingest_all_metadata()

    print("===== Run repair engine =====")
    run_repairs()

    print("===== Evaluate cross-repo dependencies =====")
    evaluate_dependencies()

    print("✅ Full cycle complete.")


if __name__ == "__main__":
    main()
