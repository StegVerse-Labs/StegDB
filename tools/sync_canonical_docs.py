#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

def read_text(p: Path) -> str:
    return p.read_text(encoding="utf-8")

def write_text(p: Path, s: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(s, encoding="utf-8")

def normalize(s: str) -> str:
    s = s.replace("\r\n", "\n").replace("\r", "\n")
    lines = [ln.rstrip() for ln in s.split("\n")]
    return "\n".join(lines).rstrip() + "\n"

def render_template(tmpl: str, subs: Dict[str, str]) -> str:
    out = tmpl
    for k, v in subs.items():
        out = out.replace("{" + k + "}", v)
    return out

def source_url(repo: str, ref: str, path: str) -> str:
    return f"https://github.com/{repo}/blob/{ref}/{path}"

def load_json(p: Path) -> Dict[str, Any]:
    return json.loads(read_text(p))

def sync_docs(
    manifest: Dict[str, Any],
    sources: Dict[str, Path],
    repo_root: Path,
    repo_name: str,
    dry_run: bool = False,
) -> List[Tuple[str, str]]:
    """
    manifest:
      - default_source_repo, default_source_ref, default_source_key
      - items[]: canonical_path, target_path, template, optional source_key/source_repo/source_ref
    sources: map source_key -> checkout path on disk
    """
    default_source_key = manifest.get("default_source_key", "diamondops")
    default_source_repo = manifest.get("default_source_repo", "")
    default_source_ref = manifest.get("default_source_ref", "main")

    results: List[Tuple[str, str]] = []

    for item in manifest["items"]:
        canonical_path = item["canonical_path"]
        target_path = item["target_path"]
        template_path = item["template"]

        source_key = item.get("source_key", default_source_key)
        src_repo = item.get("source_repo", default_source_repo)
        src_ref = item.get("source_ref", default_source_ref)

        if source_key not in sources:
            results.append((target_path, "missing_source_checkout"))
            continue

        src_root = sources[source_key]
        can_file = src_root / canonical_path
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
            "CANONICAL_SOURCE_URL": source_url(src_repo, src_ref, canonical_path) if src_repo else "",
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
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--repo-name", required=True)
    ap.add_argument("--source", action="append", required=True,
                    help="source_key=PATH (repeatable), e.g. core=_diamondops_core")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    manifest = load_json(Path(args.manifest))

    sources: Dict[str, Path] = {}
    for s in args.source:
        key, path = s.split("=", 1)
        sources[key.strip()] = Path(path.strip())

    results = sync_docs(
        manifest=manifest,
        sources=sources,
        repo_root=Path(args.repo_root),
        repo_name=args.repo_name,
        dry_run=args.dry_run,
    )

    for path, status in results:
        print(f"{status}: {path}")

    bad = [r for r in results if r[1] in ("missing_canonical", "missing_template", "missing_source_checkout")]
    return 2 if bad else 0

if __name__ == "__main__":
    raise SystemExit(main())
