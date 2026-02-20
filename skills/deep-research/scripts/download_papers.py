#!/usr/bin/env python3
"""Download PDFs from a JSONL paper database.

Self-contained: uses only stdlib (urllib).

Features:
- Atomic downloads (.part file -> rename on success)
- PDF validation (checks %PDF header + %%EOF trailer)
- Respects rate limits (configurable delay)
- Skips already-downloaded papers

Usage:
    python download_papers.py --jsonl paper_db.jsonl --output-dir papers/
    python download_papers.py --jsonl paper_db.jsonl --output-dir papers/ --max-downloads 20 --delay 2.0
"""

import argparse
import json
import os
import sys
import time
import urllib.request


def sanitize_filename(arxiv_id: str, paper_id: str) -> str:
    """Create a safe filename from paper IDs."""
    name = arxiv_id or paper_id
    # Replace path separators and problematic chars
    name = name.replace("/", "_").replace("\\", "_").replace(":", "_")
    if not name.endswith(".pdf"):
        name += ".pdf"
    return name


def validate_pdf(path: str) -> bool:
    """Check that a file looks like a valid PDF."""
    try:
        with open(path, "rb") as f:
            header = f.read(5)
            if header != b"%PDF-":
                return False
            # Check for EOF marker in last 1KB
            f.seek(0, 2)
            size = f.tell()
            f.seek(max(0, size - 1024))
            tail = f.read()
            return b"%%EOF" in tail
    except Exception:
        return False


def download_pdf(url: str, dest: str, timeout: int = 60) -> bool:
    """Download a PDF with atomic write. Returns True on success."""
    part_path = dest + ".part"

    headers = {
        "User-Agent": "deep-research/1.0 (academic research tool)",
    }
    req = urllib.request.Request(url, headers=headers)

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            content_type = resp.headers.get("Content-Type", "")
            # Some servers redirect to HTML (captcha, etc.)
            if "text/html" in content_type and "pdf" not in content_type:
                print(f"  Warning: got HTML instead of PDF from {url}", file=sys.stderr)
                return False

            with open(part_path, "wb") as f:
                while True:
                    chunk = resp.read(8192)
                    if not chunk:
                        break
                    f.write(chunk)

        if not validate_pdf(part_path):
            print(f"  Warning: invalid PDF from {url}", file=sys.stderr)
            os.remove(part_path)
            return False

        os.rename(part_path, dest)
        return True

    except Exception as e:
        print(f"  Error downloading {url}: {e}", file=sys.stderr)
        if os.path.exists(part_path):
            os.remove(part_path)
        return False


def load_papers(jsonl_path: str) -> list[dict]:
    """Load papers from a JSONL file."""
    papers = []
    with open(jsonl_path) as f:
        for line in f:
            line = line.strip()
            if line:
                papers.append(json.loads(line))
    return papers


def main():
    parser = argparse.ArgumentParser(description="Download PDFs from JSONL paper database")
    parser.add_argument("--jsonl", required=True, help="JSONL file with paper records")
    parser.add_argument("--output-dir", required=True, help="Directory to save PDFs")
    parser.add_argument("--max-downloads", type=int, default=50, help="Max PDFs to download")
    parser.add_argument("--delay", type=float, default=1.0, help="Seconds between downloads")
    parser.add_argument("--timeout", type=int, default=60, help="Download timeout in seconds")
    parser.add_argument("--sort-by-citations", action="store_true", help="Download most-cited first")
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    papers = load_papers(args.jsonl)

    if args.sort_by_citations:
        papers.sort(key=lambda p: p.get("citationCount", 0) or 0, reverse=True)

    downloaded = 0
    skipped = 0
    failed = 0

    for paper in papers:
        if downloaded >= args.max_downloads:
            break

        pdf_url = paper.get("pdf_url", "")
        if not pdf_url:
            continue

        arxiv_id = paper.get("arxiv_id", "")
        paper_id = paper.get("paperId", "")
        filename = sanitize_filename(arxiv_id, paper_id)
        dest = os.path.join(args.output_dir, filename)

        if os.path.exists(dest):
            skipped += 1
            continue

        title = paper.get("title", "unknown")[:60]
        print(f"[{downloaded + 1}/{args.max_downloads}] {title}...", file=sys.stderr)

        if download_pdf(pdf_url, dest, timeout=args.timeout):
            size_mb = os.path.getsize(dest) / (1024 * 1024)
            print(f"  OK ({size_mb:.1f} MB)", file=sys.stderr)
            downloaded += 1
        else:
            failed += 1

        if downloaded < args.max_downloads:
            time.sleep(args.delay)

    print(f"\nDone: {downloaded} downloaded, {skipped} skipped, {failed} failed", file=sys.stderr)


if __name__ == "__main__":
    main()
