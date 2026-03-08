#!/usr/bin/env python3
"""
Ingest StegTV execution events into StegDB canonical storage.

Input:
- JSONL file of StegTV events
  OR
- JSON file containing a list of events

Output:
- canon/stegtv/execution_events.jsonl
- meta/stegtv/latest_ingest_summary.json

The tool validates a minimal canonical shape and appends only valid events.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List

STEGBDB_ROOT = Path(__file__).resolve().parents[1]

CANON_DIR = STEGBDB_ROOT / "canon" / "stegtv"
META_DIR = STEGBDB_ROOT / "meta" / "stegtv"

CANON_FILE = CANON_DIR / "execution_events.jsonl"
SUMMARY_FILE = META_DIR / "latest_ingest_summary.json"


REQUIRED_FIELDS = [
    "schema_name",
    "schema_version",
    "event_id",
    "time",
    "event_type",
    "decision",
    "issuer",
    "repo",
    "ref",
    "sha",
    "scope",
    "environment",
    "request_id",
]


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_events(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"Input not found: {path}")

    if path.suffix.lower() == ".jsonl":
        records: List[Dict[str, Any]] = []
        with path.open("r", encoding="utf-8") as f:
            for i, line in enumerate(f, start=1):
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise ValueError(f"Invalid JSONL at line {i}: {exc}") from exc
                if not isinstance(obj, dict):
                    raise ValueError(f"Line {i} is not a JSON object.")
                records.append(obj)
        return records

    if path.suffix.lower() == ".json":
        with path.open("r", encoding="utf-8") as f:
            obj = json.load(f)
        if not isinstance(obj, list):
            raise ValueError("JSON input must be a list of event objects.")
        for idx, item in enumerate(obj):
            if not isinstance(item, dict):
                raise ValueError(f"JSON item #{idx} is not an object.")
        return obj

    raise ValueError("Unsupported input format. Use .jsonl or .json")


def _normalize_event(ev: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(ev)

    out["schema_name"] = "stegtv_execution_event"
    out["schema_version"] = "1.0.0"

    out.setdefault("reason", None)
    out.setdefault("token_jti", None)
    out.setdefault("rev_epoch", None)
    out.setdefault("policy", None)
    out.setdefault("identity", None)
    out.setdefault("meta", {})

    return out


def _validate_event(ev: Dict[str, Any]) -> List[str]:
    errors: List[str] = []

    for field in REQUIRED_FIELDS:
        if field not in ev:
            errors.append(f"Missing required field: {field}")

    if ev.get("schema_name") != "stegtv_execution_event":
        errors.append("schema_name must be stegtv_execution_event")

    if ev.get("schema_version") != "1.0.0":
        errors.append("schema_version must be 1.0.0")

    allowed_types = {
        "oidc_exchange",
        "token_issued",
        "token_verified",
        "action_attempted",
        "action_succeeded",
        "action_denied",
    }
    if ev.get("event_type") not in allowed_types:
        errors.append(f"Invalid event_type: {ev.get('event_type')}")

    allowed_decisions = {"allow", "deny", "defer", "ok", "fail"}
    if ev.get("decision") not in allowed_decisions:
        errors.append(f"Invalid decision: {ev.get('decision')}")

    sha = str(ev.get("sha", ""))
    if len(sha) < 7:
        errors.append("sha must be at least 7 characters")

    meta = ev.get("meta", {})
    if meta is None:
        pass
    elif not isinstance(meta, dict):
        errors.append("meta must be an object if present")

    return errors


def _append_events(events: Iterable[Dict[str, Any]]) -> int:
    CANON_DIR.mkdir(parents=True, exist_ok=True)
    count = 0
    with CANON_FILE.open("a", encoding="utf-8") as out:
        for ev in events:
            out.write(json.dumps(ev, ensure_ascii=False) + "\n")
            count += 1
    return count


def _write_summary(
    *,
    source: str,
    total_in: int,
    written: int,
    failed: int,
    errors: List[str],
) -> None:
    META_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "provider": "StegDB",
        "schema_name": "stegtv_execution_event",
        "schema_version": "1.0.0",
        "source": source,
        "generated_at_utc": _utc_now(),
        "total_in": total_in,
        "written": written,
        "failed": failed,
        "canon_file": str(CANON_FILE.relative_to(STEGBDB_ROOT)),
        "errors": errors,
    }
    SUMMARY_FILE.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Ingest StegTV execution events into StegDB.")
    p.add_argument(
        "--input",
        required=True,
        help="Path to input .jsonl or .json file containing StegTV events.",
    )
    return p.parse_args()


def main() -> None:
    args = parse_args()
    input_path = Path(args.input).resolve()

    try:
        raw_events = _load_events(input_path)
    except Exception as exc:
        print(f"❌ Failed to load input: {exc}", file=sys.stderr)
        sys.exit(2)

    normalized: List[Dict[str, Any]] = []
    errors: List[str] = []

    for idx, raw in enumerate(raw_events, start=1):
        ev = _normalize_event(raw)
        ev_errors = _validate_event(ev)
        if ev_errors:
            for err in ev_errors:
                errors.append(f"record #{idx}: {err}")
            continue
        normalized.append(ev)

    written = _append_events(normalized) if normalized else 0
    failed = len(raw_events) - written

    _write_summary(
        source=str(input_path),
        total_in=len(raw_events),
        written=written,
        failed=failed,
        errors=errors,
    )

    if errors:
        print("❌ Validation failed for one or more records:", file=sys.stderr)
        for err in errors:
            print(f" - {err}", file=sys.stderr)
        print(f"Summary written to {SUMMARY_FILE.relative_to(STEGBDB_ROOT)}", file=sys.stderr)
        sys.exit(1)

    print(f"✅ Ingested {written} StegTV event(s) into {CANON_FILE.relative_to(STEGBDB_ROOT)}")
    print(f"✅ Summary written to {SUMMARY_FILE.relative_to(STEGBDB_ROOT)}")


if __name__ == "__main__":
    main()
