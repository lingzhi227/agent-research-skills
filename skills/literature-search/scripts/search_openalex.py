#!/usr/bin/env python3
"""Search OpenAlex API and output JSONL paper metadata.

Self-contained: uses only stdlib (urllib, json).
OpenAlex is free, no API key needed, broadest coverage of academic literature.

Usage:
    python search_openalex.py --query "attention mechanism transformers" --max-results 50
    python search_openalex.py --query "graph neural networks" --min-citations 10 --year-range 2022-2026
    python search_openalex.py --query "diffusion models" --type article --sort cited_by_count:desc
"""

import argparse
import json
import sys
import time
import urllib.parse
import urllib.request


OPENALEX_API = "https://api.openalex.org"


def openalex_request(url: str) -> dict:
    """Make a request to OpenAlex API with retry logic."""
    headers = {
        "User-Agent": "research-engine/1.0 (mailto:research@example.com)",
        "Accept": "application/json",
    }
    req = urllib.request.Request(url, headers=headers)

    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read())
        except urllib.error.HTTPError as e:
            if e.code == 429:
                wait = 2 ** (attempt + 1)
                print(f"Rate limited, waiting {wait}s...", file=sys.stderr)
                time.sleep(wait)
                continue
            raise
        except Exception:
            if attempt < 2:
                time.sleep(1)
                continue
            raise
    return {}


def parse_work(work: dict) -> dict | None:
    """Parse an OpenAlex work into our standard record format."""
    if not work or not work.get("title"):
        return None

    # Authors
    authors = []
    for authorship in work.get("authorships", []):
        author = authorship.get("author", {})
        name = author.get("display_name", "")
        if name:
            authors.append(name)

    # Venue
    primary_location = work.get("primary_location", {}) or {}
    source = primary_location.get("source", {}) or {}
    venue = source.get("display_name", "")

    # ArXiv ID from locations
    arxiv_id = ""
    for loc in work.get("locations", []):
        landing = loc.get("landing_page_url", "") or ""
        if "arxiv.org" in landing:
            parts = landing.rstrip("/").split("/")
            arxiv_id = parts[-1] if parts else ""
            break

    # DOI
    doi = work.get("doi", "") or ""
    if doi.startswith("https://doi.org/"):
        doi = doi[16:]

    # PDF URL
    pdf_url = ""
    oa = work.get("open_access", {}) or {}
    pdf_url = oa.get("oa_url", "") or ""
    if not pdf_url and arxiv_id:
        pdf_url = f"https://arxiv.org/pdf/{arxiv_id}"

    # Abstract (OpenAlex uses inverted index)
    abstract = ""
    abstract_inv = work.get("abstract_inverted_index", {})
    if abstract_inv:
        # Reconstruct from inverted index
        word_positions = []
        for word, positions in abstract_inv.items():
            for pos in positions:
                word_positions.append((pos, word))
        word_positions.sort()
        abstract = " ".join(w for _, w in word_positions)

    # Peer reviewed heuristic
    work_type = work.get("type", "")
    peer_reviewed = work_type in ("article", "proceedings-article", "book-chapter")

    return {
        "openalex_id": work.get("id", ""),
        "doi": doi,
        "arxiv_id": arxiv_id,
        "title": work["title"],
        "authors": authors,
        "abstract": abstract[:1000],
        "year": work.get("publication_year"),
        "venue": venue,
        "venue_normalized": venue,
        "peer_reviewed": peer_reviewed,
        "citationCount": work.get("cited_by_count", 0),
        "url": work.get("id", ""),
        "publicationDate": work.get("publication_date", ""),
        "pdf_url": pdf_url,
        "source": "openalex",
    }


def search_works(
    query: str,
    max_results: int = 50,
    year_range: str | None = None,
    min_citations: int = 0,
    work_type: str | None = None,
    sort: str = "cited_by_count:desc",
) -> list[dict]:
    """Search OpenAlex works and return parsed results."""
    all_papers = []

    filters = []
    if year_range:
        parts = year_range.split("-")
        if len(parts) == 2:
            filters.append(f"publication_year:{parts[0]}-{parts[1]}")
    if min_citations > 0:
        filters.append(f"cited_by_count:>{min_citations}")
    if work_type:
        filters.append(f"type:{work_type}")

    page = 1
    per_page = min(50, max_results)

    while len(all_papers) < max_results:
        params = {
            "search": query,
            "per_page": per_page,
            "page": page,
            "sort": sort,
        }
        if filters:
            params["filter"] = ",".join(filters)

        url = f"{OPENALEX_API}/works?{urllib.parse.urlencode(params)}"

        try:
            resp = openalex_request(url)
        except Exception as e:
            print(f"Warning: search failed at page {page}: {e}", file=sys.stderr)
            break

        results = resp.get("results", [])
        if not results:
            break

        for work in results:
            if len(all_papers) >= max_results:
                break
            paper = parse_work(work)
            if paper:
                all_papers.append(paper)

        meta = resp.get("meta", {})
        total = meta.get("count", 0)
        if page * per_page >= total:
            break

        page += 1
        time.sleep(0.2)  # Be polite

    return all_papers


def main():
    parser = argparse.ArgumentParser(description="Search OpenAlex and output JSONL")
    parser.add_argument("--query", required=True, help="Search keywords")
    parser.add_argument("--max-results", type=int, default=50, help="Max papers to return")
    parser.add_argument("--min-citations", type=int, default=0, help="Minimum citation count")
    parser.add_argument("--year-range", help="Year range filter (e.g. 2020-2026)")
    parser.add_argument("--type", help="Work type filter (e.g. article, proceedings-article)")
    parser.add_argument("--sort", default="cited_by_count:desc", help="Sort order")
    parser.add_argument("--output", "-o", help="Output file (default: stdout)")
    args = parser.parse_args()

    papers = search_works(
        query=args.query,
        max_results=args.max_results,
        year_range=args.year_range,
        min_citations=args.min_citations,
        work_type=args.type,
        sort=args.sort,
    )

    out = open(args.output, "w") if args.output else sys.stdout
    try:
        for paper in papers:
            out.write(json.dumps(paper, ensure_ascii=False) + "\n")
    finally:
        if args.output:
            out.close()

    print(f"Found {len(papers)} papers", file=sys.stderr)


if __name__ == "__main__":
    main()
