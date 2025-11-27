import json
import argparse
from pathlib import Path

REGISTRY = Path("registry/repos.json")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", required=True)
    parser.add_argument("--path", required=True)
    parser.add_argument("--canonical", required=True)
    args = parser.parse_args()

    REGISTRY.parent.mkdir(parents=True, exist_ok=True)

    if REGISTRY.exists():
        data = json.loads(REGISTRY.read_text())
    else:
        data = {"repos": []}

    # Prevent duplicates
    data["repos"] = [r for r in data["repos"] if r["name"] != args.name]

    data["repos"].append({
        "name": args.name,
        "path": args.path,
        "canonical_path": args.canonical,
        "prod_valid": False,
        "last_build_validation": None,
        "last_prod_validation": None
    })

    REGISTRY.write_text(json.dumps(data, indent=2))
    print(f"Registered repo {args.name}")

if __name__ == "__main__":
    main()
