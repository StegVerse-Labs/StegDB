#!/usr/bin/env python3
"""
StegDB Full Cycle driver.

For each repo in tools/repos_config.json:

  1) Export canonical snapshot (if supported)
  2) Generate per-repo metadata (files.jsonl)
  3) Ingest all repos into meta/aggregated_files.jsonl
  4) Run repair_repos.py to generate repair plans
  5) Evaluate cross-repo dependency status -> meta/dependency_status.json

This is what the stegdb-central GitHub Action should call.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Dict, Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
REPOS_CONFIG = ROOT / "tools" / "repos_config.json"


def load_config() -> Dict[str, Any]:
    with REPOS_CONFIG.open("r", encoding="utf-8") as f:
        return json.load(f)


def run(cmd: Iterable[str], cwd: Path | None = None) -> None:
    cmd_list = list(cmd)
    print(f"▶ {' '.join(cmd_list)}  (cwd={cwd or ROOT})")
    subprocess.run(cmd_list, cwd=str(cwd or ROOT), check=True)


def export_canonical(repo_name: str, cfg: Dict[str, Any]) -> None:
    """
    Repo-specific canonical export hook.
    Right now only CosDen has a custom script.
    """
    local_dir = ROOT / cfg["local_clone_dir"]

    if repo_name == "CosDen":
        script = ROOT / "export_cosden_canonical.py"
        if not script.exists():
            print("⚠ export_cosden_canonical.py missing; skipping export.")
            return
        run(
            [
                "python",
                str(script),
                "--cosden-root",
                str(local_dir),
            ],
            cwd=ROOT,
        )
    else:
        # For other repos we don't enforce a canonical export yet
        print(f"⚠ No canonical export wired for repo {repo_name}; skipping.")


def generate_metadata(repo_name: str, cfg: Dict[str, Any]) -> None:
    """
    Generate per-repo files.jsonl metadata.
    """
    local_dir = ROOT / cfg["local_clone_dir"]
    output = cfg["metadata_file"]

    run(
        [
            "python",
            "tools/generate_repo_metadata.py",
            "--repo-name",
            repo_name,
            "--repo-root",
            str(local_dir),
            "--output",
            output,
        ],
        cwd=ROOT,
    )


def ingest_all_metadata() -> None:
    """
    Merge all repo files.jsonl into meta/aggregated_files.jsonl.
    """
    run(["python", "tools/ingest_repo_metadata.py"], cwd=ROOT)


def run_repairs() -> None:
    """
    Let repair_repos.py look at aggregated metadata and produce repair plans.
    """
    script = ROOT / "tools" / "repair_repos.py"
    if not script.exists():
        print("⚠ repair_repos.py not found; skipping repairs.")
        return
    run(["python", "tools/repair_repos.py"], cwd=ROOT)


def evaluate_dependencies() -> None:
    """
    Produce meta/dependency_status.json for StegGuard.
    """
    script = ROOT / "tools" / "evaluate_dependencies.py"
    if not script.exists():
        print("⚠ evaluate_dependencies.py not found; skipping dependency evaluation.")
        return
    run(["python", "tools/evaluate_dependencies.py"], cwd=ROOT)


def main() -> None:
    cfg = load_config()

    print("🧠 StegDB Full Cycle")
    print(f"   Repos: {', '.join(cfg.keys())}")
    print()

    # Per-repo steps
    for repo_name, rcfg in cfg.items():
        print(f"===== {repo_name}: export canonical =====")
        export_canonical(repo_name, rcfg)

        print(f"===== {repo_name}: generate metadata =====")
        generate_metadata(repo_name, rcfg)
        print()

    # Global steps
    print("===== Ingest all repo metadata =====")
    ingest_all_metadata()
    print()

    print("===== Run repair engine =====")
    run_repairs()
    print()

    print("===== Evaluate cross-repo dependencies =====")
    evaluate_dependencies()
    print()

    print("✅ Full cycle complete.")


if __name__ == "__main__":
    main()
