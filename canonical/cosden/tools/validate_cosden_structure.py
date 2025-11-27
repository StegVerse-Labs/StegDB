#!/usr/bin/env python3
"""
CosDenOS repo validator + metadata + validation stamp.

Modes:

  --mode=build   (default, permissive)
      - Enforces required dirs/files/import
      - Logs unexpected structure as WARNINGS (does NOT fail)
      - Writes meta/files.jsonl
      - Writes validation_stamp.json with highest_mode >= "build" for this commit

  --mode=prod    (strict, production)
      - Enforces required dirs/files/import
      - Treats unexpected structure as ERRORS
      - Writes meta/files.jsonl
      - Writes validation_stamp.json with highest_mode updated to "prod" for this commit

Hybrid root rules (for BOTH modes):
  Allowed dirs at root:
    - src, tools, .github, docs, tests, scripts
    - meta, .git, stegdb are specially handled/ignored

  Allowed files at root:
    - Dockerfile, pyproject.toml, README.md, LICENSE

Anything else at root:
  - build mode: WARNING only
  - prod mode: ERROR (blocks publish)

Highest-mode behavior:
- Stamp contains: repo, commit, highest_mode, meta_sha256, validated_at
- For a given commit:
    - If no stamp exists yet → write one with current mode
    - If stamp exists with same commit:
        - If new mode is stronger (prod > build) → upgrade highest_mode
        - If new mode is weaker (build after prod) → keep highest_mode=prod
    - If stamp for different commit → overwrite for new commit
"""

import argparse
import sys
from pathlib import Path
import json
import hashlib
from datetime import datetime, timezone
import importlib.util
import os


REPO_ROOT = Path(__file__).resolve().parents[1]

# Root-level expectations
REQUIRED_ROOT_DIRS = {
    "src",
    "tools",
    ".github",
}

# Allowed root dirs (no errors or warnings in either mode)
ALLOWED_ROOT_DIRS = REQUIRED_ROOT_DIRS.union({
    "docs",
    "tests",
    "scripts",
})

# Always-ignored root entries
IGNORED_ROOT_DIRS = {
    ".git",
    "stegdb",   # checked-out StegDB during workflows
    "meta",     # generated metadata
    "__pycache__",
}

IGNORED_ROOT_FILES = {
    ".gitignore",
}

# Allowed files at root (no warnings in either mode)
ALLOWED_ROOT_FILES = {
    "Dockerfile",
    "pyproject.toml",
    "README.md",
    "LICENSE",
}

# Required files relative to repo root
REQUIRED_FILES = [
    ".github/workflows/cosden-docker.yml",
    "src/CosDenOS/__init__.py",
    "src/CosDenOS/api.py",
    "src/CosDenOS/api_models.py",
    "src/CosDenOS/logging_utils.py",
]

META_DIR = REPO_ROOT / "meta"
META_FILE = META_DIR / "files.jsonl"
STAMP_FILE = META_DIR / "validation_stamp.json"

MODE_LEVEL = {
    "build": 1,
    "prod": 2,
}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def file_iter_for_metadata(root: Path):
    # Only hash under src/ and tools/ for now
    for base_name in ("src", "tools"):
        base = root / base_name
        if not base.exists():
            continue
        for p in base.rglob("*"):
            if p.is_file():
                yield p


def write_metadata() -> str:
    """
    Write meta/files.jsonl and return its SHA256.
    """
    META_DIR.mkdir(exist_ok=True)
    if META_FILE.exists():
        META_FILE.unlink()

    now = datetime.now(timezone.utc).isoformat()

    with META_FILE.open("w", encoding="utf-8") as out:
        for path in file_iter_for_metadata(REPO_ROOT):
            rel = path.relative_to(REPO_ROOT).as_posix()
            size = path.stat().st_size
            digest = sha256_file(path)

            rec = {
                "repo": "CosDen",
                "path": rel,
                "sha256": digest,
                "size_bytes": size,
                "timestamp": now,
                "valid_location": True,
                "issues": [],
            }
            out.write(json.dumps(rec) + "\n")

    meta_hash = sha256_file(META_FILE)
    return meta_hash


def import_check() -> bool:
    """
    Try to import CosDenOS by temporarily adding src/ to sys.path.
    """
    src_path = REPO_ROOT / "src"
    if not src_path.exists():
        print("✖ Import check: src/ missing", file=sys.stderr)
        return False

    sys.path.insert(0, str(src_path))
    try:
        spec = importlib.util.find_spec("CosDenOS")
        if spec is None:
            print("✖ Import check: CosDenOS package not found", file=sys.stderr)
            return False
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)  # type: ignore
    except Exception as exc:
        print(f"✖ Import check failed: {exc}", file=sys.stderr)
        return False
    finally:
        if sys.path and sys.path[0] == str(src_path):
            sys.path.pop(0)

    print("✓ Import check... OK")
    return True


