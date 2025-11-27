#!/usr/bin/env python3
"""
Register or update a repo entry in registry/repos.json.

Usage:
  python tools/register_repo.py \
    --name CosDen \
    --path CosDen \
    --canonical canonical/cosden
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

REGISTRY = Path(__file__).resolve().parents[1] / "registry" / "repos.json"


def load_registry() -> dict:
    if REGISTRY.exists():
        return json.loads(REGISTRY.read_text(encoding="utf-8"))
    return {"repos": []}


def save_registry(data: dict) -> None:
    REGISTRY.parent.mkdir(parents=True, exist_ok=True)
    REGISTRY.write_text(json.dumps(data, indent=2), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", required=True)
    parser.add_argument("--path", required=True)
    parser.add_argument("--canonical", required=True)
    args = parser.parse_args()

    data = load_registry()

    # Remove any existing entry with same name
    data["repos"] = [r for r in data["repos"] if r.get("name") != args.name]

    entry = {
        "name": args.name,
        "path": args.path,
        "canonical_path": args.canonical,
        "prod_valid": False,
        "last_build_validation": None,
        "last_prod_validation": None,
    }
    data["repos"].append(entry)

    save_registry(data)
    print(f"✅ Registered repo {args.name} in {REGISTRY}")


if __name__ == "__main__":
    main()
