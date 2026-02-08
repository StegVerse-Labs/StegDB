#!/usr/bin/env python3
"""
StegDB Review Runner (read-only)

Reads a StegDB review spec and a checked-out target repo folder,
then produces review artifacts under --out (default: stegdb_review).

Non-destructive: does not modify the target repo, does not create PRs,
does not sync canonicals.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Dict, List

import yaml


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_yaml(path: Path) -> Dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def write_yaml(path: Path, data: Dict[str, Any]) -> None:
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def exists(repo_path: Path, rel: str) -> bool:
    return (repo_path / rel).exists()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--review", required=True, help="Path to review.yml inside StegDB workspace")
    ap.add_argument("--target", required=True, help="Path to checked-out target repo folder")
    ap.add_argument("--out", default="stegdb_review", help="Output folder for review artifacts")
    args = ap.parse_args()

    review_path = Path(args.review).resolve()
    target_repo = Path(args.target).resolve()
    out_dir = Path(args.out).resolve()

    if not review_path.exists():
        raise FileNotFoundError(f"Review file not found: {review_path}")

    if not target_repo.exists():
        raise FileNotFoundError(f"Target repo folder not found: {target_repo}")

    review = load_yaml(review_path)
    repo = review.get("repo", {})
    checks = review.get("checks", {})

    # --- Minimum Standard v1 gates (Option C) ---
    minstd = checks.get("minimum_standard_v1", {})
    repo_type = minstd.get("repo_type", "unknown")

    required_files: List[str] = ["README.md"]

    # Template repos should have WELCOME.md
    if repo_type == "template":
        required_files.append("WELCOME.md")

    # require_status_md defaults to true
    if minstd.get("require_status_md", True):
        required_files.append("STATUS.md")

    missing_required = [f for f in required_files if not exists(target_repo, f)]

    # --- Serious failure definitions ---
    serious_failures: List[str] = []

    # Hard serious failures for first-contact
    if "README.md" in missing_required:
        serious_failures.append("User cannot open/read core docs (README missing)")

    if repo_type == "template" and "WELCOME.md" in missing_required:
        serious_failures.append("New user cannot find a start path in under 60 seconds (WELCOME missing)")

    if "STATUS.md" in missing_required:
        # Usually moderate, but you can treat as serious if you want.
        # Keeping it moderate by default to avoid over-blocking.
        pass

    confidence = "green"
    if serious_failures:
        confidence = "red"
    elif missing_required:
        confidence = "yellow"

    # --- Build result object ---
    result: Dict[str, Any] = {
        "schema_name": "stegdb_repo_review_result",
        "schema_version": "1.0.0",
        "repo": {
            "owner": repo.get("owner", "unknown"),
            "name": repo.get("name", "unknown"),
            "default_branch": repo.get("default_branch", "main"),
            "reviewed_at_utc": utc_now(),
        },
        "summary": {
            "confidence_signal": confidence,
            "serious_failures_detected": bool(serious_failures),
            "rationale": [],
        },
        "minimum_standard_v1": {
            "passes": len(missing_required) == 0 and not serious_failures,
            "repo_type": repo_type,
            "missing_required": missing_required,
            "notes": [],
        },
        "first_contact": {
            "passes": not any("start path" in s.lower() for s in serious_failures),
            "issues": [],
            "recommended_additions": [],
        },
        "failure_modes": {
            "serious": serious_failures,
            "moderate": [],
            "low": [],
        },
        "suggested_patches": {
            "available": False,
            "path": "stegdb_review/suggested_patches/",
            "notes": ["Patch generation not enabled in this runner yet"],
        },
    }

    if missing_required:
        result["summary"]["rationale"].append(f"Missing required files: {', '.join(missing_required)}")
        if "STATUS.md" in missing_required:
            result["failure_modes"]["moderate"].append("STATUS.md missing (project state not declared)")
            result["summary"]["rationale"].append("STATUS.md missing")
    else:
        result["summary"]["rationale"].append("Minimum required first-contact files present")

    # --- Write outputs ---
    out_dir.mkdir(parents=True, exist_ok=True)

    write_yaml(out_dir / "result.yml", result)
    (out_dir / "result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")

    report_md = f"""# StegDB Review Report

Repo: {result['repo']['owner']}/{result['repo']['name']}
Reviewed at (UTC): {result['repo']['reviewed_at_utc']}

Confidence: **{confidence.upper()}**
Serious failures detected: **{str(result['summary']['serious_failures_detected']).lower()}**

## Rationale
""" + "\n".join(f"- {r}" for r in result["summary"]["rationale"]) + """

## Missing required (Minimum Standard)
""" + ("\n".join(f"- {f}" for f in missing_required) if missing_required else "- None") + """

## Serious failure modes
""" + ("\n".join(f"- {s}" for s in serious_failures) if serious_failures else "- None") + "\n"

    (out_dir / "report.md").write_text(report_md, encoding="utf-8")

    print(f"[StegDB] Review file: {review_path}")
    print(f"[StegDB] Target repo: {target_repo}")
    print(f"[StegDB] Output dir:  {out_dir}")
    print(f"[StegDB] Confidence: {confidence.upper()}")


if __name__ == "__main__":
    main()
