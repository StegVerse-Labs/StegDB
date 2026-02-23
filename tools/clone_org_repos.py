#!/usr/bin/env python3
"""
Clone all repos from a GitHub org into a workspace folder.

Default behavior:
- clones public repos
- skips private repos (since StegOps-Deliverables is private and you said it's the only one)

Usage:
  python tools/clone_org_repos.py --org stegverse-labs --out _workspace --skip-private

Auth:
- For public repos, cloning works without any token.
- For better API rate limits (and private repos if you ever allow), set:
    STEGVERSE_AUDIT_TOKEN  (recommended)
  or rely on Actions' GITHUB_TOKEN for API calls.

This script does NOT print tokens and does not store them on disk.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional


def gh_api(url: str, token: Optional[str]) -> Any:
    req = urllib.request.Request(url)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", "stegdb-clone-org-repos")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read().decode("utf-8"))


def list_org_repos(org: str, token: Optional[str]) -> List[Dict[str, Any]]:
    repos: List[Dict[str, Any]] = []
    page = 1
    while True:
        url = f"https://api.github.com/orgs/{org}/repos?per_page=100&page={page}&type=all"
        data = gh_api(url, token)
        if not data:
            break
        for r in data:
            repos.append(
                {
                    "name": r["name"],
                    "full_name": r["full_name"],
                    "clone_url": r["clone_url"],
                    "ssh_url": r.get("ssh_url"),
                    "private": bool(r.get("private", False)),
                    "archived": bool(r.get("archived", False)),
                    "disabled": bool(r.get("disabled", False)),
                    "default_branch": r.get("default_branch"),
                }
            )
        page += 1
    return repos


def run(cmd: List[str], cwd: Optional[Path] = None) -> None:
    p = subprocess.run(cmd, cwd=str(cwd) if cwd else None, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    if p.returncode != 0:
        print(p.stdout)
        raise RuntimeError(f"Command failed ({p.returncode}): {' '.join(cmd)}")
    # Keep output concise
    if p.stdout.strip():
        print(p.stdout.strip())


def git_clone(repo: Dict[str, Any], out_dir: Path, token: Optional[str]) -> None:
    name = repo["name"]
    target = out_dir / name

    if target.exists():
        # Fast update (best effort)
        try:
            print(f"↻ Updating {name}")
            run(["git", "fetch", "--all", "--prune"], cwd=target)
            # checkout default branch if possible
            if repo.get("default_branch"):
                run(["git", "checkout", repo["default_branch"]], cwd=target)
                run(["git", "pull", "--ff-only"], cwd=target)
        except Exception as e:
            print(f"⚠ Update failed for {name}: {e}")
        return

    clone_url = repo["clone_url"]

    # For private repos, token may be required. For public repos, plain clone_url works.
    # If token is present, we can use it in the URL without printing it.
    if token and repo["private"]:
        # x-access-token format for GitHub HTTPS
        clone_url = clone_url.replace("https://", f"https://x-access-token:{token}@")

    print(f"⬇ Cloning {repo['full_name']}")
    run(["git", "clone", "--depth", "1", clone_url, str(target)])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--org", required=True, help="GitHub org, e.g. stegverse-labs")
    ap.add_argument("--out", required=True, help="Output folder, e.g. _workspace")
    ap.add_argument("--skip-private", action="store_true", help="Skip private repos (default recommended)")
    ap.add_argument("--skip-archived", action="store_true", help="Skip archived repos")
    args = ap.parse_args()

    out_dir = Path(args.out).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    token = os.getenv("STEGVERSE_AUDIT_TOKEN") or os.getenv("GITHUB_TOKEN")

    repos = list_org_repos(args.org, token)
    if not repos:
        print(f"⚠ No repos found for org {args.org}")
        return 1

    # Filter
    selected: List[Dict[str, Any]] = []
    for r in repos:
        if args.skip_archived and r["archived"]:
            continue
        if args.skip_private and r["private"]:
            continue
        if r.get("disabled"):
            continue
        selected.append(r)

    print(f"🔎 Org repos found: {len(repos)} | selected for clone: {len(selected)}")
    priv = sum(1 for r in repos if r["private"])
    print(f"🔐 Private repos in org: {priv} (skipped={args.skip_private})")

    failures = 0
    for r in sorted(selected, key=lambda x: x["full_name"].lower()):
        try:
            git_clone(r, out_dir, token)
        except Exception as e:
            failures += 1
            print(f"❌ Failed cloning {r['full_name']}: {e}")

    print(f"✅ Clone pass complete. Failures: {failures}")
    return 0 if failures == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
