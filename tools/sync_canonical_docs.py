#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, Any, List, Tuple


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


def canonical_source_url(source_repo: str, source_ref: str, canonical_path: str) -> str:
    return f"https://github.com/{source_repo}/blob/{source_ref}/{canonical_path}"


def load_json(p: Path) -> Dict[str, Any]:
    return json.loads(read_text(p))


def _safe_mode(item: Dict[str, Any]) -> str:
    m = (item.get("mode") or "excerpt").strip().lower()
    if m not in ("excerpt", "link-only"):
        raise ValueError(f"Unsupported mode: {m}")
    return m


def sync_docs(
    registry: Dict[str, Any],
    source_root: Path,
    repo_root: Path,
    repo_name: str,
    dry_run: bool = False,
) -> List[Tuple[str, str]]:
    source_repo = registry["source_repo"]
    source_ref = registry.get("source_ref", "main")
    results: List[Tuple[str, str]] = []

    for item in registry.get("items", []):
        canonical_path = item["canonical_path"]
        target_path = item["target_path"]
        template_path = item["template"]
        required_reference = bool(item.get("required_reference", False))
        mode = _safe_mode(item)

        can_file = source_root / canonical_path
        if not can_file.exists():
            results.append((target_path, "missing_canonical"))
            continue

        tmpl_file = repo_root / template_path
        if not tmpl_file.exists():
            results.append((target_path, "missing_template"))
            continue

        can_content = normalize(read_text(can_file))
        tmpl = read_text(tmpl_file)

        src_url = canonical_source_url(source_repo, source_ref, canonical_path)

        if required_reference and "{CANONICAL_SOURCE_URL}" not in tmpl:
            results.append((target_path, "invalid"))
            continue

        canonical_payload = "" if mode == "link-only" else (can_content.rstrip() + "\n")

        subs = {
            "REPO_NAME": repo_name,
            "CANONICAL_CONTENT": canonical_payload,
            "CANONICAL_SOURCE_URL": src_url,
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
    ap.add_argument("--registry", required=True, help="Path to registry/*.json")
    ap.add_argument("--source-root", required=True, help="Path where DiamondOps-Core is checked out")
    ap.add_argument("--repo-root", required=True, help="Path to target repo working directory")
    ap.add_argument("--repo-name", required=True, help="Repo name, e.g. HydraSafe")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    registry = load_json(Path(args.registry))
    results = sync_docs(
        registry=registry,
        source_root=Path(args.source_root),
        repo_root=Path(args.repo_root),
        repo_name=args.repo_name,
        dry_run=args.dry_run,
    )

    for path, status in results:
        print(f"{status}: {path}")

    bad = [r for r in results if r[1] in ("missing_canonical", "missing_template", "invalid")]
    return 2 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
