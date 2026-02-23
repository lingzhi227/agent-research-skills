#!/usr/bin/env python3
"""Search GitHub code for specific function/class implementations via `gh api`.

Searches code using GitHub's code search API, groups results by repo, and
outputs both code-level matches (stderr) and repo-level JSONL (--output).
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
DEFAULT_MAX_RESULTS = 50


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


def build_code_query(query: str, language: str | None, filename: str | None) -> str:
    """Build GitHub code search query with qualifiers."""
    parts = [query]
    if language:
        parts.append(f"language:{language}")
    if filename:
        parts.append(f"filename:{filename}")
    return " ".join(parts)


def search_code(query: str, max_results: int) -> list[dict]:
    """Search GitHub code with pagination."""
    total_pages = math.ceil(max_results / RESULTS_PER_PAGE)
    all_items = []

    for page in range(1, total_pages + 1):
        print(f"[info] fetching page {page}/{total_pages} ...", file=sys.stderr)

        params = {
            "q": query,
            "per_page": str(min(RESULTS_PER_PAGE, max_results - len(all_items))),
            "page": str(page),
        }

        data = gh_api("/search/code", params)

        total_count = data.get("total_count", 0)
        if page == 1:
            print(f"[info] total matching files: {total_count}", file=sys.stderr)

        items = data.get("items", [])
        if not items:
            print("[info] no more results", file=sys.stderr)
            break

        all_items.extend(items)

        if len(all_items) >= max_results:
            all_items = all_items[:max_results]
            break

        if data.get("incomplete_results", False):
            print("[warn] GitHub returned incomplete results", file=sys.stderr)

        # Code search is heavily rate limited: 10 req/min
        if page < total_pages:
            time.sleep(6)

    return all_items


def extract_code_match(item: dict) -> dict:
    """Extract a code match record from a search result item."""
    repo = item.get("repository", {})
    owner_obj = repo.get("owner", {})
    full_name = repo.get("full_name", "")

    # text_matches may be present if Accept header includes text-match
    text_fragments = []
    for tm in item.get("text_matches", []):
        fragment = tm.get("fragment", "")
        if fragment:
            text_fragments.append(fragment)

    return {
        "repo_id": full_name,
        "file_path": item.get("path", ""),
        "file_url": item.get("html_url", ""),
        "file_name": item.get("name", ""),
        "matched_text": "\n---\n".join(text_fragments) if text_fragments else "",
        "context": {
            "sha": item.get("sha", ""),
            "score": item.get("score", 0),
        },
    }


def build_repo_record(repo_id: str, repo_data: dict) -> dict:
    """Build a minimal repo_db-compatible record from code search results."""
    owner = repo_id.split("/")[0] if "/" in repo_id else ""
    name = repo_id.split("/")[1] if "/" in repo_id else repo_id

    return {
        "repo_id": repo_id,
        "url": f"https://github.com/{repo_id}",
        "name": name,
        "owner": owner,
        "description": repo_data.get("description", ""),
        "stars": 0,
        "forks": 0,
        "language": "",
        "license": "",
        "topics": [],
        "created_at": "",
        "updated_at": "",
        "pushed_at": "",
        "open_issues": 0,
        "default_branch": "main",
        "archived": False,
        "source": "code_search",
        "code_matches": repo_data.get("files", []),
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


def main():
    parser = argparse.ArgumentParser(
        description="Search GitHub code for function/class implementations via gh API."
    )
    parser.add_argument("--query", required=True, help="Code search query string")
    parser.add_argument("--language", default=None, help="Filter by programming language")
    parser.add_argument("--filename", default=None, help="Filter by filename pattern")
    parser.add_argument("--max-results", type=int, default=DEFAULT_MAX_RESULTS, help="Max code results to fetch (default: 50)")
    parser.add_argument("--output", required=True, help="Output JSONL file for repo-level records")
    args = parser.parse_args()

    check_gh_installed()

    full_query = build_code_query(args.query, args.language, args.filename)
    print(f"[info] code search query: {full_query}", file=sys.stderr)
    print(f"[info] max results: {args.max_results}", file=sys.stderr)

    items = search_code(full_query, args.max_results)

    # Process matches and group by repo
    code_matches = []
    repos: dict[str, dict] = {}  # repo_id -> {description, file_count, files}

    for item in items:
        match = extract_code_match(item)
        code_matches.append(match)

        rid = match["repo_id"]
        if rid not in repos:
            repo_obj = item.get("repository", {})
            repos[rid] = {
                "description": repo_obj.get("description") or "",
                "file_count": 0,
                "files": [],
            }
        repos[rid]["file_count"] += 1
        repos[rid]["files"].append(match["file_path"])

    # Print code matches to stderr, grouped by repo
    print(f"\n{'=' * 60}", file=sys.stderr)
    print(f"Code matches: {len(code_matches)} files in {len(repos)} repos", file=sys.stderr)
    print(f"{'=' * 60}", file=sys.stderr)

    for rid in sorted(repos.keys()):
        info = repos[rid]
        print(f"\n  {rid} ({info['file_count']} files)", file=sys.stderr)
        if info["description"]:
            print(f"    {info['description'][:100]}", file=sys.stderr)
        for fpath in info["files"][:5]:
            print(f"    - {fpath}", file=sys.stderr)
        if len(info["files"]) > 5:
            print(f"    ... and {len(info['files']) - 5} more", file=sys.stderr)

    # Write repo-level JSONL to --output (for feeding into repo_db merge)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        for rid, rdata in sorted(repos.items()):
            record = build_repo_record(rid, rdata)
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f"\n[info] wrote {len(repos)} repo records to {output_path}", file=sys.stderr)

    # Also write code-level matches alongside (with .code suffix)
    code_output = output_path.with_suffix(".code.jsonl")
    with open(code_output, "w", encoding="utf-8") as f:
        for match in code_matches:
            f.write(json.dumps(match, ensure_ascii=False) + "\n")

    print(f"[info] wrote {len(code_matches)} code matches to {code_output}", file=sys.stderr)


if __name__ == "__main__":
    main()
