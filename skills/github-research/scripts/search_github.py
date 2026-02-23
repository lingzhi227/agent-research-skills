#!/usr/bin/env python3
"""Search GitHub repositories via `gh api` with multiple query strategies.

Builds qualified search queries and paginates through results, outputting
repo_db-compatible JSONL records.
"""

import argparse
import json
import math
import shutil
import subprocess
import sys
import time
from pathlib import Path

RESULTS_PER_PAGE = 30
DEFAULT_MAX_RESULTS = 100


def check_gh_installed():
    """Verify gh CLI is available."""
    if not shutil.which("gh"):
        print("[error] gh CLI not found. Install it: https://cli.github.com/", file=sys.stderr)
        sys.exit(1)


def gh_api(endpoint: str, params: dict | None = None) -> dict:
    """Call gh api and return parsed JSON."""
    if params:
        from urllib.parse import urlencode
        endpoint = f"{endpoint}?{urlencode(params)}"
    cmd = ["gh", "api", endpoint]
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except FileNotFoundError:
        print("[error] gh CLI not found", file=sys.stderr)
        sys.exit(1)
    except subprocess.TimeoutExpired:
        print("[error] gh api call timed out", file=sys.stderr)
        sys.exit(1)

    if result.returncode != 0:
        stderr = result.stderr.strip()
        # Check for rate limit
        if "rate limit" in stderr.lower() or "403" in stderr:
            print(f"[error] GitHub API rate limit hit: {stderr}", file=sys.stderr)
            sys.exit(1)
        print(f"[error] gh api failed (exit {result.returncode}): {stderr}", file=sys.stderr)
        sys.exit(1)

    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as e:
        print(f"[error] invalid JSON from gh api: {e}", file=sys.stderr)
        sys.exit(1)


def build_query(query: str, language: str | None, min_stars: int | None, topic: str | None) -> str:
    """Build GitHub search query string with qualifiers."""
    parts = [query]
    if language:
        parts.append(f"language:{language}")
    if min_stars is not None and min_stars > 0:
        parts.append(f"stars:>={min_stars}")
    if topic:
        parts.append(f"topic:{topic}")
    return " ".join(parts)


def extract_license(license_obj) -> str:
    """Extract license identifier from GitHub API license object."""
    if not license_obj or not isinstance(license_obj, dict):
        return ""
    return license_obj.get("spdx_id") or license_obj.get("name") or ""


def map_repo(item: dict) -> dict:
    """Map a GitHub API repository item to repo_db schema."""
    owner_obj = item.get("owner") or {}
    return {
        "repo_id": item.get("full_name", ""),
        "url": item.get("html_url", ""),
        "name": item.get("name", ""),
        "owner": owner_obj.get("login", ""),
        "description": item.get("description") or "",
        "stars": item.get("stargazers_count", 0),
        "forks": item.get("forks_count", 0),
        "language": item.get("language") or "",
        "license": extract_license(item.get("license")),
        "topics": item.get("topics", []),
        "created_at": item.get("created_at", ""),
        "updated_at": item.get("updated_at", ""),
        "pushed_at": item.get("pushed_at", ""),
        "open_issues": item.get("open_issues_count", 0),
        "default_branch": item.get("default_branch", "main"),
        "archived": item.get("archived", False),
        "source": "search_github",
        # Default fields for repo_db compatibility
        "languages_pct": {},
        "readme_excerpt": "",
        "paper_ids": [],
        "paper_titles": [],
        "relevance_score": 0.0,
        "quality_score": 0.0,
        "activity_score": 0.0,
        "composite_score": 0.0,
        "tags": [],
        "analyzed": False,
        "local_path": None,
    }


