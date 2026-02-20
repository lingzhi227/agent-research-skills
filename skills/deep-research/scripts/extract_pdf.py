#!/usr/bin/env python3
"""Extract text from PDFs using PyMuPDF (fitz).

Features:
- Full text extraction with layout preservation
- Section detection (Abstract, Introduction, Methods, etc.)
- Batch mode for entire directories
- BibTeX-style reference extraction

Usage:
    python extract_pdf.py --pdf paper.pdf
    python extract_pdf.py --pdf-dir papers/ --output-dir texts/
    python extract_pdf.py --pdf paper.pdf --sections-only
"""

import argparse
import os
import re
import sys

try:
    import fitz  # PyMuPDF
except ImportError:
    print("Error: PyMuPDF not installed. Run: pip install PyMuPDF", file=sys.stderr)
    sys.exit(1)


SECTION_PATTERNS = [
    (r"^\s*abstract\s*$", "Abstract"),
    (r"^\s*\d*\.?\s*introduction\s*$", "Introduction"),
    (r"^\s*\d*\.?\s*related\s+work", "Related Work"),
    (r"^\s*\d*\.?\s*background", "Background"),
    (r"^\s*\d*\.?\s*method(?:s|ology)?", "Methods"),
    (r"^\s*\d*\.?\s*(?:proposed\s+)?(?:approach|framework|model|system)", "Methods"),
    (r"^\s*\d*\.?\s*experiment(?:s|al)?(?:\s+(?:setup|results))?", "Experiments"),
    (r"^\s*\d*\.?\s*results?(?:\s+and\s+(?:discussion|analysis))?", "Results"),
    (r"^\s*\d*\.?\s*evaluation", "Evaluation"),
    (r"^\s*\d*\.?\s*discussion", "Discussion"),
    (r"^\s*\d*\.?\s*(?:conclusion|concluding)", "Conclusion"),
    (r"^\s*\d*\.?\s*limitation", "Limitations"),
    (r"^\s*\d*\.?\s*(?:future\s+work|outlook)", "Future Work"),
    (r"^\s*\d*\.?\s*(?:acknowledge?ment)", "Acknowledgements"),
    (r"^\s*\d*\.?\s*references?\s*$", "References"),
    (r"^\s*\d*\.?\s*(?:appendix|supplementary)", "Appendix"),
]


def extract_text(pdf_path: str) -> str:
    """Extract full text from a PDF file."""
    doc = fitz.open(pdf_path)
    pages = []
    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text("text")
        if text.strip():
            pages.append(text)
    doc.close()
    return "\n\n".join(pages)


def detect_sections(text: str) -> list[tuple[str, str]]:
    """Detect sections in extracted text. Returns list of (section_name, content)."""
    lines = text.split("\n")
    sections = []
    current_section = "Preamble"
    current_lines = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            current_lines.append("")
            continue

        matched = False
        # Check if this line is a section header
        # Heuristic: short line (< 80 chars) matching a known pattern
        if len(stripped) < 80:
            for pattern, section_name in SECTION_PATTERNS:
                if re.match(pattern, stripped, re.IGNORECASE):
                    # Save previous section
                    if current_lines:
                        content = "\n".join(current_lines).strip()
                        if content:
                            sections.append((current_section, content))
                    current_section = section_name
                    current_lines = []
                    matched = True
                    break

        if not matched:
            current_lines.append(line)

    # Don't forget the last section
    if current_lines:
        content = "\n".join(current_lines).strip()
        if content:
            sections.append((current_section, content))

    return sections


def extract_with_sections(pdf_path: str) -> dict:
    """Extract text and identify sections."""
    text = extract_text(pdf_path)
    sections = detect_sections(text)
    return {
        "full_text": text,
        "sections": {name: content for name, content in sections},
        "section_order": [name for name, _ in sections],
    }


def format_sections(result: dict, sections_only: bool = False) -> str:
    """Format extracted text with section markers."""
    if sections_only:
        output = []
        for name in result["section_order"]:
            content = result["sections"].get(name, "")
            output.append(f"## {name}\n\n{content}")
        return "\n\n---\n\n".join(output)
    else:
        return result["full_text"]


def process_directory(pdf_dir: str, output_dir: str, sections_only: bool = False):
    """Process all PDFs in a directory."""
    os.makedirs(output_dir, exist_ok=True)
    pdf_files = sorted(f for f in os.listdir(pdf_dir) if f.lower().endswith(".pdf"))

    for i, filename in enumerate(pdf_files, 1):
        pdf_path = os.path.join(pdf_dir, filename)
        txt_name = os.path.splitext(filename)[0] + ".txt"
        txt_path = os.path.join(output_dir, txt_name)

        print(f"[{i}/{len(pdf_files)}] {filename}...", file=sys.stderr)

        try:
            result = extract_with_sections(pdf_path)
            text = format_sections(result, sections_only)
            with open(txt_path, "w") as f:
                f.write(text)
            print(f"  OK ({len(text)} chars)", file=sys.stderr)
        except Exception as e:
            print(f"  Error: {e}", file=sys.stderr)

    print(f"\nProcessed {len(pdf_files)} PDFs", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(description="Extract text from PDFs using PyMuPDF")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--pdf", help="Single PDF file to extract")
    group.add_argument("--pdf-dir", help="Directory of PDFs to process")
    parser.add_argument("--output-dir", help="Output directory for batch mode")
    parser.add_argument("--sections-only", action="store_true", help="Output only detected sections")
    args = parser.parse_args()

    if args.pdf:
        result = extract_with_sections(args.pdf)
        print(format_sections(result, args.sections_only))
    elif args.pdf_dir:
        if not args.output_dir:
            print("Error: --output-dir required with --pdf-dir", file=sys.stderr)
            sys.exit(1)
        process_directory(args.pdf_dir, args.output_dir, args.sections_only)


if __name__ == "__main__":
    main()
