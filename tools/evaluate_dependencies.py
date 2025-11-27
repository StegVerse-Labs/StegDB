#!/usr/bin/env python3
"""
Evaluate cross-repo dependency status for StegDB.

Reads:
  - tools/repos_config.json
  - tools/dependency_graph.json
  - <repo_root>/meta/validation_stamp.json for each repo

Writes:
  - meta/dependency_status.json

This is what StegGuard uses to decide if a repo (e.g., CosDen)
is allowed to go to PROD.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any


ROOT = Path(__file__).resolve().parents[1]
REPOS_CONFIG = ROOT / "tools" / "repos_config.json"
DEPS_GRAPH = ROOT / "tools" / "dependency_graph.json"
META_DIR = ROOT / "meta"
OUTPUT = META_DIR / "dependency_status.json"


@dataclass
class RepoStatus:
    name: str
    self_status: str          # prod | build | no_stamp | not_cloned | unconfigured | unknown
    highest_mode: str | None
    has_stamp: bool
    dependencies: List[str]
    deps_ok: bool
    problems: List[str]


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def evaluate_single_repo(
    name: str,
    cfg: Dict[str, Any] | None,
    deps: List[str],
) -> RepoStatus:
    """Work out the *local* status of one repo (ignoring its dependencies)."""

    if cfg is None:
        return RepoStatus(
            name=name,
            self_status="unconfigured",
            highest_mode=None,
            has_stamp=False,
            dependencies=deps,
            deps_ok=False,
            problems=[f"{name} appears in dependency_graph.json but not repos_config.json"],
        )

    repo_root = ROOT / cfg["local_clone_dir"]
    stamp_path = repo_root / "meta" / "validation_stamp.json"

    if not repo_root.exists():
        return RepoStatus(
            name=name,
            self_status="not_cloned",
            highest_mode=None,
            has_stamp=False,
            dependencies=deps,
            deps_ok=False,
            problems=[f"Local clone directory missing: {repo_root}"],
        )

    if not stamp_path.exists():
        return RepoStatus(
            name=name,
            self_status="no_stamp",
            highest_mode=None,
            has_stamp=False,
            dependencies=deps,
            deps_ok=False,
            problems=[f"validation_stamp.json missing under {repo_root / 'meta'}"],
        )

    data = load_json(stamp_path)
    mode = data.get("highest_mode")
    problems: List[str] = []

    if mode == "prod":
        status = "prod"
    elif mode == "build":
        status = "build"
        problems.append("Repo only validated in build mode (not prod).")
    else:
        status = "unknown"
        problems.append(f"Unknown or missing highest_mode in stamp: {mode!r}")

    return RepoStatus(
        name=name,
        self_status=status,
        highest_mode=mode,
        has_stamp=True,
        dependencies=deps,
        deps_ok=True,  # will be updated when we check dependencies
        problems=problems,
    )


def main() -> None:
    if not REPOS_CONFIG.exists():
        raise SystemExit(f"Missing repos_config.json at {REPOS_CONFIG}")
    if not DEPS_GRAPH.exists():
        raise SystemExit(f"Missing dependency_graph.json at {DEPS_GRAPH}")

    META_DIR.mkdir(exist_ok=True)

    cfg_all: Dict[str, Any] = load_json(REPOS_CONFIG)
    graph: Dict[str, List[str]] = load_json(DEPS_GRAPH)

    # First pass: evaluate each repo by itself
    statuses: Dict[str, RepoStatus] = {}
    for repo_name, deps in graph.items():
        statuses[repo_name] = evaluate_single_repo(
            name=repo_name,
            cfg=cfg_all.get(repo_name),
            deps=list(deps),
        )

    # Second pass: check that each repo's dependencies are prod
    for repo_name, status in statuses.items():
        ok = True
        for dep_name in status.dependencies:
            dep_status = statuses.get(dep_name)
            if dep_status is None:
                ok = False
                status.problems.append(
                    f"Dependency {dep_name} is referenced but has no RepoStatus."
                )
                continue

            if dep_status.self_status != "prod":
                ok = False
                status.problems.append(
                    f"Dependency {dep_name} is not prod (status={dep_status.self_status})."
                )

        status.deps_ok = ok

    output = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "repos": {
            name: {k: v for k, v in asdict(st).items() if k != "name"}
            for name, st in statuses.items()
        },
    }

    with OUTPUT.open("w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)

    print(f"✅ Wrote dependency status to {OUTPUT}")


if __name__ == "__main__":
    main()