def validate_structure(mode: str) -> tuple[int, str]:
    """
    Returns (number_of_issues, meta_hash).
    """
    errors = 0

    print("🔍 Validating CosDenOS repo structure + generating metadata...\n")

    # 1) Required directories
    print("• Required directories...")
    missing_dirs = []
    for d in REQUIRED_ROOT_DIRS:
        if not (REPO_ROOT / d).exists():
            missing_dirs.append(d)

    if missing_dirs:
        for d in missing_dirs:
            print(f"  ✖ Missing required directory at root: {d}")
        errors += len(missing_dirs)
    else:
        print("  ✓ OK")

    # 2) Required files
    print("• Required files...")
    missing_files = []
    for rel in REQUIRED_FILES:
        if not (REPO_ROOT / rel).exists():
            missing_files.append(rel)

    if missing_files:
        for rel in missing_files:
            print(f"  ✖ Missing required file: {rel}")
        errors += len(missing_files)
    else:
        print("  ✓ OK")

    # 3) Unexpected structure
    print("• Unexpected structure...")
    unexpected_items = []

    for child in REPO_ROOT.iterdir():
        name = child.name
        if child.is_dir():
            if name in ALLOWED_ROOT_DIRS:
                continue
            if name in IGNORED_ROOT_DIRS:
                continue
            unexpected_items.append(f"directory: {name}")
        else:
            if name in IGNORED_ROOT_FILES:
                continue
            if name in ALLOWED_ROOT_FILES:
                continue
            unexpected_items.append(f"file: {name}")

    if not unexpected_items:
        print("  ✓ OK")
    else:
        for item in unexpected_items:
            if mode == "build":
                print(f"  ⚠ Unexpected {item} (permissive build mode: WARNING only)")
            else:
                print(f"  ✖ Unexpected {item}")
        if mode == "prod":
            errors += len(unexpected_items)

    # 4) Import check
    print("• Import check...")
    if not import_check():
        errors += 1

    # 5) File hashing + metadata
    print("• File hashing & metadata...")
    meta_hash = write_metadata()
    print(f"  ✓ Wrote metadata to {META_FILE.relative_to(REPO_ROOT)} (sha256={meta_hash})")

    print("\n" + "-" * 64)
    if errors == 0:
        print("✓ Validation passed")
    else:
        if mode == "build":
            print("✖ Validation has issues (missing required elements).")
        else:
            print("✖ Validation failed (strict mode).")

    return errors, meta_hash


def update_validation_stamp(mode: str, meta_hash: str) -> None:
    """
    Update meta/validation_stamp.json with highest_mode for this commit.
    For the same commit:
      - never downgrade from prod to build
      - always keep the strongest mode seen.
    """
    META_DIR.mkdir(exist_ok=True)

    commit = os.environ.get("GITHUB_SHA", "").strip() or "unknown"
    now = datetime.now(timezone.utc).isoformat()

    new_level = MODE_LEVEL.get(mode, 0)

    current = None
    if STAMP_FILE.exists():
        try:
            with STAMP_FILE.open("r", encoding="utf-8") as f:
                current = json.load(f)
        except Exception:
            current = None

    if current and current.get("commit") == commit:
        old_mode = current.get("highest_mode", "build")
        old_level = MODE_LEVEL.get(old_mode, 0)
        if new_level >= old_level:
            highest_mode = mode
        else:
            highest_mode = old_mode
    else:
        highest_mode = mode

    stamp = {
        "repo": "CosDen",
        "commit": commit,
        "highest_mode": highest_mode,
        "meta_sha256": meta_hash,
        "validated_at": now,
    }

    with STAMP_FILE.open("w", encoding="utf-8") as f:
        json.dump(stamp, f, indent=2)

    print(f"✓ Wrote validation stamp to {STAMP_FILE.relative_to(REPO_ROOT)}")
    print(f"  commit={commit}, highest_mode={highest_mode}, meta_sha256={meta_hash}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate CosDenOS repo structure and generate metadata + validation stamp."
    )
    parser.add_argument(
        "--mode",
        type=str,
        choices=["build", "prod"],
        default="build",
        help="Validation mode: 'build' (permissive) or 'prod' (strict). Default: build.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    mode = args.mode

    issues, meta_hash = validate_structure(mode=mode)

    # Only write stamp if validation succeeded for this mode.
    if issues == 0:
        update_validation_stamp(mode=mode, meta_hash=meta_hash)
    else:
        print("⚠ Skipping validation stamp update because validation had issues.")

    if issues > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
