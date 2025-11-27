from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import json
import requests


@dataclass
class CosDenClientConfig:
    """
    Configuration for talking to a CosDenOS API instance.
    """
    base_url: str  # e.g. "http://localhost:8000" or "https://cosden.stegverse.internal"
    timeout_seconds: float = 10.0


class CosDenHTTPError(Exception):
    """Raised when the CosDen HTTP API returns an error."""


class CosDenClient:
    """
    Simple Python client for the CosDenOS API.

    Wraps:
      - GET /health
      - POST /plan
      - POST /simulate
    """

    def __init__(self, config: CosDenClientConfig) -> None:
        self.config = config

    # ------------------------------
    # Internal helpers
    # ------------------------------

    def _url(self, path: str) -> str:
        return self.config.base_url.rstrip("/") + path

    def _handle_response(self, resp: requests.Response) -> Dict[str, Any]:
        try:
            data = resp.json()
        except json.JSONDecodeError:
            raise CosDenHTTPError(
                f"CosDen API returned non-JSON response: {resp.status_code}"
            )
        if resp.status_code >= 400:
            detail = data.get("detail", data)
            raise CosDenHTTPError(f"CosDen API error {resp.status_code}: {detail}")
        return data

    # ------------------------------
    # Health
    # ------------------------------

    def health(self) -> Dict[str, Any]:
        resp = requests.get(
            self._url("/health"),
            timeout=self.config.timeout_seconds,
        )
        return self._handle_response(resp)

    # ------------------------------
    # /plan endpoint
    # ------------------------------

    def plan(
        self,
        age_years: int,
        request_text: str,
        tone_preference: Optional[str] = None,
        sensitivity_flag: bool = False,
        event_time_hours: Optional[int] = None,
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Call POST /plan to get a cosmetic plan.

        Returns the PlanResponse JSON as a Python dict.
        """
        payload = {
            "user": {
                "age_years": age_years,
                "tone_preference": tone_preference,
                "sensitivity_flag": sensitivity_flag,
                "event_time_hours": event_time_hours,
                "notes": notes,
            },
            "request_text": request_text,
        }
        resp = requests.post(
            self._url("/plan"),
            json=payload,
            timeout=self.config.timeout_seconds,
        )
        return self._handle_response(resp)

    # ------------------------------
    # /simulate endpoint
    # ------------------------------

    def simulate(
        self,
        age_years: int,
        codes: List[str],
        tone_preference: Optional[str] = None,
        sensitivity_flag: bool = False,
        event_time_hours: Optional[int] = None,
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Call POST /simulate to compute cosmetic effect for given product codes.

        Returns the SimulateResponse JSON as a Python dict.
        """
        payload = {
            "user": {
                "age_years": age_years,
                "tone_preference": tone_preference,
                "sensitivity_flag": sensitivity_flag,
                "event_time_hours": event_time_hours,
                "notes": notes,
            },
            "codes": codes,
        }
        resp = requests.post(
            self._url("/simulate"),
            json=payload,
            timeout=self.config.timeout_seconds,
        )
        return self._handle_response(resp)
