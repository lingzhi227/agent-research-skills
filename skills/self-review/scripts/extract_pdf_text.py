#!/usr/bin/env python3
"""Extract text from a PDF file for review.

Tries multiple extraction methods in order of quality:
1. pymupdf4llm (markdown output, best quality)
2. pymupdf/fitz (plain text)
3. pypdf (fallback)

Adapted from AI-Scientist perform_review.py load_paper().

Usage:
    python extract_pdf_text.py paper.pdf
    python extract_pdf_text.py paper.pdf --output paper_text.txt
    python extract_pdf_text.py paper.pdf --format markdown
"""

import argparse
import sys


def extract_with_pymupdf4llm(pdf_path: str) -> str | None:
    """Try pymupdf4llm for markdown extraction (best quality)."""
    try:
        import pymupdf4llm
        return pymupdf4llm.to_markdown(pdf_path)
    except ImportError:
        return None
    except Exception as e:
        print(f"pymupdf4llm failed: {e}", file=sys.stderr)
        return None


def extract_with_pymupdf(pdf_path: str) -> str | None:
    """Try pymupdf/fitz for plain text extraction."""
    try:
        import fitz
        doc = fitz.open(pdf_path)
        text_parts = []
        for page in doc:
            text_parts.append(page.get_text())
        doc.close()
        return "\n".join(text_parts)
    except ImportError:
        return None
    except Exception as e:
        print(f"pymupdf failed: {e}", file=sys.stderr)
        return None


def extract_with_pypdf(pdf_path: str) -> str | None:
    """Try pypdf for fallback text extraction."""
    try:
        from pypdf import PdfReader
        reader = PdfReader(pdf_path)
        text_parts = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                text_parts.append(text)
        return "\n".join(text_parts)
    except ImportError:
        return None
    except Exception as e:
        print(f"pypdf failed: {e}", file=sys.stderr)
        return None


def extract_text(pdf_path: str, preferred_format: str = "auto") -> str:
    """Extract text from PDF using the best available method."""
    methods = [
        ("pymupdf4llm", extract_with_pymupdf4llm),
        ("pymupdf", extract_with_pymupdf),
        ("pypdf", extract_with_pypdf),
    ]

    if preferred_format == "markdown":
        # Prefer pymupdf4llm
        methods = [methods[0], methods[1], methods[2]]
    elif preferred_format == "plain":
        # Skip pymupdf4llm
        methods = [methods[1], methods[2], methods[0]]

    for name, func in methods:
        text = func(pdf_path)
        if text and text.strip():
            print(f"Extracted using {name} ({len(text)} chars)", file=sys.stderr)
            return text

    print("ERROR: All extraction methods failed. Install one of: pymupdf4llm, pymupdf, pypdf", file=sys.stderr)
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Extract text from PDF for review")
    parser.add_argument("pdf_file", help="Path to PDF file")
    parser.add_argument("--output", "-o", help="Output text file (default: stdout)")
    parser.add_argument("--format", choices=["auto", "markdown", "plain"],
                        default="auto", help="Preferred output format")
    args = parser.parse_args()

    text = extract_text(args.pdf_file, args.format)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"Written to {args.output} ({len(text)} chars)", file=sys.stderr)
    else:
        print(text)


if __name__ == "__main__":
    main()
