#!/usr/bin/env python
"""
StegDB Full Cycle driver.

Phases:
  1) Optional CosDen canonical export (if CosDen checkout is present)
  2) CosDen metadata generation into repos/CosDen/files.jsonl
  3) Ingest all repo metadata into meta/aggregated_files.jsonl
  4) Run repair engine (writes repairs/* as needed)
  5) Evaluate dependency status (multi-repo graph using repos_config.json)

The goal is "can’t-fail" behavior:
  - Missing CosDen checkout => skip canonical/metadata with warnings,
    but still ingest/repair/evaluate with whatever data exists.
"""

import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
TOOLS = ROOT / "tools"
REPOS_DIR = ROOT / "repos"
META_DIR = ROOT / "meta"
REPAIRS_DIR = ROOT / "repairs"


def run(cmd, cwd: Path | None = None) -> None:
    """Run a subprocess with basic logging."""
    if cwd is None:
        cwd = ROOT
    cmd_display = " ".join(cmd)
    print(f"\n▶ Running: {cmd_display}\n   cwd={cwd}", flush=True)
    subprocess.run(cmd, cwd=str(cwd), check=True)


def main() -> None:
    print("🧠 StegDB Full Cycle (CosDen-focused, org-aware)")
    print(f"StegDB root: {ROOT}")

    # ------------------------------------------------------------------
    # Phase 1: Canonical export for CosDen (if checkout exists)
    # ------------------------------------------------------------------
    cosden_root = ROOT / "CosDen"
    if cosden_root.exists():
        print("\n===== CosDen: export canonical =====")
        try:
            run(
                [
                    "python",
                    "export_cosden_canonical.py",
                    "--cosden-root",
                    str(cosden_root),
                ],
                cwd=ROOT,
            )
        except subprocess.CalledProcessError as e:
            # Don't hard-fail the whole brain; log and continue.
            print(
                f"⚠ CosDen canonical export failed with exit code {e.returncode}."
                " Continuing full cycle."
            )
    else:
        print(
            f"⚠ CosDen root not found at {cosden_root} — "
            "skipping canonical export."
        )

    # ------------------------------------------------------------------
    # Phase 2: Generate metadata for CosDen into repos/CosDen/files.jsonl
    #         (Only if CosDen checkout is present.)
    # ------------------------------------------------------------------
    if cosden_root.exists():
        print("\n===== CosDen: generate metadata =====")
        cosden_meta_dir = REPOS_DIR / "CosDen"
        cosden_meta_dir.mkdir(parents=True, exist_ok=True)

        try:
            run(
                [
                    "python",
                    "tools/generate_repo_metadata.py",
                    "--repo-name",
                    "CosDen",
                    "--repo-root",
                    str(cosden_root),
                    "--output",
                    str(cosden_meta_dir / "files.jsonl"),
                ],
                cwd=ROOT,
            )
        except subprocess.CalledProcessError as e:
            print(
                f"⚠ CosDen metadata generation failed with exit code {e.returncode}."
                " Continuing with whatever metadata already exists."
            )
    else:
        print(
            "⚠ Skipping CosDen metadata generation because CosDen checkout is missing."
        )

    # ------------------------------------------------------------------
    # Phase 3: Ingest all repo metadata into meta/aggregated_files.jsonl
    #          (Whatever repos/*/files.jsonl exist will be aggregated.)
    # ------------------------------------------------------------------
    print("\n===== Ingest all repo metadata =====")
    META_DIR.mkdir(exist_ok=True)
    try:
        run(["python", "tools/ingest_repo_metadata.py"], cwd=ROOT)
    except subprocess.CalledProcessError as e:
        print(
            f"⚠ Metadata ingest failed with exit code {e.returncode}."
            " Continuing to repair/evaluate phases."
        )

    # ------------------------------------------------------------------
    # Phase 4: Run repair engine
    # ------------------------------------------------------------------
    print("\n===== Run repair engine =====")
    REPAIRS_DIR.mkdir(exist_ok=True)
    try:
        run(["python", "tools/repair_repos.py"], cwd=ROOT)
    except subprocess.CalledProcessError as e:
        print(
            f"⚠ Repair engine failed with exit code {e.returncode}."
            " Continuing to dependency evaluation."
        )

    # ------------------------------------------------------------------
    # Phase 5: Evaluate dependency status (multi-repo graph)
    #          Uses:
    #            - tools/repos_config.json  (auto-generated in workflow)
    #            - meta/aggregated_files.jsonl (if present)
    #          Writes:
    #            - tools/dependency_graph.json
    #            - meta/dependency_status.json
    # ------------------------------------------------------------------
    print("\n===== Evaluate dependency status =====")
    try:
        run(["python", "tools/evaluate_dependencies.py"], cwd=ROOT)
    except subprocess.CalledProcessError as e:
        print(
            f"⚠ Dependency evaluation failed with exit code {e.returncode}."
            " Full cycle will still finish."
        )

    print("\n✅ Full cycle complete.\n")


if __name__ == "__main__":
    main()
