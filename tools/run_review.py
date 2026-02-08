#!/usr/bin/env python3
"""
StegDB Review Runner

Read-only repository review executor.
Produces human + machine review artifacts without modifying any repo.

This tool intentionally does NOT:
- sync canonicals
- repair repos
- open PRs
- write outside stegdb_review/

It exists to prevent trivial human error from becoming systemic drift.
"""

from pathlib import Path
from datetime import datetime, timezone
import yaml
import json
import sys


ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / "schemas"
OUT = ROOT / "stegdb_review"


def utc_now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_yaml(path: Path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def exists(repo_path: Path, name: str) -> bool:
    return (repo_path / name).exists()


def main():
    if len(sys.argv) < 3:
        print("Usage: run_review.py <review.yml> <target_repo_path>")
        sys.exit(1)

    review_path = Path(sys.argv[1]).resolve()
    target_repo = Path(sys.argv[2]).resolve()

    review = load_yaml(review_path)
    repo = review["repo"]
    checks = review["checks"]["minimum_standard_v1"]

    required = ["README.md"]
    if checks.get("require_status_md", True):
        required.append("STATUS.md")
    if checks.get("repo_type") == "template":
        required.append("WELCOME.md")

    missing_required = [f for f in required if not exists(target_repo, f)]

    serious_failures = []
    rationale = []

    if "README.md" in missing_required:
        serious_failures.append("Missing README.md (no entry point)")
        rationale.append("README.md missing")

    if "WELCOME.md" in missing_required:
        rationale.append("WELCOME.md missing for template repo")

    confidence = "green"
    if serious_failures:
        confidence = "red"
    elif missing_required:
        confidence = "yellow"

    OUT.mkdir(exist_ok=True)

    result = {
        "schema_name": "stegdb_repo_review_result",
        "schema_version": "1.0.0",
        "repo": {
            "owner": repo["owner"],
            "name": repo["name"],
            "default_branch": repo.get("default_branch", "main"),
            "reviewed_at_utc": utc_now(),
        },
        "summary": {
            "confidence_signal": confidence,
            "serious_failures_detected": bool(serious_failures),
            "rationale": rationale,
        },
        "minimum_standard_v1": {
            "passes": not bool(missing_required),
            "missing_required": missing_required,
        },
        "failure_modes": {
            "serious": serious_failures,
            "moderate": [],
            "low": [],
        },
    }

    (OUT / "result.yml").write_text(yaml.safe_dump(result, sort_keys=False))
    (OUT / "result.json").write_text(json.dumps(result, indent=2))

    report = f"""# StegDB Review Report

Repo: {repo['owner']}/{repo['name']}
Reviewed at: {result['repo']['reviewed_at_utc']}

Confidence: {confidence.upper()}

Rationale:
{chr(10).join(f"- {r}" for r in rationale) if rationale else "- No issues detected"}

Serious failures:
{chr(10).join(f"- {s}" for s in serious_failures) if serious_failures else "- None"}
"""

    (OUT / "report.md").write_text(report)
    print("Review complete:", confidence.upper())


if __name__ == "__main__":
    main()
