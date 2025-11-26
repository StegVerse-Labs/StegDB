#!/usr/bin/env python3
"""
Export canonical CosDen files into StegDB.

This script copies selected files from the CosDen repo into:

    canonical/cosden/...

so that StegDB can act as the canonical source of truth for those files.

Usage (from StegDB root):

    python tools/export_cosden_canonical.py

Or specify a custom CosDen location:

    python tools/export_cosden_canonical.py --cosden-root ../CosDen
"""

import argparse
import shutil
from pathlib import Path
from typing import List

STEGBDB_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_COSDEN_ROOT = STEGBDB_ROOT.parent / "CosDen"

CANONICAL_ROOT = STEGBDB_ROOT / "canonical" / "cosden"


# List of relative paths in CosDen that we treat as canonical surfaces
CANONICAL_FILES: List[str] = [
    "src/CosDenOS/api.py",
    "src/CosDenOS/api_models.py",
    "src/CosDenOS/logging_utils.py",
    "src/CosDenOS/stegcore_integration.py",
    "src/CosDenOS/clients/python_client.py",
    "src/CosDenOS/clients/__init__.py",
    "tools/validate_cosden_structure.py",
    "Dockerfile",
    ".github/workflows/cosden-docker.yml",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export canonical CosDen files into StegDB."
    )
    parser.add_argument(
        "--cosden-root",
        type=str,
        default=str(DEFAULT_COSDEN_ROOT),
        help="Path to the CosDen repo (default: ../CosDen)",
    )
    return parser.parse_args()


def export_cosden(cosden_root: Path) -> None:
    cosden_root = cosden_root.resolve()
    if not cosden_root.exists():
        raise SystemExit(f"CosDen root does not exist: {cosden_root}")

    print(f"📦 Exporting canonical files from CosDen at: {cosden_root}")
    CANONICAL_ROOT.mkdir(parents=True, exist_ok=True)

    for rel in CANONICAL_FILES:
        src = cosden_root / rel
        dst = CANONICAL_ROOT / rel

        if not src.exists():
            print(f"⚠️ Skipping missing source file: {src}")
            continue

        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        print(f"   ✓ {rel}  ->  canonical/cosden/{rel}")


def main() -> None:
    args = parse_args()
    cosden_root = Path(args.cosden_root)

    print("\n🛠  StegDB Canonical Export: CosDen\n")
    export_cosden(cosden_root)
    print("\n✅ Export complete.\n")


if __name__ == "__main__":
    main()
