#!/usr/bin/env python3
import argparse
import json
import os
from datetime import datetime, timezone

def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def main() -> int:
    p = argparse.ArgumentParser(description="Write StegDB meta/dependency_status.json")
    p.add_argument("--state", choices=["ok", "degraded", "broken"], required=True)
    p.add_argument("--reason", required=True)
    p.add_argument("--details", default="{}", help="JSON object string")
    p.add_argument("--canonical-sha", default="", help="Optional sha256 for canonical bundle")
    p.add_argument("--has-aggregated-files", action="store_true")
    p.add_argument("--out", default="meta/dependency_status.json")
    args = p.parse_args()

    try:
        details_obj = json.loads(args.details)
        if not isinstance(details_obj, dict):
            raise ValueError("details must be a JSON object")
    except Exception as e:
        details_obj = {"_details_parse_error": str(e), "_raw": args.details}

    out_path = args.out
    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    payload = {
        "provider": "StegDB",
        "state": args.state,
        "reason": args.reason,
        "generated_at_utc": utc_now(),
        "artifacts": {
            "aggregated_files_jsonl": bool(args.has_aggregated_files),
        },
        "details": details_obj,
    }

    if args.canonical_sha:
        payload["artifacts"]["canonical_bundle_sha256"] = args.canonical_sha

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, sort_keys=True)
        f.write("\n")

    print(json.dumps(payload))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
