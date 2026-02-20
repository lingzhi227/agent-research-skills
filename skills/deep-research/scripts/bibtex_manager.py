#!/usr/bin/env python3
"""Generate and manage BibTeX entries from JSONL paper records.

Citation keys: firstAuthorLastNameYearFirstTitleWord (e.g., vaswani2017attention).

Usage:
    python bibtex_manager.py --jsonl paper_db.jsonl --output references.bib
    python bibtex_manager.py --jsonl paper_db.jsonl  # stdout
"""

import argparse
import json
import re
import sys
import unicodedata


def normalize_name(name: str) -> str:
    """Normalize a name: strip accents, lowercase."""
    nfkd = unicodedata.normalize("NFKD", name)
    ascii_name = nfkd.encode("ascii", "ignore").decode("ascii")
    return ascii_name.strip()


def last_name(author: str) -> str:
    """Extract last name from an author string."""
    author = normalize_name(author)
    parts = author.split()
    if not parts:
        return "unknown"
    return parts[-1].lower()


def make_citation_key(paper: dict) -> str:
    """Generate a citation key: lastNameYearWord."""
    authors = paper.get("authors", [])
    first_author = last_name(authors[0]) if authors else "unknown"
    # Remove non-alphanumeric from author
    first_author = re.sub(r"[^a-z]", "", first_author)

    year = paper.get("year", "")
    if not year:
        pub = paper.get("published", "") or paper.get("publicationDate", "") or ""
        if pub and len(pub) >= 4:
            year = pub[:4]
        else:
            year = "nd"

    title = paper.get("title", "")
    skip_words = {"a", "an", "the", "on", "in", "of", "for", "to", "with", "and", "or"}
    title_words = re.findall(r"[a-z]+", title.lower())
    first_word = "paper"
    for w in title_words:
        if w not in skip_words and len(w) > 2:
            first_word = w
            break

    return f"{first_author}{year}{first_word}"


def escape_bibtex(text: str) -> str:
    """Escape special BibTeX characters."""
    text = text.replace("&", r"\&")
    text = text.replace("%", r"\%")
    text = text.replace("#", r"\#")
    text = text.replace("_", r"\_")
    return text


def format_authors_bibtex(authors: list[str]) -> str:
    """Format authors for BibTeX (Name1 and Name2 and Name3)."""
    if not authors:
        return "Unknown"
    return " and ".join(authors)


def paper_to_bibtex(paper: dict, key: str) -> str:
    """Convert a paper record to a BibTeX entry."""
    arxiv_id = paper.get("arxiv_id", "")
    venue = paper.get("venue", "")
    year = paper.get("year", "")
    if not year:
        pub = paper.get("published", "") or paper.get("publicationDate", "") or ""
        year = pub[:4] if len(pub) >= 4 else ""

    authors = format_authors_bibtex(paper.get("authors", []))
    title = paper.get("title", "")
    abstract_text = paper.get("abstract", "")

    # Determine entry type
    conf_keywords = ["conference", "proceedings", "icml", "neurips", "iclr", "acl", "emnlp", "cvpr", "aaai"]
    journal_keywords = ["journal", "transactions", "review"]

    if venue and any(kw in venue.lower() for kw in conf_keywords):
        entry_type = "inproceedings"
    elif venue and any(kw in venue.lower() for kw in journal_keywords):
        entry_type = "article"
    elif arxiv_id:
        entry_type = "article"
    else:
        entry_type = "misc"

    lines = [f"@{entry_type}{{{key},"]
    lines.append(f"  title = {{{escape_bibtex(title)}}},")
    lines.append(f"  author = {{{authors}}},")
    if year:
        lines.append(f"  year = {{{year}}},")
    if venue:
        if entry_type == "inproceedings":
            lines.append(f"  booktitle = {{{escape_bibtex(venue)}}},")
        elif entry_type == "article" and not arxiv_id:
            lines.append(f"  journal = {{{escape_bibtex(venue)}}},")
    if arxiv_id:
        lines.append(f"  eprint = {{{arxiv_id}}},")
        lines.append(f"  archivePrefix = {{arXiv}},")
        if not venue:
            lines.append(f"  journal = {{arXiv preprint arXiv:{arxiv_id}}},")
    url = paper.get("url", "")
    if url:
        lines.append(f"  url = {{{url}}},")
    if abstract_text:
        short_abstract = abstract_text[:500]
        lines.append(f"  abstract = {{{escape_bibtex(short_abstract)}}},")
    lines.append("}")

    return "\n".join(lines)


def load_jsonl(path: str) -> list[dict]:
    """Load records from a JSONL file."""
    records = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def generate_bibtex(records: list[dict]) -> str:
    """Generate BibTeX for all records, with deduplication by key."""
    entries = {}
    for rec in records:
        key = make_citation_key(rec)
        original_key = key
        suffix_idx = 0
        while key in entries:
            suffix_idx += 1
            key = f"{original_key}{chr(96 + suffix_idx)}"  # a, b, c...
        entries[key] = paper_to_bibtex(rec, key)

    return "\n\n".join(entries.values()) + "\n"


def main():
    parser = argparse.ArgumentParser(description="Generate BibTeX from JSONL paper records")
    parser.add_argument("--jsonl", required=True, help="Input JSONL file with paper records")
    parser.add_argument("--output", "-o", help="Output .bib file (default: stdout)")
    parser.add_argument("--keys-only", action="store_true", help="Only print citation keys")
    args = parser.parse_args()

    records = load_jsonl(args.jsonl)

    if args.keys_only:
        seen = set()
        for rec in records:
            key = make_citation_key(rec)
            original_key = key
            suffix_idx = 0
            while key in seen:
                suffix_idx += 1
                key = f"{original_key}{chr(96 + suffix_idx)}"
            seen.add(key)
            title = rec.get("title", "")[:60]
            print(f"{key}\t{title}")
        return

    bibtex = generate_bibtex(records)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(bibtex)
        print(f"Written {len(records)} entries to {args.output}", file=sys.stderr)
    else:
        print(bibtex)


if __name__ == "__main__":
    main()
