from __future__ import annotations

import json
import sys
from datetime import datetime
from typing import Any, Dict, Optional


def log_event(
    event: str,
    level: str = "INFO",
    extra: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Minimal structured logger for CosDenOS.

    Writes a single JSON line to stdout so that containers / gateways / log
    collectors can parse events consistently.

    Example output:
    {
      "ts": "2025-11-25T12:34:56.789012Z",
      "level": "INFO",
      "event": "plan_request",
      "endpoint": "/plan",
      "age_years": 35
    }
    """
    record: Dict[str, Any] = {
        "ts": datetime.utcnow().isoformat() + "Z",
        "level": level.upper(),
        "event": event,
    }
    if extra:
        record.update(extra)

    sys.stdout.write(json.dumps(record) + "\n")
    sys.stdout.flush()
