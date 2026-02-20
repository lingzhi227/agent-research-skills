#!/usr/bin/env python3
"""Novelty checker for research ideas via Semantic Scholar API.

Iteratively searches literature to assess if a research idea is novel.
Self-contained: uses only stdlib.

Adapted from AI-Scientist's check_idea_novelty() in generate_ideas.py.

Usage:
    python novelty_check.py --idea "Adaptive attention pruning via gradient importance"
    python novelty_check.py --idea "..." --max-rounds 10
    python novelty_check.py --idea-file idea.json
"""

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request


S2_API_KEY = os.environ.get("SEMANTIC_SCHOLAR_API_KEY", "")
S2_SEARCH_URL = "https://api.semanticscholar.org/graph/v1/paper/search"
FIELDS = "title,authors,venue,year,abstract,citationCount"


def search_semantic_scholar(query: str, limit: int = 10) -> list[dict]:
    """Search Semantic Scholar for papers matching the query."""
    params = urllib.parse.urlencode({
        "query": query,
        "limit": limit,
        "fields": FIELDS,
    })
    url = f"{S2_SEARCH_URL}?{params}"
    req = urllib.request.Request(url)
    if S2_API_KEY:
        req.add_header("X-API-KEY", S2_API_KEY)

    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode())
                return data.get("data", [])
        except urllib.error.HTTPError as e:
            if e.code == 429:
                wait = 2 ** (attempt + 1)
                print(f"  Rate limited, waiting {wait}s...", file=sys.stderr)
                time.sleep(wait)
                continue
            raise
        except urllib.error.URLError:
            time.sleep(2)
            continue
    return []


def format_paper(paper: dict) -> str:
    """Format a single paper for display."""
    title = paper.get("title", "Unknown")
    year = paper.get("year", "?")
    venue = paper.get("venue", "")
    citations = paper.get("citationCount", 0)
    authors = paper.get("authors", [])
    author_str = ", ".join(a.get("name", "") for a in authors[:3])
    if len(authors) > 3:
        author_str += " et al."
    abstract = paper.get("abstract", "") or ""
    if len(abstract) > 300:
        abstract = abstract[:300] + "..."
    venue_str = f" ({venue})" if venue else ""
    return (
        f"  [{year}] {title}{venue_str}\n"
        f"  Authors: {author_str} | Citations: {citations}\n"
        f"  Abstract: {abstract}"
    )


def generate_search_queries(idea: str) -> list[str]:
    """Generate diverse search queries from an idea description."""
    # Extract key phrases by splitting on common delimiters
    words = idea.lower().split()

    # Strategy 1: Use the full idea as a query (truncated)
    queries = [" ".join(words[:15])]

    # Strategy 2: Extract noun-phrase-like chunks
    # Look for sequences of capitalized words or technical terms
    chunks = []
    current_chunk = []
    for word in idea.split():
        if len(word) > 3 and not word.lower() in {"with", "from", "that", "this", "using", "based", "through", "which", "their", "have", "been", "into", "also", "more"}:
            current_chunk.append(word)
        else:
            if current_chunk:
                chunks.append(" ".join(current_chunk))
                current_chunk = []
    if current_chunk:
        chunks.append(" ".join(current_chunk))

    # Add the longest chunks as queries
    chunks.sort(key=len, reverse=True)
    for chunk in chunks[:3]:
        if len(chunk.split()) >= 2 and chunk not in queries:
            queries.append(chunk)

    return queries[:5]


def run_novelty_check(idea: str, max_rounds: int = 5, result_limit: int = 10) -> dict:
    """Run iterative novelty checking against Semantic Scholar.

    Returns a dict with novelty assessment and similar papers found.
    """
    print(f"Checking novelty of idea:")
    print(f"  \"{idea[:200]}{'...' if len(idea) > 200 else ''}\"")
    print()

    all_papers_seen = {}
    queries_used = []

    # Generate initial search queries
    search_queries = generate_search_queries(idea)

    for round_num in range(1, max_rounds + 1):
        if not search_queries:
            break

        query = search_queries.pop(0)
        queries_used.append(query)
        print(f"Round {round_num}/{max_rounds}: Searching \"{query}\"")

        papers = search_semantic_scholar(query, limit=result_limit)

        if not papers:
            print("  No results found.")
            print()
            continue

        new_papers = 0
        for paper in papers:
            title = paper.get("title", "")
            if title and title not in all_papers_seen:
                all_papers_seen[title] = paper
                new_papers += 1

        print(f"  Found {len(papers)} papers ({new_papers} new)")
        for paper in papers[:3]:
            print(format_paper(paper))
        if len(papers) > 3:
            print(f"  ... and {len(papers) - 3} more")
        print()

        # If we got results, try to refine with more specific queries
        if papers and round_num < max_rounds and not search_queries:
            # Generate follow-up queries from the most relevant paper titles
            for p in papers[:2]:
                t = p.get("title", "")
                if t and len(t.split()) >= 3:
                    search_queries.append(t[:80])

    # Rank by relevance (citation count as proxy)
    ranked = sorted(all_papers_seen.values(),
                    key=lambda p: p.get("citationCount", 0), reverse=True)

    result = {
        "idea": idea,
        "total_papers_found": len(all_papers_seen),
        "rounds_used": len(queries_used),
        "queries_used": queries_used,
        "most_cited_similar": [
            {
                "title": p.get("title", ""),
                "year": p.get("year"),
                "venue": p.get("venue", ""),
                "citations": p.get("citationCount", 0),
                "abstract": (p.get("abstract", "") or "")[:200],
            }
            for p in ranked[:10]
        ],
    }

    print("=" * 60)
    print(f"NOVELTY CHECK SUMMARY")
    print(f"Total unique papers found: {len(all_papers_seen)}")
    print(f"Rounds used: {len(queries_used)}/{max_rounds}")
    print()
    print("Most cited similar papers:")
    for i, p in enumerate(ranked[:5], 1):
        print(f"  {i}. [{p.get('year', '?')}] {p.get('title', '?')} "
              f"(citations: {p.get('citationCount', 0)})")
    print()
    print("NOTE: Review the papers above to determine if your idea is novel.")
    print("An idea is novel if no paper significantly overlaps with it.")
    print("=" * 60)

    return result


def main():
    parser = argparse.ArgumentParser(description="Check research idea novelty via Semantic Scholar")
    parser.add_argument("--idea", type=str, help="Research idea to check (text)")
    parser.add_argument("--idea-file", type=str, help="JSON file containing idea (must have 'Title' or 'Experiment' field)")
    parser.add_argument("--max-rounds", type=int, default=5, help="Max search rounds (default: 5)")
    parser.add_argument("--result-limit", type=int, default=10, help="Results per query (default: 10)")
    parser.add_argument("--output", type=str, help="Output JSON file for results")
    args = parser.parse_args()

    if args.idea_file:
        with open(args.idea_file, encoding="utf-8") as f:
            idea_data = json.load(f)
        idea_text = idea_data.get("Title", "") + ". " + idea_data.get("Experiment", "")
        if not idea_text.strip(". "):
            idea_text = json.dumps(idea_data)
    elif args.idea:
        idea_text = args.idea
    else:
        parser.error("Either --idea or --idea-file is required")
        return

    result = run_novelty_check(idea_text, max_rounds=args.max_rounds,
                                result_limit=args.result_limit)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"\nResults saved to {args.output}")
    else:
        print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
