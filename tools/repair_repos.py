#!/usr/bin/env python3
"""
StegDB Repair Engine (Phase 1: CosDen root cleanup)

Generates repair plans under:

    repairs/<RepoName>/repair_plan.json

For now this is focused on CosDen, and produces a plan that
moves certain root-level files into their canonical locations
(scripts/ and docs/), so that CosDen passes strict PROD validation.

Schema (v1):

{
  "repo": "CosDen",
  "version": 1,
  "generated_at": "...",
  "actions": [
    {
      "type": "move_file",
      "from": "cosden_init_full.sh",
      "to": "scripts/cosden_init_full.sh"
    },
    ...
  ]
}

CosDen's "Apply Repair Plan From StegDB" workflow will read this file
and apply the moves.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import List


STEGBDB_ROOT = Path(__file__).resolve().parents[1]
REPAIRS_ROOT = STEGBDB_ROOT / "repairs"

COSDEN_ROOT = STEGBDB_ROOT.parent / "CosDen"
COSDEN_REPAIRS = REPAIRS_ROOT / "CosDen"


@dataclass
class RepairAction:
    type: str
    src: str
    dst: str

    def to_dict(self) -> dict:
        return {
            "type": self.type,
            "from": self.src,
            "to": self.dst,
        }


def plan_cosden_root_cleanup() -> List[RepairAction]:
    """
    Create move_file actions for known root files if they exist.
    """
    actions: List[RepairAction] = []

    mapping = {
        "cosden_init_full.sh": "scripts/cosden_init_full.sh",
        "setup_cosden_structure.sh": "scripts/setup_cosden_structure.sh",
        "COSDEN_MASTER_SPEC.md": "docs/COSDEN_MASTER_SPEC.md",
        "Architecture.txt": "docs/Architecture.txt",
    }

    if not COSDEN_ROOT.exists():
        print(f"⚠ CosDen root not found at {COSDEN_ROOT} — skipping.")
        return actions

    for src_name, dst_rel in mapping.items():
        src_path = COSDEN_ROOT / src_name
        if not src_path.exists():
            continue
        actions.append(
            RepairAction(
                type="move_file",
                src=src_name,
                dst=dst_rel,
            )
        )

    return actions


def write_cosden_plan(actions: List[RepairAction]) -> None:
    COSDEN_REPAIRS.mkdir(parents=True, exist_ok=True)
    plan_path = COSDEN_REPAIRS / "repair_plan.json"

    if not actions:
        # If there are no actions, we can either delete existing plan
        # or write an empty one. We'll write an empty plan to be explicit.
        plan = {
            "repo": "CosDen",
            "version": 1,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "actions": [],
        }
    else:
        plan = {
            "repo": "CosDen",
            "version": 1,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "actions": [a.to_dict() for a in actions],
        }

    with plan_path.open("w", encoding="utf-8") as f:
        json.dump(plan, f, indent=2)

    print(f"✅ Wrote CosDen repair plan to {plan_path}")


def main() -> None:
    print("🛠 StegDB Repair Engine (Phase 1: CosDen root cleanup)\n")

    actions = plan_cosden_root_cleanup()
    if not actions:
        print("No CosDen root cleanup actions required.")
    else:
        print("Planned CosDen actions:")
        for a in actions:
            print(f"  - {a.type}: {a.src} -> {a.dst}")

    write_cosden_plan(actions)
    print("\nDone.")


if __name__ == "__main__":
    main()
