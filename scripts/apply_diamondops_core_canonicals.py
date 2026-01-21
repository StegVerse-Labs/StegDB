#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
from pathlib import Path


def sh(cmd: list[str], cwd: Path | None = None) -> None:
    print("+", " ".join(cmd))
    subprocess.check_call(cmd, cwd=str(cwd) if cwd else None)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--diamondops-core", required=True, help="Path to a checked-out DiamondOps-Core repo")
    ap.add_argument("--repo-root", default=".", help="Target repo root (default: current repo)")
    ap.add_argument("--repo-name", default="StegDB", help="Repo name for template substitution")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    repo_root = Path(args.repo_root).resolve()
    diamondops = Path(args.diamondops_core).resolve()

    cmd = [
        "python",
        "tools/sync_canonical_docs.py",
        "--registry",
        "registry/diamondops_core_canonical_docs.json",
        "--source-root",
        str(diamondops),
        "--repo-root",
        str(repo_root),
        "--repo-name",
        args.repo_name,
    ]
    if args.dry_run:
        cmd.append("--dry-run")

    sh(cmd, cwd=repo_root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
