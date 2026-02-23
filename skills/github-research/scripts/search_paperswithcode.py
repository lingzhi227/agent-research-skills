#!/usr/bin/env python3
"""Search Papers With Code for paper-to-repo mappings.

Uses the Papers With Code public API (https://paperswithcode.com/api/v1/)
to find GitHub repositories linked to research papers. Supports lookup by
single arXiv ID, multiple IDs, a file of IDs, or keyword search.

Self-contained: stdlib only (urllib for HTTP).

Usage:
    python search_paperswithcode.py --arxiv-id 2301.12345 --output repos.jsonl
    python search_paperswithcode.py --query "multi-agent" --output repos.jsonl
    python search_paperswithcode.py --arxiv-ids-file papers.txt --output repos.jsonl
    python search_paperswithcode.py --arxiv-ids 2301.12345 2305.67890 --output repos.jsonl
"""

import argparse
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

PWC_API = "https://paperswithcode.com/api/v1"
USER_AGENT = "github-research/1.0"
REQUEST_DELAY = 1.0  # seconds between requests


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------

def pwc_request(url: str) -> dict | list | None:
    """Make a GET request to the Papers With Code API with retry logic.

    Returns parsed JSON or None on failure.
    """
    headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    req = urllib.request.Request(url, headers=headers)

    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            if e.code == 429:
                wait = 2 ** (attempt + 1)
                print(f"[warn] rate limited, waiting {wait}s ...", file=sys.stderr)
                time.sleep(wait)
                continue
            print(f"[warn] HTTP {e.code} for {url}", file=sys.stderr)
            if attempt < 2:
                time.sleep(1)
                continue
            return None
        except (urllib.error.URLError, OSError) as e:
            print(f"[warn] request failed: {e}", file=sys.stderr)
            if attempt < 2:
                time.sleep(1)
                continue
            return None
    return None


def paginate_results(url: str) -> list[dict]:
    """Follow ``next`` links and collect all ``results`` items."""
    items: list[dict] = []
    current_url: str | None = url
    while current_url:
        data = pwc_request(current_url)
        if not data or not isinstance(data, dict):
            break
        items.extend(data.get("results", []))
        current_url = data.get("next")
        if current_url:
            time.sleep(REQUEST_DELAY)
    return items


# ---------------------------------------------------------------------------
# GitHub URL parsing
# ---------------------------------------------------------------------------

def parse_repo_url(url: str) -> tuple[str, str]:
    """Parse a GitHub URL into (owner, name). Returns ("", "") if not GitHub."""
    if not url or "github.com" not in url:
        return "", ""
    url = url.rstrip("/")
    for prefix in ("https://github.com/", "http://github.com/"):
        if url.startswith(prefix):
            path = url[len(prefix):]
            parts = path.split("/")
            if len(parts) >= 2 and parts[0] and parts[1]:
                name = parts[1].removesuffix(".git")
                return parts[0], name
    return "", ""


# ---------------------------------------------------------------------------
# Repo record mapping
# ---------------------------------------------------------------------------

def map_to_repo_record(
    repo: dict,
    paper_title: str = "",
    arxiv_id: str = "",
) -> dict | None:
    """Map a PWC repository entry to the repo_db schema.

    Returns None if the URL is not a valid GitHub repo.
    """
    url = repo.get("url", "")
    owner, name = parse_repo_url(url)
    if not owner or not name:
        return None

    repo_id = f"{owner}/{name}"
    paper_ids = [arxiv_id] if arxiv_id else []
    paper_titles = [paper_title] if paper_title else []

    return {
        "repo_id": repo_id,
        "url": f"https://github.com/{repo_id}",
        "name": name,
        "owner": owner,
        "description": repo.get("description") or "",
        "stars": repo.get("stars", 0) or 0,
        "forks": 0,
        "language": repo.get("framework") or "",
        "license": "",
        "topics": [],
        "created_at": "",
        "updated_at": "",
        "pushed_at": "",
        "open_issues": 0,
        "default_branch": "main",
        "archived": False,
        "source": "paperswithcode",
        "paper_ids": paper_ids,
        "paper_titles": paper_titles,
        "is_official": repo.get("is_official", False),
        # Default fields for repo_db compatibility
        "languages_pct": {},
        "readme_excerpt": "",
        "relevance_score": 0.0,
        "quality_score": 0.0,
        "activity_score": 0.0,
        "composite_score": 0.0,
        "tags": [],
        "analyzed": False,
        "local_path": None,
    }


