import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
META_DIR = ROOT / "meta"
TOOLS_DIR = ROOT / "tools"

AGGREGATED = META_DIR / "aggregated_files.jsonl"
GRAPH_OUT = TOOLS_DIR / "dependency_graph.json"
STATUS_OUT = META_DIR / "dependency_status.json"


def load_aggregated():
    if not AGGREGATED.exists():
        return []

    records = []
    with open(AGGREGATED, "r") as f:
        for line in f:
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return records


def build_dependency_graph(records):
    graph = {}
    for r in records:
        repo = r.get("repo", "UNKNOWN")
        graph.setdefault(repo, {"files": []})
        graph[repo]["files"].append(r.get("path", ""))
    return graph


def evaluate_health(graph):
    status = {"overall_status": "ok", "repos": {}}

    for repo, data in graph.items():
        file_count = len(data.get("files", []))

        if file_count == 0:
            status["repos"][repo] = {
                "status": "no_metadata",
                "files_indexed": 0,
                "reason": "Repository has no metadata entries."
            }
            status["overall_status"] = "warning"
        else:
            status["repos"][repo] = {
                "status": "ok",
                "files_indexed": file_count
            }

    return status


def main():
    META_DIR.mkdir(parents=True, exist_ok=True)

    records = load_aggregated()
    graph = build_dependency_graph(records)
    status = evaluate_health(graph)

    with open(GRAPH_OUT, "w") as f:
        json.dump(graph, f, indent=2)

    with open(STATUS_OUT, "w") as f:
        json.dump(status, f, indent=2)

    print("Dependency evaluation complete.")
    print(f"Wrote graph → {GRAPH_OUT}")
    print(f"Wrote status → {STATUS_OUT}")


if __name__ == "__main__":
    main()
