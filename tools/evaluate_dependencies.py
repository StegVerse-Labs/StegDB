#!/usr/bin/env python3
"""
Evaluate cross-repo dependency status for StegDB.

Reads:
  - tools/repos_config.json
  - tools/dependency_graph.json
  - <repo>/meta/validation_stamp.json

Writes:
  - meta/dependency_status.json
"""

from __future__ import annotations
import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any

ROOT = Path(__file__).resolve().parents[1]
CFG = ROOT / "tools" / "repos_config.json"
GRAPH = ROOT / "tools" / "dependency_graph.json"
META = ROOT / "meta"
OUTFILE = META / "dependency_status.json"

@dataclass
class RepoStatus:
    name: str
    self_status: str
    highest_mode: str | None
    has_stamp: bool
    dependencies: List[str]
    deps_ok: bool
    problems: List[str]

def load_json(path: Path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def evaluate_repo(name: str, cfg: Dict[str, Any] | None, deps: List[str]) -> RepoStatus:
    if cfg is None:
        return RepoStatus(
            name=name,
            self_status="unconfigured",
            highest_mode=None,
            has_stamp=False,
            dependencies=deps,
            deps_ok=False,
            problems=[f"{name} not in repos_config.json"]
        )

    repo_root = ROOT / cfg["local_clone_dir"]
    stamp = repo_root / "meta" / "validation_stamp.json"

    if not repo_root.exists():
        return RepoStatus(
            name=name,
            self_status="not_cloned",
            highest_mode=None,
            has_stamp=False,
            dependencies=deps,
            deps_ok=False,
            problems=[f"Missing clone: {repo_root}"]
        )

    if not stamp.exists():
        return RepoStatus(
            name=name,
            self_status="no_stamp",
            highest_mode=None,
            has_stamp=False,
            dependencies=deps,
            deps_ok=False,
            problems=["Missing validation_stamp.json"]
        )

    data = load_json(stamp)
    mode = data.get("highest_mode", None)
    problems = []
    status = "unknown"

    if mode == "prod":
        status = "prod"
    elif mode == "build":
        status = "build"
        problems.append("Repo validated only in build mode.")
    else:
        problems.append(f"Invalid mode: {mode}")

    return RepoStatus(
        name=name,
        self_status=status,
        highest_mode=mode,
        has_stamp=True,
        dependencies=deps,
        deps_ok=True,
        problems=problems
    )

def main():
    META.mkdir(exist_ok=True)

    cfg = load_json(CFG)
    graph = load_json(GRAPH)

    statuses = {}

    for repo, deps in graph.items():
        statuses[repo] = evaluate_repo(repo, cfg.get(repo), deps)

    # Evaluate dependency success
    for repo, st in statuses.items():
        ok = True
        for dep in st.dependencies:
            dep_st = statuses.get(dep)
            if not dep_st or dep_st.self_status != "prod":
                ok = False
                st.problems.append(f"Dependency {dep} not prod.")
        st.deps_ok = ok

    out = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "repos": {
            name: {k: v for k, v in asdict(st).items() if k != "name"}
            for name, st in statuses.items()
        }
    }

    with open(OUTFILE, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)

    print(f"✅ Wrote {OUTFILE}")

if __name__ == "__main__":
    main()