# ---------------------------------------------------------------------------
# Core lookup functions
# ---------------------------------------------------------------------------

def lookup_paper_by_arxiv(arxiv_id: str) -> dict | None:
    """Look up a paper on PWC by arXiv ID. Returns first matching paper or None."""
    clean_id = arxiv_id.strip()
    # Remove version suffix if present (e.g. 2301.12345v2 -> 2301.12345)
    if "v" in clean_id and clean_id[-1].isdigit():
        base, _, ver = clean_id.rpartition("v")
        if ver.isdigit():
            clean_id = base

    url = f"{PWC_API}/papers/?arxiv_id={urllib.parse.quote(clean_id, safe='')}"
    data = pwc_request(url)
    if not data or not isinstance(data, dict):
        return None

    results = data.get("results", [])
    return results[0] if results else None


def fetch_paper_repos(paper_id: str) -> list[dict]:
    """Fetch all repositories linked to a paper by its PWC paper ID."""
    url = f"{PWC_API}/papers/{urllib.parse.quote(paper_id, safe='')}/repositories/"
    return paginate_results(url)


def search_papers_by_query(query: str, max_papers: int = 50) -> list[dict]:
    """Search PWC papers by keyword query."""
    papers: list[dict] = []
    page = 1

    while len(papers) < max_papers:
        params = urllib.parse.urlencode({"q": query, "page": page})
        url = f"{PWC_API}/papers/?{params}"
        data = pwc_request(url)
        if not data or not isinstance(data, dict):
            break

        results = data.get("results", [])
        if not results:
            break

        papers.extend(results)

        if data.get("next"):
            page += 1
            time.sleep(REQUEST_DELAY)
        else:
            break

    return papers[:max_papers]


# ---------------------------------------------------------------------------
# Processing functions
# ---------------------------------------------------------------------------

def process_arxiv_id(arxiv_id: str) -> tuple[list[dict], str]:
    """Process a single arXiv ID: look up paper, fetch repos.

    Returns (repo_records, paper_title).
    """
    clean_id = arxiv_id.strip()
    if not clean_id:
        return [], ""

    print(f"  arXiv:{clean_id} ...", file=sys.stderr)
    paper = lookup_paper_by_arxiv(clean_id)
    if not paper:
        print(f"    not found on PWC", file=sys.stderr)
        return [], ""

    paper_id = paper.get("id", "")
    paper_title = paper.get("title", "")
    repo_count = paper.get("repository_count", 0)

    print(f"    {paper_title[:80]}", file=sys.stderr)
    print(f"    repos: {repo_count}", file=sys.stderr)

    if not paper_id or repo_count == 0:
        return [], paper_title

    time.sleep(REQUEST_DELAY)
    raw_repos = fetch_paper_repos(paper_id)

    records = []
    for repo in raw_repos:
        record = map_to_repo_record(repo, paper_title=paper_title, arxiv_id=clean_id)
        if record:
            records.append(record)

    print(f"    mapped {len(records)} GitHub repos", file=sys.stderr)
    return records, paper_title


def process_query(query: str) -> list[dict]:
    """Search PWC by keyword and fetch repos for matching papers."""
    print(f"[info] searching PWC for: {query}", file=sys.stderr)
    papers = search_papers_by_query(query)
    print(f"[info] found {len(papers)} papers", file=sys.stderr)

    all_records: list[dict] = []
    papers_with_repos = 0

    for i, paper in enumerate(papers):
        paper_id = paper.get("id", "")
        paper_title = paper.get("title", "")
        arxiv_id = paper.get("arxiv_id", "") or ""
        repo_count = paper.get("repository_count", 0)

        if not paper_id or repo_count == 0:
            continue

        print(
            f"  [{i + 1}/{len(papers)}] {paper_title[:60]} ({repo_count} repos)",
            file=sys.stderr,
        )

        time.sleep(REQUEST_DELAY)
        raw_repos = fetch_paper_repos(paper_id)

        for repo in raw_repos:
            record = map_to_repo_record(
                repo, paper_title=paper_title, arxiv_id=arxiv_id
            )
            if record:
                all_records.append(record)

        papers_with_repos += 1
        time.sleep(REQUEST_DELAY)

    print(f"[info] {papers_with_repos} papers had repos", file=sys.stderr)
    return all_records


