#!/usr/bin/env python
"""
Evaluate multi-repo dependency health for StegDB.

- Reads:
    - meta/aggregated_files.jsonl      (per-file metadata across repos)
    - tools/repos_config.json          (declared repos + dependencies)
- Writes:
    - tools/dependency_graph.json      (graph of repos + edges)
    - meta/dependency_status.json      (high-level health summary)

If repos_config.json is missing, this script will emit a WARNING and
exit with status 0 so StegDB full-cycle is not blocked.
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Set, Any


ROOT = Path(__file__).resolve().parent.parent
META_DIR = ROOT / "meta"
TOOLS_DIR = ROOT / "tools"

AGGREGATED_FILES = META_DIR / "aggregated_files.jsonl"

# We’ll look for repos_config.json in multiple places to be resilient
REPOS_CONFIG_CANDIDATES = [
    TOOLS_DIR / "repos_config.json",
    ROOT / "repos_config.json",
]

DEPENDENCY_GRAPH_JSON = TOOLS_DIR / "dependency_graph.json"
DEPENDENCY_STATUS_JSON = META_DIR / "dependency_status.json"


@dataclass
class RepoNode:
    name: str
    path: str
    depends_on: List[str]
    files: List[str]


def _load_repos_config() -> Dict[str, Any] | None:
    """Return parsed repos_config, or None if not found."""
    for candidate in REPOS_CONFIG_CANDIDATES:
        if candidate.is_file():
            print(f"✅ Using repos_config.json at: {candidate}")
            with candidate.open("r", encoding="utf-8") as f:
                return json.load(f)

    print("⚠️  repos_config.json missing at any of these locations:")
    for c in REPOS_CONFIG_CANDIDATES:
        print(f"   - {c}")
    return None


def _load_aggregated_files() -> List[Dict[str, Any]]:
    if not AGGREGATED_FILES.is_file():
        print(f"⚠️  No aggregated_files.jsonl found at {AGGREGATED_FILES}")
        return []

    records: List[Dict[str, Any]] = []
    with AGGREGATED_FILES.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                print(f"⚠️  Skipping malformed JSON line in {AGGREGATED_FILES}")
    print(f"📄 Loaded {len(records)} aggregated file records.")
    return records


def _build_repo_nodes(
    repos_cfg: Dict[str, Any], aggregated: List[Dict[str, Any]]
) -> Dict[str, RepoNode]:
    """Join declared repos with the files we know about from aggregated metadata."""

    repo_defs = repos_cfg.get("repos", [])
    nodes: Dict[str, RepoNode] = {}

    # index aggregated files by repo name
    files_by_repo: Dict[str, List[str]] = {}
    for rec in aggregated:
        repo = rec.get("repo")
        path = rec.get("path")
        if not repo or not path:
            continue
        files_by_repo.setdefault(repo, []).append(path)

    for repo in repo_defs:
        name = repo["name"]
        path = repo.get("path", "")
        depends_on = repo.get("depends_on", [])
        files = files_by_repo.get(name, [])
        nodes[name] = RepoNode(
            name=name,
            path=path,
            depends_on=depends_on,
            files=files,
        )

    return nodes


def _detect_cycles(nodes: Dict[str, RepoNode]) -> List[List[str]]:
    """Simple cycle detection in the dependency graph."""
    graph: Dict[str, List[str]] = {
        name: node.depends_on for name, node in nodes.items()
    }

    visited: Set[str] = set()
    stack: Set[str] = set()
    cycles: List[List[str]] = []

    def dfs(node: str, path: List[str]):
        if node in stack:
            # found a cycle
            idx = path.index(node) if node in path else 0
            cycles.append(path[idx:] + [node])
            return
        if node in visited:
            return

        visited.add(node)
        stack.add(node)
        for dep in graph.get(node, []):
            dfs(dep, path + [dep])
        stack.remove(node)

    for n in graph:
        if n not in visited:
            dfs(n, [n])

    return cycles


def _compute_status(nodes: Dict[str, RepoNode], cycles: List[List[str]]) -> Dict[str, Any]:
    declared_repos = set(nodes.keys())
    all_deps: Set[str] = set(
        dep for node in nodes.values() for dep in node.depends_on
    )

    missing_repos = sorted(all_deps - declared_repos)
    unused_repos = sorted(declared_repos - all_deps)

    status: Dict[str, Any] = {
        "summary": {},
        "repos": {},
        "graph": {
            "nodes": list(declared_repos),
            "edges": [
                {"from": name, "to": dep}
                for name, node in nodes.items()
                for dep in node.depends_on
            ],
        },
    }

    status["summary"]["total_repos"] = len(declared_repos)
    status["summary"]["missing_repos"] = missing_repos
    status["summary"]["unused_repos"] = unused_repos
    status["summary"]["cycles"] = cycles

    for name, node in nodes.items():
        status["repos"][name] = {
            "path": node.path,
            "depends_on": node.depends_on,
            "file_count": len(node.files),
        }

    return status


def main() -> int:
    print("===== Evaluate dependency status =====")

    repos_cfg = _load_repos_config()
    if repos_cfg is None:
        # IMPORTANT: we *do not* fail the run here. This keeps StegDB
        # full-cycle from breaking if config is temporarily missing.
        status = {
            "summary": {
                "status": "no_config",
                "message": "repos_config.json missing; dependency health not evaluated.",
            }
        }
        DEPENDENCY_STATUS_JSON.parent.mkdir(parents=True, exist_ok=True)
        with DEPENDENCY_STATUS_JSON.open("w", encoding="utf-8") as f:
            json.dump(status, f, indent=2)
        print("⚠️  Wrote minimal dependency_status.json with no_config status.")
        return 0

    aggregated = _load_aggregated_files()
    nodes = _build_repo_nodes(repos_cfg, aggregated)
    cycles = _detect_cycles(nodes)
    status = _compute_status(nodes, cycles)

    # Write graph + status
    DEPENDENCY_GRAPH_JSON.parent.mkdir(parents=True, exist_ok=True)
    with DEPENDENCY_GRAPH_JSON.open("w", encoding="utf-8") as f:
        json.dump(
            {
                "nodes": [asdict(n) for n in nodes.values()],
                "cycles": cycles,
            },
            f,
            indent=2,
        )

    DEPENDENCY_STATUS_JSON.parent.mkdir(parents=True, exist_ok=True)
    with DEPENDENCY_STATUS_JSON.open("w", encoding="utf-8") as f:
        json.dump(status, f, indent=2)

    print(f"🧠 Wrote dependency graph to {DEPENDENCY_GRAPH_JSON}")
    print(f"📊 Wrote dependency status to {DEPENDENCY_STATUS_JSON}")
    print("✅ Dependency evaluation complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
