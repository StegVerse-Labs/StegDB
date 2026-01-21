#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Dict, Any, List, Tuple

def read_text(p: Path) -> str:
    return p.read_text(encoding="utf-8")

def write_text(p: Path, s: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(s, encoding="utf-8")

def normalize(s: str) -> str:
    # normalize line endings + trailing whitespace
    s = s.replace("\r\n", "\n").replace("\r", "\n")
    lines = [ln.rstrip() for ln in s.split("\n")]
    # keep one trailing newline
    return "\n".join(lines).rstrip() + "\n"

def render_template(tmpl: str, subs: Dict[str, str]) -> str:
    out = tmpl
    for k, v in subs.items():
        out = out.replace("{" + k + "}", v)
    return out

def canonical_source_url(source_repo: str, source_ref: str, canonical_path: str) -> str:
    # human-viewable URL (fine for docs)
    return f"https://github.com/{source_repo}/blob/{source_ref}/{canonical_path}"

def load_manifest(p: Path) -> Dict[str, Any]:
    return json.loads(read_text(p))

def sync_docs(
    manifest: Dict[str, Any],
    diamondops_root: Path,
    repo_root: Path,
    repo_name: str,
    dry_run: bool = False,
) -> List[Tuple[str, str]]:
    """
    Returns list of (target_path, status) where status in {"unchanged","updated","missing_template","missing_canonical"}.
    """
    source_repo = manifest["source_repo"]
    source_ref = manifest.get("source_ref", "main")
    results: List[Tuple[str, str]] = []

    for item in manifest["items"]:
        canonical_path = item["canonical_path"]
        target_path = item["target_path"]
        template_path = item["template"]

        can_file = diamondops_root / canonical_path
        if not can_file.exists():
            results.append((target_path, "missing_canonical"))
            continue

        tmpl_file = repo_root / template_path
        if not tmpl_file.exists():
            results.append((target_path, "missing_template"))
            continue

        can_content = normalize(read_text(can_file))
        tmpl = read_text(tmpl_file)

        subs = {
            "REPO_NAME": repo_name,
            "CANONICAL_CONTENT": can_content.rstrip() + "\n",
            "CANONICAL_SOURCE_URL": canonical_source_url(source_repo, source_ref, canonical_path),
        }
        rendered = normalize(render_template(tmpl, subs))

        tgt_file = repo_root / target_path
        current = normalize(read_text(tgt_file)) if tgt_file.exists() else ""

        if current == rendered:
            results.append((target_path, "unchanged"))
            continue

        if not dry_run:
            write_text(tgt_file, rendered)

        results.append((target_path, "updated"))

    return results

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True, help="Path to tools/canonical_docs_manifest.json")
    ap.add_argument("--diamondops-root", required=True, help="Path where DiamondOps repo is checked out")
    ap.add_argument("--repo-root", required=True, help="Path to the target repo working directory")
    ap.add_argument("--repo-name", required=True, help="Repo name, e.g. HydraSafe")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    manifest = load_manifest(Path(args.manifest))
    results = sync_docs(
        manifest=manifest,
        diamondops_root=Path(args.diamondops_root),
        repo_root=Path(args.repo_root),
        repo_name=args.repo_name,
        dry_run=args.dry_run,
    )

    # Print a compact summary for CI logs
    for path, status in results:
        print(f"{status}: {path}")

    # non-zero exit if missing canonical/template (so we notice)
    bad = [r for r in results if r[1] in ("missing_canonical", "missing_template")]
    return 2 if bad else 0

if __name__ == "__main__":
    raise SystemExit(main())
