#!/usr/bin/env python3
"""
Evaluate cross-repo dependency status for StegDB.

Reads:
  - tools/repos_config.json
  - tools/dependency_graph.json
  - <local_clone_dir>/meta/validation_stamp.json (per repo)

Writes:
  - meta/dependency_status.json
"""

from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any

STEGBDB_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = STEGBDB_ROOT / "tools" / "repos_config.json"
GRAPH_PATH = STEGBDB_ROOT / "tools" / "dependency_graph.json"
META_DIR = STEGBDB_ROOT / "meta"
DEPS_STATUS_PATH = META_DIR / "dependency_status.json"


@dataclass
class RepoStatus:
    name: str
    self_status: str        # "prod", "build", "no_stamp", "not_cloned", "unconfigured"
    highest_mode: str | None
    has_stamp: bool
    dependencies: List[str]
    deps_ok: bool
    problems: List[str]


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def eval_repo(
    name: str,
    cfg: Dict[str, Any] | None,
    deps: List[str],
) -> RepoStatus:
    if cfg is None:
        return RepoStatus(
            name=name,
            self_status="unconfigured",
            highest_mode=None,
            has_stamp=False,
            dependencies=deps,
            deps_ok=False,
            problems=[f"{name} in dependency_graph.json but not in repos_config.json"],
        )

    local_dir = STEGBDB_ROOT / cfg["local_clone_dir"]
    stamp_path = local_dir / "meta" / "validation_stamp.json"

    if not local_dir.exists():
        return RepoStatus(
            name=name,
            self_status="not_cloned",
            highest_mode=None,
            has_stamp=False,
            dependencies=deps,
            deps_ok=False if deps else True,
            problems=[f"Local clone directory missing: {local_dir}"],
        )

    if not stamp_path.exists():
        return RepoStatus(
            name=name,
            self_status="no_stamp",
            highest_mode=None,
            has_stamp=False,
            dependencies=deps,
            deps_ok=False if deps else True,
            problems=[f"validation_stamp.json missing in {local_dir}/meta"],
        )

    with stamp_path.open("r", encoding="utf-8") as f:
        stamp = json.load(f)

    highest_mode = stamp.get("highest_mode")
    problems: List[str] = []

    if highest_mode == "prod":
        self_status = "prod"
    elif highest_mode == "build":
        self_status = "build"
        problems.append("Repo only validated in build mode, not prod.")
    else:
        self_status = "unknown"
        problems.append(f"Unknown highest_mode in stamp: {highest_mode!r}")

    return RepoStatus(
        name=name,
        self_status=self_status,
        highest_mode=highest_mode,
        has_stamp=True,
        dependencies=deps,
        deps_ok=True,  # filled in later
        problems=problems,
    )


def evaluate() -> None:
    META_DIR.mkdir(exist_ok=True)

    cfg_all = load_json(CONFIG_PATH)
    graph = load_json(GRAPH_PATH)

    statuses: Dict[str, RepoStatus] = {}

    # first pass: individual repos
    for repo_name, deps in graph.items():
        cfg = cfg_all.get(repo_name)
        statuses[repo_name] = eval_repo(repo_name, cfg, list(deps))

    # second pass: dependency satisfaction
    for repo_name, st in statuses.items():
        deps_ok = True
        for dep in st.dependencies:
            dep_status = statuses.get(dep)
            if dep_status is None:
                deps_ok = False
                st.problems.append(f"Dependency {dep} not present in statuses.")
                continue
            if dep_status.self_status != "prod":
                deps_ok = False
                st.problems.append(
                    f"Dependency {dep} is not prod (status={dep_status.self_status})."
                )
        st.deps_ok = deps_ok

    out = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "repos": {
            name: {k: v for k, v in asdict(status).items() if k != "name"}
            for name, status in statuses.items()
        },
    }

    with DEPS_STATUS_PATH.open("w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)

    print(f"✅ Wrote dependency status to {DEPS_STATUS_PATH}")


def main() -> None:
    if not CONFIG_PATH.exists():
        raise SystemExit(f"Missing repos_config.json at {CONFIG_PATH}")
    if not GRAPH_PATH.exists():
        raise SystemExit(f"Missing dependency_graph.json at {GRAPH_PATH}")
    evaluate()


if __name__ == "__main__":
    main()
