#!/usr/bin/env python3
"""Search arxiv via the Atom API and output JSONL paper metadata.

Self-contained: uses only stdlib (urllib, xml.etree).

Usage:
    python search_arxiv.py --query "long context reasoning" --max-results 50
    python search_arxiv.py --query "protein language model" --categories q-bio.BM cs.LG --max-results 100
    python search_arxiv.py --query "LLM agent" --sort-by lastUpdatedDate --start-date 2024-01-01
"""

import argparse
import json
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime

ARXIV_API = "http://export.arxiv.org/api/query"
NS = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}

SORT_MAP = {
    "relevance": "relevance",
    "lastUpdatedDate": "lastUpdatedDate",
    "submittedDate": "submittedDate",
}


def build_query(keywords: str, categories: list[str] | None = None) -> str:
    """Build an arxiv search query string."""
    parts = []
    # keyword search across all fields
    parts.append(f"all:{keywords}")
    if categories:
        cat_query = " OR ".join(f"cat:{c}" for c in categories)
        parts.append(f"({cat_query})")
    return " AND ".join(parts)


def fetch_results(
    query: str,
    start: int,
    max_results: int,
    sort_by: str = "relevance",
    sort_order: str = "descending",
) -> bytes:
    """Fetch a page of results from the arxiv API."""
    params = {
        "search_query": query,
        "start": start,
        "max_results": max_results,
        "sortBy": sort_by,
        "sortOrder": sort_order,
    }
    url = f"{ARXIV_API}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"User-Agent": "deep-research/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read()


def parse_entry(entry: ET.Element) -> dict:
    """Parse a single Atom entry into a paper record."""
    def text(tag: str, ns: str = "atom") -> str:
        el = entry.find(f"{ns}:{tag}", NS) if ns else entry.find(tag)
        return el.text.strip() if el is not None and el.text else ""

    # Extract arxiv ID from the entry id URL
    entry_id = text("id")
    arxiv_id = entry_id.split("/abs/")[-1] if "/abs/" in entry_id else entry_id

    # Authors
    authors = []
    for author_el in entry.findall("atom:author", NS):
        name_el = author_el.find("atom:name", NS)
        if name_el is not None and name_el.text:
            authors.append(name_el.text.strip())

    # Categories
    categories = []
    for cat_el in entry.findall("arxiv:primary_category", NS):
        term = cat_el.get("term", "")
        if term:
            categories.append(term)
    for cat_el in entry.findall("atom:category", NS):
        term = cat_el.get("term", "")
        if term and term not in categories:
            categories.append(term)

    # PDF link
    pdf_url = ""
    for link_el in entry.findall("atom:link", NS):
        if link_el.get("title") == "pdf":
            pdf_url = link_el.get("href", "")
            break
    if not pdf_url and arxiv_id:
        pdf_url = f"https://arxiv.org/pdf/{arxiv_id}"

    # Comment (often contains page count, conference info)
    comment = text("comment", "arxiv")

    # Abstract: normalize whitespace
    abstract = " ".join(text("summary").split())

    published = text("published")
    year = int(published[:4]) if len(published) >= 4 else None

    return {
        "arxiv_id": arxiv_id,
        "title": " ".join(text("title").split()),
        "authors": authors,
        "abstract": abstract,
        "year": year,
        "published": published,
        "updated": text("updated"),
        "categories": categories,
        "pdf_url": pdf_url,
        "comment": comment,
        "source": "arxiv",
    }


def search(
    keywords: str,
    categories: list[str] | None = None,
    max_results: int = 50,
    sort_by: str = "relevance",
    start_date: str | None = None,
    end_date: str | None = None,
) -> list[dict]:
    """Run a full paginated search and return deduplicated results."""
    query = build_query(keywords, categories)
    page_size = min(max_results, 100)  # arxiv max per request
    all_papers = []
    seen_ids = set()

    for start in range(0, max_results, page_size):
        fetch_count = min(page_size, max_results - start)
        try:
            xml_data = fetch_results(query, start, fetch_count, sort_by)
        except Exception as e:
            print(f"Warning: fetch failed at offset {start}: {e}", file=sys.stderr)
            break

        root = ET.fromstring(xml_data)
        entries = root.findall("atom:entry", NS)
        if not entries:
            break

        for entry in entries:
            paper = parse_entry(entry)
            if not paper["title"] or paper["arxiv_id"] in seen_ids:
                continue

            # Date filtering
            if start_date or end_date:
                pub = paper["published"][:10]  # YYYY-MM-DD
                if start_date and pub < start_date:
                    continue
                if end_date and pub > end_date:
                    continue

            seen_ids.add(paper["arxiv_id"])
            all_papers.append(paper)

        # Respect rate limit: 1 request per 3 seconds
        if start + page_size < max_results:
            time.sleep(3)

    return all_papers


def main():
    parser = argparse.ArgumentParser(description="Search arxiv and output JSONL")
    parser.add_argument("--query", required=True, help="Search keywords")
    parser.add_argument("--max-results", type=int, default=50, help="Max papers to return")
    parser.add_argument("--categories", nargs="*", help="arxiv categories (e.g. cs.AI cs.CL q-bio.BM)")
    parser.add_argument("--sort-by", choices=list(SORT_MAP.keys()), default="relevance")
    parser.add_argument("--start-date", help="Filter: earliest publication date (YYYY-MM-DD)")
    parser.add_argument("--end-date", help="Filter: latest publication date (YYYY-MM-DD)")
    parser.add_argument("--output", "-o", help="Output file (default: stdout)")
    args = parser.parse_args()

    papers = search(
        keywords=args.query,
        categories=args.categories,
        max_results=args.max_results,
        sort_by=SORT_MAP[args.sort_by],
        start_date=args.start_date,
        end_date=args.end_date,
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
