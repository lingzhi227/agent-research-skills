#!/usr/bin/env python3
"""Search CrossRef API for academic papers and generate BibTeX entries.

Queries the CrossRef works API, maps document types to BibTeX types,
and generates clean BibTeX entries with proper key formatting.

Self-contained: uses only stdlib. Replaces unidecode with unicodedata.normalize().

Usage:
    python search_crossref.py --query "attention is all you need" --rows 5
    python search_crossref.py --query "transformer architecture" --rows 10 --output results.jsonl
    python search_crossref.py --query "diffusion models" --rows 3 --bibtex --output refs.bib
"""

import argparse
import json
import re
import sys
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
import time

CROSSREF_URL = "https://api.crossref.org/works"
HEADERS = {"User-Agent": "SkillScript/1.0 (mailto:user@example.com)"}

TYPE_MAPPING = {
    "journal-article": "article",
    "proceedings-article": "inproceedings",
    "book-chapter": "incollection",
    "book": "book",
    "posted-content": "misc",
    "report": "techreport",
    "dissertation": "phdthesis",
    "dataset": "misc",
    "monograph": "book",
}

BIBTEX_FIELDS = {
    "article": ["author", "title", "journal", "year", "volume", "number", "pages", "doi"],
    "inproceedings": ["author", "title", "booktitle", "year", "pages", "doi"],
    "incollection": ["author", "title", "booktitle", "year", "pages", "doi"],
    "book": ["author", "title", "publisher", "year", "doi"],
    "misc": ["author", "title", "year", "doi", "howpublished"],
    "techreport": ["author", "title", "institution", "year"],
    "phdthesis": ["author", "title", "school", "year"],
}

COMMON_WORDS = {
    "a", "an", "the", "of", "in", "on", "at", "to", "for", "and", "or",
    "is", "are", "was", "were", "be", "been", "with", "from", "by", "as",
    "its", "it", "this", "that", "via", "using", "through", "between",
}

FORBIDDEN_IDS = {
    "none", "introduction", "references", "abstract", "conclusion",
    "method", "methods", "results", "discussion", "appendix",
}


def normalize_text(text: str) -> str:
    """Remove diacritics and normalize unicode to ASCII-safe text."""
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def clean_bibtex_id(text: str) -> str:
    """Remove special characters from a BibTeX ID component."""
    return re.sub(r"[^a-zA-Z0-9]", "", normalize_text(text))


def make_bibtex_key(item: dict) -> str | None:
    """Generate a BibTeX key like 'vaswani2017attention' from CrossRef item."""
    authors = item.get("author", [])
    title = item.get("title", [""])[0] if item.get("title") else ""
    year = ""
    if item.get("published-print"):
        parts = item["published-print"].get("date-parts", [[]])
        if parts and parts[0]:
            year = str(parts[0][0])
    elif item.get("published-online"):
        parts = item["published-online"].get("date-parts", [[]])
        if parts and parts[0]:
            year = str(parts[0][0])
    elif item.get("created"):
        parts = item["created"].get("date-parts", [[]])
        if parts and parts[0]:
            year = str(parts[0][0])

    if not title:
        return None

    family = ""
    if authors:
        family = clean_bibtex_id(authors[0].get("family", ""))

    title_words = re.findall(r"[A-Za-z]+", normalize_text(title))
    content_words = [w.lower() for w in title_words if w.lower() not in COMMON_WORDS]
    title_part = content_words[0] if content_words else ""

    key = family + year + title_part
    if not key or key.lower() in FORBIDDEN_IDS:
        doi = item.get("DOI", "")
        key = "ref" + clean_bibtex_id(doi)[-12:] if doi else None

    return key


def format_authors(authors: list[dict]) -> str:
    """Format CrossRef author list as BibTeX author string."""
    parts = []
    for a in authors:
        given = a.get("given", "")
        family = a.get("family", "")
        if family and given:
            parts.append(f"{normalize_text(family)}, {normalize_text(given)}")
        elif family:
            parts.append(normalize_text(family))
    return " and ".join(parts)


