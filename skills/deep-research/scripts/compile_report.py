#!/usr/bin/env python3
"""Compile research notes into a final report with numbered citations and BibTeX.

Reads notes/*.md + paper_db.jsonl + code_repos.md from a topic directory
and generates report.md with proper [1], [2] citations and references.bib.

Self-contained: uses only stdlib.

Usage:
    python compile_report.py --topic-dir output/long-horizon-reasoning/
"""

import argparse
import json
import os
import re
import sys
from collections import Counter


def load_papers(jsonl_path: str) -> list[dict]:
    """Load paper records from JSONL."""
    papers = []
    if not os.path.exists(jsonl_path):
        return papers
    with open(jsonl_path) as f:
        for line in f:
            line = line.strip()
            if line:
                papers.append(json.loads(line))
    return papers


def load_text(path: str) -> str:
    """Load a text file, return empty string if missing."""
    if not os.path.exists(path):
        return ""
    with open(path) as f:
        return f.read()


def make_cite_key(paper: dict) -> str:
    """Generate a citation key from a paper record."""
    arxiv_id = paper.get("arxiv_id", "")
    if arxiv_id:
        return arxiv_id.replace("/", "_").replace(".", "_")
    # Fallback: first author last name + year
    authors = paper.get("authors", [])
    first = authors[0].split()[-1].lower() if authors else "unknown"
    year = paper.get("year") or paper.get("published", "")[:4] or "0000"
    title_word = paper.get("title", "").split()[0].lower() if paper.get("title") else "paper"
    return f"{first}{year}_{title_word}"


def paper_to_bibtex(paper: dict, cite_key: str) -> str:
    """Convert a paper record to BibTeX entry."""
    authors = " and ".join(paper.get("authors", ["Unknown"]))
    title = paper.get("title", "Unknown")
    year = paper.get("year") or paper.get("published", "")[:4] or ""
    venue = paper.get("venue", "")
    arxiv_id = paper.get("arxiv_id", "")
    url = paper.get("url", "")

    if venue:
        entry_type = "inproceedings"
        venue_field = f"  booktitle = {{{venue}}},"
    elif arxiv_id:
        entry_type = "article"
        venue_field = f"  journal = {{arXiv preprint arXiv:{arxiv_id}}},"
    else:
        entry_type = "article"
        venue_field = ""

    lines = [
        f"@{entry_type}{{{cite_key},",
        f"  title = {{{title}}},",
        f"  author = {{{authors}}},",
        f"  year = {{{year}}},",
    ]
    if venue_field:
        lines.append(venue_field)
    if url:
        lines.append(f"  url = {{{url}}},")
    lines.append("}")
    return "\n".join(lines)


def build_citation_map(papers: list[dict]) -> dict[str, tuple[int, dict]]:
    """Build a map from various paper identifiers to (number, paper).

    Keys used: arxiv_id, paperId, cite_key, and partial title matches.
    """
    cite_map = {}
    for i, paper in enumerate(papers, 1):
        cite_key = make_cite_key(paper)
        paper["_cite_key"] = cite_key
        paper["_cite_num"] = i

        if paper.get("arxiv_id"):
            cite_map[paper["arxiv_id"]] = (i, paper)
        if paper.get("paperId"):
            cite_map[paper["paperId"]] = (i, paper)
        cite_map[cite_key] = (i, paper)

    return cite_map


def replace_citations(text: str, cite_map: dict[str, tuple[int, dict]]) -> str:
    """Replace [@key] citations in text with numbered [N] references."""
    def replacer(match):
        key = match.group(1)
        if key in cite_map:
            num, _ = cite_map[key]
            return f"[{num}]"
        return match.group(0)  # leave unchanged if not found

    return re.sub(r"\[@([^\]]+)\]", replacer, text)


def compute_stats(papers: list[dict]) -> str:
    """Generate summary statistics section."""
    if not papers:
        return "No papers in database."

    lines = []
    lines.append(f"**Total papers**: {len(papers)}")

    # By year (normalize to int for consistent grouping)
    def normalize_year(y):
        if y is None:
            return "Unknown"
        try:
            return int(y)
        except (ValueError, TypeError):
            return "Unknown"

    years = Counter(normalize_year(p.get("year")) for p in papers)
    lines.append("\n**Papers by year**:")
    for year in sorted(years.keys(), key=lambda x: (0, 0) if x == "Unknown" else (1, x), reverse=True):
        lines.append(f"- {year}: {years[year]}")

    # By venue (top 10)
    venues = Counter(p.get("venue", "") or "Preprint" for p in papers)
    top_venues = venues.most_common(10)
    lines.append("\n**Top venues**:")
    for venue, count in top_venues:
        lines.append(f"- {venue}: {count}")

    # Top cited
    cited = sorted(papers, key=lambda p: p.get("citationCount", 0) or 0, reverse=True)[:10]
    if any(p.get("citationCount", 0) for p in cited):
        lines.append("\n**Most cited papers**:")
        for p in cited:
            cc = p.get("citationCount", 0) or 0
            if cc > 0:
                lines.append(f"- [{p.get('_cite_num', '?')}] {p['title'][:80]} ({cc} citations)")

    return "\n".join(lines)


