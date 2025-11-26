#!/usr/bin/env python3
"""
StegDB Full Cycle Orchestrator
------------------------------

Runs the full pipeline for CosDen:

1) Export canonical CosDen files into StegDB
2) Generate meta/files.jsonl for CosDen
3) Ingest repo metadata from sibling repos
4) Generate repair plans (starting with CosDen)

Usage (from StegDB root):

    python tools/run_full_cycle.py

Or specify a custom CosDen location:

    python tools/run_full_cycle.py --cosden-root ../CosDen
"""

import argparse
import subprocess
from pathlib import Path

STEGBDB_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_COSDEN_ROOT = STEGBDB_ROOT.parent / "CosDen"


def run(cmd, cwd: Path) -> None:
    print(f"\n▶ Running: {' '.join(cmd)}  (in {cwd})")
    subprocess.run(cmd, cwd=str(cwd), check=True)
    print("   ✓ Done")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Run full StegDB cycle for CosDen."
    )
    parser.add_argument(
        "--cosden-root",
        type=str,
        default=str(DEFAULT_COSDEN_ROOT),
        help="Path to the CosDen repo (default: ../CosDen)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    cosden_root = Path(args.cosden_root).resolve()

    print("\n🌀 StegDB Full Cycle (CosDen)\n")
    print(f"CosDen root: {cosden_root}")
    print(f"StegDB root: {STEGBDB_ROOT}\n")

    # 1) Export canonical files from CosDen into StegDB
    run(
        ["python", "tools/export_cosden_canonical.py", "--cosden-root", str(cosden_root)],
        cwd=STEGBDB_ROOT,
    )

    # 2) Generate metadata for CosDen (meta/files.jsonl inside CosDen)
    run(
        ["python", "tools/generate_repo_metadata.py", "--repo-root", str(cosden_root), "--repo-name", "CosDen"],
        cwd=STEGBDB_ROOT,
    )

    # 3) Ingest repo metadata (from all repos with meta/files.jsonl)
    run(
        ["python", "tools/ingest_repo_metadata.py"],
        cwd=STEGBDB_ROOT,
    )

    # 4) Generate repair plans (CosDen for now)
    run(
        ["python", "tools/repair_repos.py"],
        cwd=STEGBDB_ROOT,
    )

    print("\n✅ Full cycle complete.\n")


if __name__ == "__main__":
    main()
