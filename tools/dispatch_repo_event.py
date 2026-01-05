#!/usr/bin/env python3
"""
Dispatch a repository_dispatch event (default: sync-to-canonical) to many repos.

Targeting:
- Discovers repos under ORG_NAME via GitHub API (pagination supported)
- Optionally unions with repos listed in tools/repo_manifest.json (MANIFEST_PATH)
- Skips archived repos by default (unless INCLUDE_ARCHIVED=true)
- Applies safety cap MAX_REPOS (default 35; set 0 for unlimited)

Behavior:
- Sends: POST /repos/{owner}/{repo}/dispatches
  body: {"event_type": EVENT_TYPE, "client_payload": {...}}

Requires env:
  GH_TOKEN
  ORG_NAME
Optional env:
  MANIFEST_PATH
  MAX_REPOS
  INCLUDE_ARCHIVED
  DRY_RUN
  EVENT_TYPE
"""

from __future__ import annotations

import json
import os
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


API = "https://api.github.com"


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def truthy(s: str) -> bool:
    return str(s).strip().lower() in ("1", "true", "yes", "y", "on")


def gh_request(
    token: str,
    method: str,
    url: str,
    payload: Optional[dict] = None,
    accept: str = "application/vnd.github+json",
) -> Tuple[int, Any, Dict[str, str]]:
    data = None
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")

    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"token {token}")
    req.add_header("Accept", accept)
    req.add_header("X-GitHub-Api-Version", "2022-11-28")

    try:
        with urllib.request.urlopen(req) as resp:
            raw = resp.read().decode("utf-8")
            body = json.loads(raw) if raw.strip() else None
            headers = {k.lower(): v for k, v in resp.headers.items()}
            return resp.status, body, headers
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", errors="replace")
        try:
            body = json.loads(raw) if raw.strip() else {"message": str(e)}
        except Exception:
            body = {"message": raw or str(e)}
        headers = {k.lower(): v for k, v in e.headers.items()} if e.headers else {}
        return e.code, body, headers


def parse_link_next(link_header: str) -> Optional[str]:
    if not link_header:
        return None
    parts = [p.strip() for p in link_header.split(",")]
    for p in parts:
        if 'rel="next"' in p:
            start = p.find("<")
            end = p.find(">")
            if start != -1 and end != -1 and end > start:
                return p[start + 1 : end]
    return None


def load_manifest_repos(path: Path) -> List[str]:
    if not path.exists():
        return []
    try:
        man = json.loads(path.read_text(encoding="utf-8"))
        repos = man.get("repos") or []
        out = []
        for r in repos:
            name = (r.get("name") or "").strip()
            if name and "/" in name:
                out.append(name)
        return out
    except Exception:
        return []


def discover_org_repos(token: str, org: str, include_archived: bool) -> List[str]:
    url = f"{API}/orgs/{urllib.parse.quote(org)}/repos?per_page=100&type=all"
    names: List[str] = []

    while url:
        code, data, headers = gh_request(token, "GET", url)
        if code != 200 or not isinstance(data, list):
            break

        for repo in data:
            if not isinstance(repo, dict):
                continue
            if (repo.get("archived") is True) and (not include_archived):
                continue
            full = (repo.get("full_name") or "").strip()
            if full and "/" in full:
                names.append(full)

        url = parse_link_next(headers.get("link", ""))

    return names


def repo_has_actions_enabled(info: dict) -> bool:
    # Some org policies disable actions; GitHub reports via "has_actions" in some contexts,
    # but not always. We'll just attempt dispatch and report failures.
    return True


def get_repo_info(token: str, full_name: str) -> Optional[dict]:
    code, data, _ = gh_request(token, "GET", f"{API}/repos/{full_name}")
    if code == 200 and isinstance(data, dict):
        return data
    return None


def dispatch_event(token: str, full_name: str, event_type: str, payload: dict) -> Tuple[bool, str]:
    url = f"{API}/repos/{full_name}/dispatches"
    body = {"event_type": event_type, "client_payload": payload}
    code, data, _ = gh_request(token, "POST", url, payload=body)
    if code == 204:
        return True, "dispatched"
    # common failure is 404 (no perms) or 422 (validation) or 403 (forbidden)
    msg = ""
    if isinstance(data, dict):
        msg = data.get("message") or json.dumps(data)
    else:
        msg = str(data)
    return False, f"failed({code}): {msg}"


def main() -> int:
    token = os.environ.get("GH_TOKEN", "").strip()
    org = os.environ.get("ORG_NAME", "").strip()
    manifest_path = Path(os.environ.get("MANIFEST_PATH", "tools/repo_manifest.json"))
    include_archived = truthy(os.environ.get("INCLUDE_ARCHIVED", "false"))
    dry_run = truthy(os.environ.get("DRY_RUN", "false"))
    event_type = os.environ.get("EVENT_TYPE", "sync-to-canonical").strip() or "sync-to-canonical"

    max_repos_raw = os.environ.get("MAX_REPOS", "35").strip()
    try:
        max_repos = int(max_repos_raw)
    except Exception:
        max_repos = 35

    if not token:
        print("::error::GH_TOKEN is not set")
        return 2
    if not org:
        print("::error::ORG_NAME is not set")
        return 2

    org_repos = discover_org_repos(token, org, include_archived=include_archived)
    manifest_repos = load_manifest_repos(manifest_path)

    repo_set = {r.strip() for r in (org_repos + manifest_repos) if r.strip() and "/" in r}
    repos = sorted(repo_set)

    if max_repos > 0:
        repos = repos[:max_repos]

    summary: Dict[str, Any] = {
        "ran_at_utc": utc_now(),
        "org": org,
        "event_type": event_type,
        "include_archived": include_archived,
        "dry_run": dry_run,
        "max_repos": max_repos,
        "repo_count": len(repos),
        "results": [],
    }

    for full_name in repos:
        info = get_repo_info(token, full_name)
        if not info:
            summary["results"].append({"repo": full_name, "status": "error", "detail": "repo-not-accessible"})
            continue

        # Payload can include trace metadata (safe)
        payload = {
            "source": "StegDB",
            "trigger": "dispatch-sync-to-canonical",
            "requested_at_utc": utc_now(),
        }

        if dry_run:
            summary["results"].append({"repo": full_name, "status": "dry-run"})
            continue

        ok, msg = dispatch_event(token, full_name, event_type=event_type, payload=payload)
        summary["results"].append({"repo": full_name, "status": "ok" if ok else "error", "detail": msg})

        time.sleep(0.25)

    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
