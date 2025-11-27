#!/usr/bin/env python3

from __future__ import annotations
import argparse
import json
import subprocess
from pathlib import Path
from typing import Dict, Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "tools" / "repos_config.json"

def run(cmd: Iterable[str], cwd: Path | None = None):
    cmd = list(cmd)
    subprocess.run(cmd, cwd=str(cwd or ROOT), check=True)

def load_config() -> Dict[str, Any]:
    with open(CONFIG, "r", encoding="utf-8") as f:
        return json.load(f)

def export(repo: str, cfg: Dict[str, Any]):
    if repo == "CosDen":
        script = ROOT / "export_cosden_canonical.py"
        if not script.exists():
            print("⚠ Missing export script")
            return
        run(["python", str(script), "--cosden-root", str(ROOT / cfg["local_clone_dir"])])

def gen_meta(repo: str, cfg: Dict[str, Any]):
    run([
        "python",
        "tools/generate_repo_metadata.py",
        "--repo-name", repo,
        "--repo-root", str(ROOT / cfg["local_clone_dir"]),
        "--output", cfg["metadata_file"]
    ])

def ingest():
    run(["python", "tools/ingest_repo_metadata.py"])

def repair():
    run(["python", "tools/repair_repos.py"])

def deps():
    run(["python", "tools/evaluate_dependencies.py"])

def main():
    cfg = load_config()

    print("🧠 StegDB Full Cycle")

    for repo, rcfg in cfg.items():
        print(f"--- {repo}: export ---")
        export(repo, rcfg)
        print(f"--- {repo}: metadata ---")
        gen_meta(repo, rcfg)

    print("--- ingest all ---")
    ingest()

    print("--- repair ---")
    repair()

    print("--- deps ---")
    deps()

    print("✅ Full cycle done.")

if __name__ == "__main__":
    main()
