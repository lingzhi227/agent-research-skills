#!/usr/bin/env python3
"""Harvest missing citations for a LaTeX paper.

Scans .tex for under-cited claims (sentences with factual assertions but no \\cite),
generates search queries, calls Semantic Scholar API, and outputs candidate BibTeX entries.

Self-contained: uses only stdlib.

Usage:
    python harvest_citations.py --tex main.tex --bib references.bib --output candidates.bib
    python harvest_citations.py --tex main.tex --bib references.bib --max-rounds 10 --dry-run
    python harvest_citations.py --tex main.tex --bib references.bib --output candidates.bib --verbose
"""

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

S2_API = "https://api.semanticscholar.org/graph/v1/paper/search"

CLAIM_PATTERNS = [
    r"(?:has been shown|have been shown|was shown|were shown|is known|are known)",
    r"(?:recent(?:ly)?|prior|previous) (?:work|studies?|research|methods?|approaches?)",
    r"(?:state[- ]of[- ]the[- ]art|SOTA|benchmark)",
    r"(?:outperform|surpass|exceed|achieve|obtain|report|demonstrate|propose|introduce)",
    r"(?:widely used|commonly used|popular|well-known|established)",
    r"(?:inspired by|motivated by|based on|building on|following)",
    r"(?:\d+\.?\d*)\s*%",  # Numbers that likely need citation
]

COMMON_WORDS = {
    "a", "an", "the", "of", "in", "on", "at", "to", "for", "and", "or",
    "is", "are", "was", "were", "be", "been", "with", "from", "by", "as",
    "we", "our", "this", "that", "these", "those", "it", "its",
}


def extract_existing_keys(bib_content: str) -> set[str]:
    """Extract all BibTeX keys from .bib file."""
    return set(re.findall(r"@\w+\{([^,]+),", bib_content))


def extract_cited_keys(tex_content: str) -> set[str]:
    """Extract all cited keys from .tex file."""
    keys = set()
    for match in re.findall(r"\\cite[a-z]*\{([^}]+)\}", tex_content):
        for key in match.split(","):
            keys.add(key.strip())
    return keys


def find_uncited_claims(tex_content: str) -> list[dict]:
    """Find sentences with factual claims that lack citations."""
    # Remove comments
    text = re.sub(r"%.*$", "", tex_content, flags=re.MULTILINE)
    # Remove math environments
    text = re.sub(r"\$\$.*?\$\$", "", text, flags=re.DOTALL)
    text = re.sub(r"\$.*?\$", "", text)
    # Remove commands but keep text
    text = re.sub(r"\\(?:begin|end)\{[^}]+\}", "", text)

    sentences = re.split(r"(?<=[.!?])\s+", text)
    claims = []

    for sent in sentences:
        sent = sent.strip()
        if not sent or len(sent) < 30:
            continue
        # Skip if already has a citation
        if re.search(r"\\cite", sent):
            continue
        # Check for claim patterns
        for pattern in CLAIM_PATTERNS:
            if re.search(pattern, sent, re.IGNORECASE):
                # Extract key terms for search query
                words = re.findall(r"[A-Za-z]+", sent)
                content_words = [w for w in words if w.lower() not in COMMON_WORDS and len(w) > 2]
                query = " ".join(content_words[:8])
                claims.append({
                    "sentence": sent[:200],
                    "pattern": pattern,
                    "query": query,
                })
                break

    return claims


def search_semantic_scholar(query: str, limit: int = 3, api_key: str = "") -> list[dict]:
    """Search Semantic Scholar for papers matching the query."""
    params = urllib.parse.urlencode({
        "query": query,
        "limit": limit,
        "fields": "title,authors,year,venue,externalIds,citationCount,abstract",
    })
    url = f"{S2_API}?{params}"
    headers = {"User-Agent": "SkillScript/1.0"}
    if api_key:
        headers["x-api-key"] = api_key

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return data.get("data", [])
    except Exception as e:
        print(f"  S2 API error: {e}", file=sys.stderr)
        return []


def make_bibtex_key(paper: dict) -> str:
    """Generate a BibTeX key from a Semantic Scholar paper."""
    authors = paper.get("authors", [])
    family = ""
    if authors:
        name = authors[0].get("name", "")
        parts = name.split()
        family = re.sub(r"[^a-zA-Z]", "", parts[-1]) if parts else ""
    year = str(paper.get("year", ""))
    title = paper.get("title", "")
    title_words = re.findall(r"[A-Za-z]+", title)
    content_words = [w.lower() for w in title_words if w.lower() not in COMMON_WORDS]
    title_part = content_words[0] if content_words else ""
    return family.lower() + year + title_part


