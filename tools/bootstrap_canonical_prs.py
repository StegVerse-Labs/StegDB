#!/usr/bin/env python3
"""
Bootstrap the canonical sync workflow into many repos by opening PRs that add:

  .github/workflows/sync-to-canonical.yml

Repo targeting:
- Auto-discovers repos in ORG_NAME via GitHub API (pagination supported)
- Optionally unions with tools/repo_manifest.json (MANIFEST_PATH) if present
- Skips archived repos by default (unless INCLUDE_ARCHIVED=true)
- Safety cap MAX_REPOS (default 35; set 0 for unlimited)

Requires env:
  GH_TOKEN         PAT with repo write + PR permissions for the org(s)
  ORG_NAME         e.g. "StegVerse-Labs"
  BOOTSTRAP_SOURCE path in StegDB repo, e.g. canonical/profiles/base/.github/workflows/sync-to-canonical.yml
  TARGET_PATH      e.g. .github/workflows/sync-to-canonical.yml
Optional env:
  MANIFEST_PATH    tools/repo_manifest.json (union list)
  MAX_REPOS        integer string; default "35"
  INCLUDE_ARCHIVED "true"/"false" (default false)
"""

from __future__ import annotations

import base64
import json
import os
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


API = "https://api.github.com"


def utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")


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
    # GitHub pagination: Link: <url>; rel="next", <url>; rel="last"
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
    # Use /orgs/{org}/repos?per_page=100&type=all
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


def read_source_file(path: Path) -> str:
    txt = path.read_text(encoding="utf-8")
    if not txt.strip():
        raise SystemExit(f"Bootstrap source file is empty: {path}")
    return txt


def get_repo_info(token: str, full_name: str) -> Optional[dict]:
    code, data, _ = gh_request(token, "GET", f"{API}/repos/{full_name}")
    if code == 200 and isinstance(data, dict):
        return data
    return None


def get_file_sha_if_exists(token: str, full_name: str, path: str, ref: str) -> Optional[str]:
    code, data, _ = gh_request(token, "GET", f"{API}/repos/{full_name}/contents/{path}?ref={ref}")
    if code == 200 and isinstance(data, dict):
        return data.get("sha")
    return None


def create_branch(token: str, full_name: str, base_branch: str, new_branch: str) -> bool:
    code, data, _ = gh_request(token, "GET", f"{API}/repos/{full_name}/git/ref/heads/{base_branch}")
    if code != 200 or not isinstance(data, dict):
        return False
    base_sha = data.get("object", {}).get("sha")
    if not base_sha:
        return False

    payload = {"ref": f"refs/heads/{new_branch}", "sha": base_sha}
    code2, _, _ = gh_request(token, "POST", f"{API}/repos/{full_name}/git/refs", payload=payload)

    # 201 created, 422 already exists
    return code2 in (201, 422)


def put_file(token: str, full_name: str, path: str, content_text: str, branch: str, message: str) -> bool:
    b64 = base64.b64encode(content_text.encode("utf-8")).decode("ascii")
    payload = {"message": message, "content": b64, "branch": branch}
    code, _, _ = gh_request(token, "PUT", f"{API}/repos/{full_name}/contents/{path}", payload=payload)
    return code in (201, 200)


def open_pr(token: str, full_name: str, head: str, base: str, title: str, body: str) -> Optional[str]:
    payload = {"title": title, "head": head, "base": base, "body": body}
    code, data, _ = gh_request(token, "POST", f"{API}/repos/{full_name}/pulls", payload=payload)
    if code == 201 and isinstance(data, dict):
        return data.get("html_url")
    return None


def main() -> int:
    token = os.environ.get("GH_TOKEN", "").strip()
    org = os.environ.get("ORG_NAME", "").strip()
    source_path = Path(os.environ.get("BOOTSTRAP_SOURCE", "canonical/profiles/base/.github/workflows/sync-to-canonical.yml"))
    target_path = os.environ.get("TARGET_PATH", ".github/workflows/sync-to-canonical.yml").strip()
    manifest_path = Path(os.environ.get("MANIFEST_PATH", "tools/repo_manifest.json"))
    include_archived = truthy(os.environ.get("INCLUDE_ARCHIVED", "false"))
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
    if not source_path.exists():
        print(f"::error::Missing bootstrap source: {source_path}")
        return 2

    src_text = read_source_file(source_path)

    # Discover repos from org
    org_repos = discover_org_repos(token, org, include_archived=include_archived)

    # Union with manifest repos (optional)
    manifest_repos = load_manifest_repos(manifest_path)
    repo_set = {r.strip() for r in (org_repos + manifest_repos) if r.strip() and "/" in r}
    repos = sorted(repo_set)

    if max_repos > 0:
        repos = repos[:max_repos]

    stamp = utc_stamp()
    summary: Dict[str, Any] = {
        "ran_at_utc": utc_now(),
        "org": org,
        "include_archived": include_archived,
        "max_repos": max_repos,
        "source": str(source_path),
        "target_path": target_path,
        "repo_count": len(repos),
        "results": [],
    }

    for full_name in repos:
        info = get_repo_info(token, full_name)
        if not info:
            summary["results"].append({"repo": full_name, "status": "error", "reason": "repo-not-accessible"})
            continue

        default_branch = info.get("default_branch") or "main"

        # If file already exists, skip
        existing_sha = get_file_sha_if_exists(token, full_name, target_path, default_branch)
        if existing_sha:
            summary["results"].append(
                {"repo": full_name, "status": "skip", "reason": "already-present", "branch": default_branch}
            )
            continue

        branch = f"bootstrap-canonical-{stamp}"
        if not create_branch(token, full_name, default_branch, branch):
            summary["results"].append({"repo": full_name, "status": "error", "reason": "branch-create-failed"})
            continue

        msg = "chore: add canonical bootstrap sync workflow"
        if not put_file(token, full_name, target_path, src_text, branch, msg):
            summary["results"].append({"repo": full_name, "status": "error", "reason": "put-file-failed", "branch": branch})
            continue

        pr_title = "chore: bootstrap canonical sync (StegDB)"
        pr_body = (
            "This PR was generated by StegDB bootstrap automation.\n\n"
            "It adds the canonical `sync-to-canonical` workflow so this repo can self-update from StegDB profiles.\n\n"
            f"- Source: `{source_path}`\n"
            f"- Target: `{target_path}`\n"
            f"- Generated: {utc_now()}\n"
        )
        pr_url = open_pr(token, full_name, head=branch, base=default_branch, title=pr_title, body=pr_body)

        summary["results"].append(
            {
                "repo": full_name,
                "status": "pr-opened" if pr_url else "pushed-branch",
                "branch": branch,
                "base": default_branch,
                "pr": pr_url,
            }
        )

        # light throttle to avoid API bursts
        time.sleep(0.35)

    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