def check_rate_limit():
    """Check GitHub API rate limit and warn if approaching it."""
    try:
        result = subprocess.run(
            ["gh", "api", "rate_limit"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            data = json.loads(result.stdout)
            search = data.get("resources", {}).get("search", {})
            remaining = search.get("remaining", -1)
            limit = search.get("limit", -1)
            reset_ts = search.get("reset", 0)

            if remaining >= 0:
                if remaining <= 3:
                    reset_time = time.strftime("%H:%M:%S", time.localtime(reset_ts))
                    print(
                        f"[warn] GitHub search API rate limit: {remaining}/{limit} remaining, "
                        f"resets at {reset_time}",
                        file=sys.stderr,
                    )
                else:
                    print(f"[info] rate limit: {remaining}/{limit} search requests remaining", file=sys.stderr)
    except (subprocess.TimeoutExpired, json.JSONDecodeError, OSError):
        pass  # Non-critical, skip


def search_repos(
    query: str,
    sort: str,
    max_results: int,
) -> list[dict]:
    """Search GitHub repositories with pagination."""
    total_pages = math.ceil(max_results / RESULTS_PER_PAGE)
    all_repos = []
    seen_ids = set()

    for page in range(1, total_pages + 1):
        print(f"[info] fetching page {page}/{total_pages} ...", file=sys.stderr)

        params = {
            "q": query,
            "sort": sort,
            "order": "desc",
            "per_page": str(min(RESULTS_PER_PAGE, max_results - len(all_repos))),
            "page": str(page),
        }

        data = gh_api("/search/repositories", params)

        total_count = data.get("total_count", 0)
        if page == 1:
            print(f"[info] total matching repos: {total_count}", file=sys.stderr)

        items = data.get("items", [])
        if not items:
            print("[info] no more results", file=sys.stderr)
            break

        for item in items:
            repo = map_repo(item)
            if repo["repo_id"] not in seen_ids:
                seen_ids.add(repo["repo_id"])
                all_repos.append(repo)

            if len(all_repos) >= max_results:
                break

        if len(all_repos) >= max_results:
            break

        # Incomplete results means GitHub truncated
        if data.get("incomplete_results", False):
            print("[warn] GitHub returned incomplete results (query too broad?)", file=sys.stderr)

        # Respect rate limit: sleep 2s between pages for search API
        if page < total_pages:
            time.sleep(2)

    return all_repos


def main():
    parser = argparse.ArgumentParser(
        description="Search GitHub repositories via gh API with flexible query strategies."
    )
    parser.add_argument("--query", required=True, help="Search query string")
    parser.add_argument("--language", default=None, help="Filter by programming language")
    parser.add_argument("--min-stars", type=int, default=None, help="Minimum star count")
    parser.add_argument(
        "--sort",
        choices=["stars", "updated", "best-match"],
        default="best-match",
        help="Sort order (default: best-match)",
    )
    parser.add_argument("--max-results", type=int, default=DEFAULT_MAX_RESULTS, help="Max results to fetch (default: 100)")
    parser.add_argument("--topic", default=None, help="Filter by GitHub topic")
    parser.add_argument("--output", required=True, help="Output JSONL file path")
    args = parser.parse_args()

    check_gh_installed()

    # Build the qualified query
    full_query = build_query(args.query, args.language, args.min_stars, args.topic)
    print(f"[info] search query: {full_query}", file=sys.stderr)
    print(f"[info] sort: {args.sort}, max: {args.max_results}", file=sys.stderr)

    # Check rate limit before starting
    check_rate_limit()

    # Handle "best-match" -> empty sort for GitHub API (relevance is default)
    sort_param = "" if args.sort == "best-match" else args.sort

    repos = search_repos(full_query, sort_param, args.max_results)

    # Write output
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        for repo in repos:
            f.write(json.dumps(repo, ensure_ascii=False) + "\n")

    # Summary stats
    print(f"\n[info] results summary:", file=sys.stderr)
    print(f"  repos found: {len(repos)}", file=sys.stderr)
    if repos:
        languages = {}
        for r in repos:
            lang = r["language"] or "unknown"
            languages[lang] = languages.get(lang, 0) + 1
        top_langs = sorted(languages.items(), key=lambda x: -x[1])[:5]
        print(f"  top languages: {', '.join(f'{l}({c})' for l, c in top_langs)}", file=sys.stderr)

        star_counts = [r["stars"] for r in repos]
        print(f"  stars range: {min(star_counts)} - {max(star_counts)}", file=sys.stderr)

    print(f"[info] written to {output_path}", file=sys.stderr)

    # Check rate limit after
    check_rate_limit()


if __name__ == "__main__":
    main()