def paper_to_bibtex(paper: dict, key: str) -> str:
    """Convert a Semantic Scholar paper to a BibTeX entry."""
    title = paper.get("title", "")
    authors = " and ".join(a.get("name", "") for a in paper.get("authors", []))
    year = str(paper.get("year", ""))
    venue = paper.get("venue", "")
    doi = ""
    ext_ids = paper.get("externalIds", {})
    if ext_ids:
        doi = ext_ids.get("DOI", "")

    if venue:
        entry_type = "inproceedings"
        lines = [f"@inproceedings{{{key},"]
        lines.append(f"  author = {{{authors}}},")
        lines.append(f"  title = {{{title}}},")
        lines.append(f"  booktitle = {{{venue}}},")
        lines.append(f"  year = {{{year}}},")
    else:
        entry_type = "article"
        lines = [f"@article{{{key},"]
        lines.append(f"  author = {{{authors}}},")
        lines.append(f"  title = {{{title}}},")
        lines.append(f"  year = {{{year}}},")

    if doi:
        lines.append(f"  doi = {{{doi}}},")
    lines.append("}")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Harvest missing citations for a LaTeX paper")
    parser.add_argument("--tex", required=True, help="Main .tex file")
    parser.add_argument("--bib", required=True, help=".bib file")
    parser.add_argument("--output", "-o", help="Output .bib file for candidates")
    parser.add_argument("--max-rounds", type=int, default=10, help="Max harvesting rounds (default: 10)")
    parser.add_argument("--api-key", default="", help="Semantic Scholar API key")
    parser.add_argument("--dry-run", action="store_true", help="Only show claims, don't search")
    parser.add_argument("--verbose", action="store_true", help="Print detailed progress")
    args = parser.parse_args()

    with open(args.tex, encoding="utf-8", errors="replace") as f:
        tex_content = f.read()
    with open(args.bib, encoding="utf-8", errors="replace") as f:
        bib_content = f.read()

    existing_keys = extract_existing_keys(bib_content)
    cited_keys = extract_cited_keys(tex_content)
    claims = find_uncited_claims(tex_content)

    print(f"Existing bib entries: {len(existing_keys)}", file=sys.stderr)
    print(f"Cited keys in tex: {len(cited_keys)}", file=sys.stderr)
    print(f"Uncited claims found: {len(claims)}", file=sys.stderr)

    if args.dry_run:
        print(f"\n## Uncited Claims (top {min(len(claims), args.max_rounds)}):")
        for i, claim in enumerate(claims[:args.max_rounds]):
            print(f"\n[{i+1}] {claim['sentence'][:120]}...")
            print(f"    Pattern: {claim['pattern']}")
            print(f"    Query: {claim['query']}")
        sys.exit(0)

    if not claims:
        print("No uncited claims found.", file=sys.stderr)
        sys.exit(0)

    candidates = []
    used_keys = set(existing_keys)
    rounds = min(len(claims), args.max_rounds)

    for i, claim in enumerate(claims[:rounds]):
        print(f"\n[{i+1}/{rounds}] Searching for: {claim['query'][:60]}...", file=sys.stderr)
        papers = search_semantic_scholar(claim["query"], limit=3, api_key=args.api_key)
        time.sleep(1)  # Rate limiting

        if not papers:
            if args.verbose:
                print(f"  No results found.", file=sys.stderr)
            continue

        # Pick the most cited result
        papers.sort(key=lambda p: p.get("citationCount", 0), reverse=True)
        best = papers[0]
        key = make_bibtex_key(best)
        if not key or key in used_keys:
            if args.verbose:
                print(f"  Skipping duplicate key: {key}", file=sys.stderr)
            continue

        used_keys.add(key)
        bibtex = paper_to_bibtex(best, key)
        candidates.append(bibtex)

        if args.verbose:
            print(f"  Found: {best.get('title', '')[:60]}", file=sys.stderr)
            print(f"  Key: {key}, Citations: {best.get('citationCount', 0)}", file=sys.stderr)

    print(f"\nHarvested {len(candidates)} candidate citations.", file=sys.stderr)

    if candidates:
        output_text = "\n\n".join(candidates) + "\n"
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(output_text)
            print(f"Written to: {args.output}", file=sys.stderr)
        else:
            print(output_text)


if __name__ == "__main__":
    main()
