#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="meta", help="Root folder to manifest (default: meta)")
    ap.add_argument("--out", default="meta/attest/manifest.json")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    out = Path(args.out).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)

    files: List[Path] = []
    if root.exists():
        for p in root.rglob("*"):
            if p.is_file():
                files.append(p)

    entries: Dict[str, Dict[str, object]] = {}
    for p in sorted(files):
        rel = p.relative_to(root.parent).as_posix()  # relative to repo root
        try:
            entries[rel] = {"sha256": sha256_file(p), "size": p.stat().st_size}
        except Exception as e:
            entries[rel] = {"sha256": None, "size": None, "error": str(e)}

    payload = {
        "generated_at_utc": now_utc(),
        "root": str(root.relative_to(root.parent)),
        "file_count": len(files),
        "entries": entries,
    }

    out.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
