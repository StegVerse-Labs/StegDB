#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, help="Path to SCW workflow_runnability_latest.json")
    ap.add_argument("--out-dir", default="meta/guardian/per_repo/StegVerse-SCW")
    args = ap.parse_args()

    src = Path(args.input).resolve()
    out_dir = Path(args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    if not src.exists():
        raise SystemExit(f"Input not found: {src}")

    data = json.loads(src.read_text(encoding="utf-8"))
    data["canonized_at_utc"] = now_utc()

    (out_dir / "workflow_runnability_latest.json").write_text(
        json.dumps(data, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    # optional small pointer file
    (out_dir / "LATEST.md").write_text(
        "# StegVerse-SCW Workflow Runnability (Latest)\n\n"
        "This is a canonized copy of SCW's API-aware workflow runnability report.\n",
        encoding="utf-8",
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
