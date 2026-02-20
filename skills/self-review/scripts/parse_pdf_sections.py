#!/usr/bin/env python3
"""Parse PDF papers into structured sections using font analysis.

Extracts title (via largest font detection), section headings, and
section text from academic PDF papers.

Requires: PyMuPDF (pip install pymupdf)

Usage:
    python parse_pdf_sections.py --pdf paper.pdf --output sections.json
    python parse_pdf_sections.py --pdf paper.pdf --format text
    python parse_pdf_sections.py --pdf paper.pdf --output sections.json --verbose
"""

import argparse
import json
import os
import re
import sys
from collections import Counter

try:
    import fitz  # PyMuPDF
except ImportError:
    print("Error: PyMuPDF required. Install: pip install pymupdf", file=sys.stderr)
    sys.exit(1)


def get_title(doc) -> tuple[str, int]:
    """Extract paper title by finding the largest font text on early pages.

    Returns (title_string, title_page_index).
    """
    max_font_sizes = []
    for page_index, page in enumerate(doc):
        if page_index > 2:
            break
        text = page.get_text("dict")
        for block in text.get("blocks", []):
            if block.get("type") == 0 and block.get("lines"):
                for line in block["lines"]:
                    for span in line.get("spans", []):
                        max_font_sizes.append(span.get("size", 0))

    if not max_font_sizes:
        return "", 0

    max_font_sizes.sort()
    top_sizes = max_font_sizes[-2:] if len(max_font_sizes) >= 2 else max_font_sizes[-1:]

    title_parts = []
    title_page = 0
    for page_index, page in enumerate(doc):
        if page_index > 2:
            break
        text = page.get_text("dict")
        for block in text.get("blocks", []):
            if block.get("type") != 0 or not block.get("lines"):
                continue
            for line in block["lines"]:
                for span in line.get("spans", []):
                    font_size = span.get("size", 0)
                    cur_text = span.get("text", "").strip()
                    if any(abs(font_size - ts) < 0.3 for ts in top_sizes):
                        if len(cur_text) > 4 and "arXiv" not in cur_text:
                            title_parts.append(cur_text)
                            title_page = page_index

    title = " ".join(title_parts).replace("\n", " ").strip()
    return title, title_page


def get_font_size_threshold(doc) -> float:
    """Determine the most common font size (body text) as threshold."""
    font_sizes = []
    for page in doc:
        blocks = page.get_text("dict").get("blocks", [])
        for block in blocks:
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    font_sizes.append(span.get("size", 0))
    if not font_sizes:
        return 10.0
    most_common, _ = Counter(font_sizes).most_common(1)[0]
    return most_common


def extract_sections(doc, threshold: float) -> list[dict]:
    """Extract sections from the PDF using font-based heading detection.

    Uses two strategies:
    1. ALL-CAPS headings (common in IEEE/ACM style)
    2. Larger-font headings (common in NeurIPS/ICML style)
    """
    sections = []
    current_heading = None
    current_text = []
    current_page = 0
    heading_font = -1
    found_abstract = False
    upper_heading = False
    font_heading = False

    roman_nums = {"I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X"}
    digit_nums = {str(d) for d in range(1, 11)}

    for page_index, page in enumerate(doc):
        blocks = page.get_text("dict").get("blocks", [])
        for block in blocks:
            if not found_abstract:
                try:
                    block_text = json.dumps(block)
                except (TypeError, ValueError):
                    continue
                if re.search(r"\bAbstract\b", block_text, re.IGNORECASE):
                    found_abstract = True
                    current_heading = "Abstract"
                    current_page = page_index

            if not found_abstract:
                continue

            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    text = span.get("text", "").strip()
                    size = span.get("size", 0)

                    if not text:
                        continue

                    is_upper_heading = (
                        not font_heading
                        and text.isupper()
                        and sum(1 for c in text if c.isupper() and 'A' <= c <= 'Z') > 4
                    )

                    is_font_heading = (
                        not upper_heading
                        and size > threshold
                        and re.match(r"[0-9]*\.* *[A-Z][a-z]+(?:\s[A-Z][a-z]+)*", text)
                    )

                    if is_upper_heading:
                        upper_heading = True
                        if "References" in text or "REFERENCES" in text:
                            if current_heading:
                                sections.append({
                                    "name": current_heading,
                                    "text": " ".join(current_text).strip(),
                                    "page": current_page + 1,
                                })
                            return sections

                        if current_heading:
                            sections.append({
                                "name": current_heading,
                                "text": " ".join(current_text).strip(),
                                "page": current_page + 1,
                            })
                        current_heading = text
                        current_text = []
                        current_page = page_index

                    elif is_font_heading:
                        font_heading = True
                        if heading_font == -1:
                            heading_font = size
                        elif abs(heading_font - size) > 0.5:
                            current_text.append(text)
                            continue

                        if "References" in text:
                            if current_heading:
                                sections.append({
                                    "name": current_heading,
                                    "text": " ".join(current_text).strip(),
                                    "page": current_page + 1,
                                })
                            return sections

                        if current_heading:
                            sections.append({
                                "name": current_heading,
                                "text": " ".join(current_text).strip(),
                                "page": current_page + 1,
                            })
                        current_heading = text
                        current_text = []
                        current_page = page_index

                    elif current_heading is not None:
                        current_text.append(text)

    # Flush last section
    if current_heading:
        sections.append({
            "name": current_heading,
            "text": " ".join(current_text).strip(),
            "page": current_page + 1,
        })

    return sections


def parse_pdf(pdf_path: str, verbose: bool = False) -> dict:
    """Parse a PDF paper into structured sections.

    Returns: {title: str, pages: int, sections: [{name, text, page}]}
    """
    doc = fitz.open(pdf_path)
    title, title_page = get_title(doc)
    threshold = get_font_size_threshold(doc)

    if verbose:
        print(f"Title: {title}", file=sys.stderr)
        print(f"Body font size threshold: {threshold:.1f}", file=sys.stderr)
        print(f"Total pages: {len(doc)}", file=sys.stderr)

    sections = extract_sections(doc, threshold)
    num_pages = len(doc)
    doc.close()

    return {
        "title": title,
        "pages": num_pages,
        "sections": sections,
    }


def main():
    parser = argparse.ArgumentParser(description="Parse PDF papers into structured sections")
    parser.add_argument("--pdf", required=True, help="Input PDF file")
    parser.add_argument("--output", "-o", help="Output JSON file (default: stdout)")
    parser.add_argument("--format", choices=["json", "text"], default="json",
                        help="Output format (default: json)")
    parser.add_argument("--verbose", action="store_true", help="Print progress info")
    args = parser.parse_args()

    if not os.path.exists(args.pdf):
        print(f"Error: {args.pdf} not found", file=sys.stderr)
        sys.exit(1)

    result = parse_pdf(args.pdf, verbose=args.verbose)

    if args.format == "text":
        output = f"# {result['title']}\n\n"
        for sec in result["sections"]:
            output += f"## {sec['name']} (page {sec['page']})\n\n"
            output += sec["text"] + "\n\n"
    else:
        output = json.dumps(result, indent=2, ensure_ascii=False)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"Parsed {len(result['sections'])} sections to {args.output}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
