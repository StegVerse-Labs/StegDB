#!/usr/bin/env python3
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

def run(label, cmd):
    print(f"\n===== {label} =====")
    subprocess.run(cmd, cwd=str(ROOT), check=True)

def main():
    cosden_root = ROOT / "CosDen"
    repos_dir = ROOT / "repos" / "CosDen"
    meta_dir = ROOT / "meta"

    # 1. Export canonical CosDen set
    run(
        "CosDen: export canonical",
        ["python", "export_cosden_canonical.py", "--cosden-root", str(cosden_root)]
    )

    # 2. Generate metadata for CosDen
    run(
        "CosDen: generate metadata",
        [
            "python",
            "tools/generate_repo_metadata.py",
            "--repo-name", "CosDen",
            "--repo-root", str(cosden_root),
            "--output", str(repos_dir / "files.jsonl"),
        ]
    )

    # 3. Ingest metadata for all repos
    run(
        "Ingest all repo metadata",
        ["python", "tools/ingest_repo_metadata.py"]
    )

    # 4. Run repair engine
    run(
        "Run repair engine",
        ["python", "tools/repair_repos.py"]
    )

    # 5. Evaluate repo dependencies  **THIS WAS MISSING**
    run(
        "Evaluate dependency status",
        ["python", "tools/evaluate_dependencies.py"]
    )

    print("\n✔ Full cycle complete.")

if __name__ == "__main__":
    main()