def load_notes(topic_dir: str) -> str:
    """Load note files from phase-based directory structure.

    Searches for notes in this order:
    1. Phase-based: phase1_frontier/frontier.md, phase2_survey/survey.md, etc.
    2. Legacy notes/ directory: notes/frontier.md, notes/survey.md, etc.
    3. Legacy single file: notes.md
    """
    # Phase-based note locations (new structure)
    phase_notes = [
        ("phase1_frontier", "frontier.md"),
        ("phase2_survey", "survey.md"),
        ("phase3_deep_dive", "deep_dive.md"),
        ("phase5_synthesis", "synthesis.md"),
        ("phase5_synthesis", "gaps.md"),
    ]
    parts = []
    for subdir, filename in phase_notes:
        path = os.path.join(topic_dir, subdir, filename)
        if os.path.exists(path):
            content = load_text(path)
            if content.strip():
                parts.append(content)

    if parts:
        return "\n\n---\n\n".join(parts)

    # Fallback: legacy notes/ directory
    notes_dir = os.path.join(topic_dir, "notes")
    legacy_files = ["frontier.md", "survey.md", "deep_dive.md", "synthesis.md", "gaps.md"]
    if os.path.isdir(notes_dir):
        for name in legacy_files:
            path = os.path.join(notes_dir, name)
            if os.path.exists(path):
                content = load_text(path)
                if content.strip():
                    parts.append(content)

    if not parts:
        fallback = load_text(os.path.join(topic_dir, "notes.md"))
        if fallback.strip():
            parts.append(fallback)

    return "\n\n---\n\n".join(parts)


def compile_report(topic_dir: str):
    """Compile all materials into a final report."""
    paper_db_path = os.path.join(topic_dir, "paper_db.jsonl")

    # Code repos: phase-based first, then legacy fallbacks
    code_path = os.path.join(topic_dir, "phase4_code", "code_repos.md")
    if not os.path.exists(code_path):
        code_path = os.path.join(topic_dir, "code_repos.md")
    if not os.path.exists(code_path):
        code_path = os.path.join(topic_dir, "code_resources.md")

    # Report output: phase-based directory
    report_dir = os.path.join(topic_dir, "phase6_report")
    os.makedirs(report_dir, exist_ok=True)
    report_path = os.path.join(report_dir, "report.md")
    bib_path = os.path.join(report_dir, "references.bib")

    papers = load_papers(paper_db_path)
    notes = load_notes(topic_dir)
    code_resources = load_text(code_path)

    if not papers and not notes:
        print("Warning: no papers or notes found", file=sys.stderr)

    cite_map = build_citation_map(papers)

    # Process notes: replace [@key] with [N]
    processed_notes = replace_citations(notes, cite_map)

    # Build report
    report_parts = []

    # Title
    topic_name = os.path.basename(topic_dir.rstrip("/")).replace("-", " ").title()
    report_parts.append(f"# Research Report: {topic_name}\n")
    report_parts.append(f"*Generated from {len(papers)} papers*\n")

    # Statistics
    report_parts.append("## Paper Statistics\n")
    report_parts.append(compute_stats(papers))

    # Notes (the main content)
    if processed_notes:
        report_parts.append("\n---\n")
        report_parts.append(processed_notes)

    # Code resources
    if code_resources:
        report_parts.append("\n---\n")
        report_parts.append("## Code & Tools\n")
        report_parts.append(code_resources)

    # References
    report_parts.append("\n---\n")
    report_parts.append("## References\n")
    for paper in papers:
        num = paper.get("_cite_num", "?")
        title = paper.get("title", "Unknown")
        authors = paper.get("authors", [])
        year = paper.get("year") or paper.get("published", "")[:4] or ""
        author_str = ", ".join(authors[:3])
        if len(authors) > 3:
            author_str += " et al."
        venue = paper.get("venue", "")
        venue_str = f" {venue}." if venue else ""
        url = paper.get("url", "")
        url_str = f" {url}" if url else ""
        report_parts.append(f"[{num}] {author_str}. \"{title}\". {year}.{venue_str}{url_str}\n")

    report_text = "\n".join(report_parts)

    # Write report
    with open(report_path, "w") as f:
        f.write(report_text)
    print(f"Report written to {report_path} ({len(report_text)} chars)", file=sys.stderr)

    # Write BibTeX
    bib_entries = []
    for paper in papers:
        cite_key = paper.get("_cite_key", make_cite_key(paper))
        bib_entries.append(paper_to_bibtex(paper, cite_key))

    with open(bib_path, "w") as f:
        f.write("\n\n".join(bib_entries) + "\n")
    print(f"BibTeX written to {bib_path} ({len(bib_entries)} entries)", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(description="Compile research notes into a report")
    parser.add_argument("--topic-dir", required=True, help="Topic output directory")
    args = parser.parse_args()

    if not os.path.isdir(args.topic_dir):
        print(f"Error: {args.topic_dir} is not a directory", file=sys.stderr)
        sys.exit(1)

    compile_report(args.topic_dir)


if __name__ == "__main__":
    main()