def deduplicate_repos(records: list[dict]) -> list[dict]:
    """Deduplicate repos by repo_id, merging paper_ids and paper_titles."""
    seen: dict[str, dict] = {}
    for record in records:
        rid = record["repo_id"]
        if rid in seen:
            existing = seen[rid]
            # Merge paper references
            for pid in record.get("paper_ids", []):
                if pid and pid not in existing["paper_ids"]:
                    existing["paper_ids"].append(pid)
            for pt in record.get("paper_titles", []):
                if pt and pt not in existing["paper_titles"]:
                    existing["paper_titles"].append(pt)
            # Keep higher star count
            if record.get("stars", 0) > existing.get("stars", 0):
                existing["stars"] = record["stars"]
            # Prefer official repos
            if record.get("is_official", False):
                existing["is_official"] = True
        else:
            seen[rid] = record
    return list(seen.values())


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Search Papers With Code for paper-to-repo mappings."
    )
    parser.add_argument("--arxiv-id", default=None,
                        help="Single arXiv ID to look up")
    parser.add_argument("--arxiv-ids", nargs="+", default=None,
                        help="Multiple arXiv IDs")
    parser.add_argument("--arxiv-ids-file", default=None,
                        help="File with one arXiv ID per line")
    parser.add_argument("--query", default=None,
                        help="Search papers by keyword")
    parser.add_argument("--output", required=True,
                        help="Output JSONL file path")
    args = parser.parse_args()

    # Validate: at least one input source required
    if not any([args.arxiv_id, args.arxiv_ids, args.arxiv_ids_file, args.query]):
        parser.error(
            "At least one of --arxiv-id, --arxiv-ids, --arxiv-ids-file, "
            "or --query is required"
        )

    # Collect all arXiv IDs from all sources
    all_arxiv_ids: list[str] = []
    if args.arxiv_id:
        all_arxiv_ids.append(args.arxiv_id)
    if args.arxiv_ids:
        all_arxiv_ids.extend(args.arxiv_ids)
    if args.arxiv_ids_file:
        ids_file = Path(args.arxiv_ids_file)
        if not ids_file.exists():
            print(f"[error] arXiv IDs file not found: {ids_file}", file=sys.stderr)
            sys.exit(1)
        try:
            for line in ids_file.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line and not line.startswith("#"):
                    all_arxiv_ids.append(line)
        except OSError as e:
            print(f"[error] cannot read {ids_file}: {e}", file=sys.stderr)
            sys.exit(1)

    all_records: list[dict] = []
    papers_found = 0

    # Process arXiv IDs
    if all_arxiv_ids:
        print(
            f"[info] looking up {len(all_arxiv_ids)} arXiv IDs on Papers With Code ...",
            file=sys.stderr,
        )
        for arxiv_id in all_arxiv_ids:
            records, title = process_arxiv_id(arxiv_id)
            if title:
                papers_found += 1
            all_records.extend(records)
            time.sleep(REQUEST_DELAY)

    # Process keyword query
    if args.query:
        query_records = process_query(args.query)
        all_records.extend(query_records)

    # Deduplicate
    deduped = deduplicate_repos(all_records)

    # Write output
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        for record in deduped:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    # Summary
    total_paper_links = sum(len(r.get("paper_ids", [])) for r in deduped)
    official = sum(1 for r in deduped if r.get("is_official", False))

    print(f"\n[info] results summary:", file=sys.stderr)
    print(f"  repos found: {len(deduped)}", file=sys.stderr)
    print(f"  linked to papers: {total_paper_links}", file=sys.stderr)
    if official:
        print(f"  official implementations: {official}", file=sys.stderr)
    print(f"Found {len(deduped)} repos linked to {papers_found} papers", file=sys.stderr)
    print(f"[info] written to {output_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