def extract_year(item: dict) -> str:
    """Extract publication year from CrossRef item."""
    for field in ["published-print", "published-online", "created"]:
        if item.get(field):
            parts = item[field].get("date-parts", [[]])
            if parts and parts[0]:
                return str(parts[0][0])
    return ""


def item_to_record(item: dict) -> dict:
    """Convert a CrossRef API item to a flat record dict."""
    title = item.get("title", [""])[0] if item.get("title") else ""
    authors = format_authors(item.get("author", []))
    year = extract_year(item)
    journal = ""
    for cn in item.get("container-title", []):
        journal = cn
        break
    doi = item.get("DOI", "")
    abstract = item.get("abstract", "")
    # Strip HTML tags from abstract
    abstract = re.sub(r"<[^>]+>", "", abstract)
    score = item.get("score", 0)
    cited_by = item.get("is-referenced-by-count", 0)
    bib_type = TYPE_MAPPING.get(item.get("type", ""), "misc")

    return {
        "title": title,
        "authors": authors,
        "year": year,
        "journal": journal,
        "doi": doi,
        "abstract": abstract,
        "type": bib_type,
        "score": score,
        "cited_by": cited_by,
        "volume": item.get("volume", ""),
        "issue": item.get("issue", ""),
        "pages": item.get("page", ""),
        "publisher": item.get("publisher", ""),
        "booktitle": journal,
    }


def record_to_bibtex(record: dict, key: str) -> str:
    """Format a record dict as a BibTeX entry string."""
    bib_type = record.get("type", "misc")
    fields = BIBTEX_FIELDS.get(bib_type, BIBTEX_FIELDS["misc"])
    lines = [f"@{bib_type}{{{key},"]
    for field in fields:
        val = record.get(field, "")
        if field == "journal":
            val = record.get("journal", "")
        elif field == "number":
            val = record.get("issue", "")
        if val:
            lines.append(f"  {field} = {{{val}}},")
    lines.append("}")
    return "\n".join(lines)


def query_crossref(query: str, rows: int = 10, timeout: int = 30) -> list[dict]:
    """Query CrossRef API and return raw items."""
    params = urllib.parse.urlencode({"query": query, "rows": rows})
    url = f"{CROSSREF_URL}?{params}"
    req = urllib.request.Request(url, headers=HEADERS)

    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            return data.get("message", {}).get("items", [])
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
            if attempt < 2:
                time.sleep(2 ** attempt)
            else:
                print(f"CrossRef API error after 3 attempts: {e}", file=sys.stderr)
                return []


def main():
    parser = argparse.ArgumentParser(description="Search CrossRef for academic papers")
    parser.add_argument("--query", required=True, help="Search query")
    parser.add_argument("--rows", type=int, default=10, help="Number of results (default: 10)")
    parser.add_argument("--output", "-o", help="Output file (.jsonl or .bib)")
    parser.add_argument("--bibtex", action="store_true", help="Output BibTeX format")
    parser.add_argument("--timeout", type=int, default=30, help="Request timeout in seconds")
    args = parser.parse_args()

    items = query_crossref(args.query, rows=args.rows, timeout=args.timeout)
    if not items:
        print("No results found.", file=sys.stderr)
        sys.exit(1)

    records = []
    used_keys = set()
    for item in items:
        record = item_to_record(item)
        key = make_bibtex_key(item)
        if key is None:
            continue
        # Deduplicate keys
        orig_key = key
        suffix_idx = 0
        while key in used_keys:
            suffix_idx += 1
            key = orig_key + chr(ord("a") + suffix_idx - 1)
        used_keys.add(key)
        record["bibtex_key"] = key
        records.append(record)

    is_bibtex = args.bibtex or (args.output and args.output.endswith(".bib"))

    output_lines = []
    if is_bibtex:
        for r in records:
            output_lines.append(record_to_bibtex(r, r["bibtex_key"]))
            output_lines.append("")
    else:
        for r in records:
            output_lines.append(json.dumps(r, ensure_ascii=False))

    text = "\n".join(output_lines) + "\n" if output_lines else ""

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"Wrote {len(records)} results to {args.output}", file=sys.stderr)
    else:
        sys.stdout.write(text)

    print(f"Found {len(records)} results for: {args.query}", file=sys.stderr)


if __name__ == "__main__":
    main()
