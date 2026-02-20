#!/usr/bin/env python3
"""Download arXiv paper source by title, extract .tex content.

Searches the arXiv API by title, downloads the source tarball,
and extracts .tex files into a local directory.

Self-contained: uses only stdlib (urllib + xml.etree instead of feedparser).

Usage:
    python download_arxiv_source.py --title "Attention Is All You Need" --output-dir arxiv_papers/
    python download_arxiv_source.py --title "BERT" --max-results 3 --output-dir arxiv_papers/
    python download_arxiv_source.py --arxiv-id 1706.03762 --output-dir arxiv_papers/
"""

import argparse
import json
import os
import re
import sys
import tarfile
import tempfile
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

ARXIV_API = "http://export.arxiv.org/api/query"
ARXIV_NS = {"atom": "http://www.w3.org/2005/Atom"}


def search_arxiv(query: str, max_results: int = 5, search_field: str = "ti") -> list[dict]:
    """Search arXiv API and return paper metadata."""
    params = urllib.parse.urlencode({
        "search_query": f"{search_field}:{urllib.parse.quote(query)}",
        "start": 0,
        "max_results": max_results,
        "sortBy": "relevance",
        "sortOrder": "descending",
    })
    url = f"{ARXIV_API}?{params}"

    try:
        with urllib.request.urlopen(url, timeout=30) as resp:
            xml_data = resp.read()
    except Exception as e:
        print(f"arXiv API error: {e}", file=sys.stderr)
        return []

    root = ET.fromstring(xml_data)
    papers = []
    for entry in root.findall("atom:entry", ARXIV_NS):
        title_el = entry.find("atom:title", ARXIV_NS)
        title = title_el.text.strip().replace("\n", " ") if title_el is not None else ""

        summary_el = entry.find("atom:summary", ARXIV_NS)
        summary = summary_el.text.strip() if summary_el is not None else ""

        authors = []
        for author in entry.findall("atom:author", ARXIV_NS):
            name_el = author.find("atom:name", ARXIV_NS)
            if name_el is not None:
                authors.append(name_el.text)

        published_el = entry.find("atom:published", ARXIV_NS)
        published = published_el.text if published_el is not None else ""

        abs_link = ""
        pdf_link = ""
        for link in entry.findall("atom:link", ARXIV_NS):
            href = link.get("href", "")
            link_type = link.get("type", "")
            rel = link.get("rel", "")
            if link_type == "application/pdf":
                pdf_link = href
            elif rel == "alternate":
                abs_link = href

        arxiv_id = ""
        id_el = entry.find("atom:id", ARXIV_NS)
        if id_el is not None:
            m = re.search(r"abs/(.+)", id_el.text)
            if m:
                arxiv_id = m.group(1)

        papers.append({
            "title": title,
            "authors": authors,
            "published": published,
            "summary": summary,
            "abs_link": abs_link,
            "pdf_link": pdf_link,
            "arxiv_id": arxiv_id,
        })

    return papers


def download_source(arxiv_id: str, output_dir: str) -> str | None:
    """Download arXiv source tarball and extract .tex files.

    Returns the path to the extracted content or None on failure.
    """
    # Strip version suffix for source download
    base_id = re.sub(r"v\d+$", "", arxiv_id)
    source_url = f"https://arxiv.org/src/{base_id}"

    safe_name = re.sub(r"[^a-zA-Z0-9._-]", "_", arxiv_id)
    os.makedirs(output_dir, exist_ok=True)

    try:
        req = urllib.request.Request(source_url, headers={"User-Agent": "SkillScript/1.0"})
        with urllib.request.urlopen(req, timeout=60) as resp:
            tar_data = resp.read()
    except Exception as e:
        print(f"Download failed for {arxiv_id}: {e}", file=sys.stderr)
        return None

    # Save tarball to temp file, then extract
    with tempfile.NamedTemporaryFile(suffix=".tar.gz", delete=False) as tmp:
        tmp.write(tar_data)
        tmp_path = tmp.name

    tex_contents = []
    try:
        with tarfile.open(tmp_path, "r:gz") as tar:
            tex_files = [m for m in tar.getmembers() if m.name.endswith(".tex")]
            for tex_file in tex_files:
                f = tar.extractfile(tex_file)
                if f is not None:
                    try:
                        content = f.read().decode("utf-8")
                    except UnicodeDecodeError:
                        f.seek(0)
                        content = f.read().decode("latin-1")
                    tex_contents.append((tex_file.name, content))
    except (tarfile.TarError, Exception) as e:
        print(f"Extraction failed for {arxiv_id}: {e}", file=sys.stderr)
        return None
    finally:
        os.unlink(tmp_path)

    if not tex_contents:
        print(f"No .tex files found in source for {arxiv_id}", file=sys.stderr)
        return None

    # Find main tex file (contains \documentclass or largest file)
    main_file = None
    for name, content in tex_contents:
        if r"\documentclass" in content:
            main_file = (name, content)
            break
    if main_file is None:
        main_file = max(tex_contents, key=lambda x: len(x[1]))

    # Write all tex files
    out_subdir = os.path.join(output_dir, safe_name)
    os.makedirs(out_subdir, exist_ok=True)
    for name, content in tex_contents:
        safe_tex = re.sub(r"[/\\]", "_", name)
        out_path = os.path.join(out_subdir, safe_tex)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(content)

    # Also write combined file
    combined_path = os.path.join(output_dir, f"{safe_name}.tex")
    with open(combined_path, "w", encoding="utf-8") as f:
        for name, content in tex_contents:
            f.write(f"\n{'=' * 50}\n% File: {name}\n{'=' * 50}\n")
            f.write(content)
            f.write("\n\n")

    return combined_path


def main():
    parser = argparse.ArgumentParser(description="Download arXiv paper source by title")
    parser.add_argument("--title", help="Paper title to search for")
    parser.add_argument("--arxiv-id", help="Direct arXiv ID (e.g., 1706.03762)")
    parser.add_argument("--max-results", type=int, default=5, help="Max search results (default: 5)")
    parser.add_argument("--output-dir", default="arxiv_papers", help="Output directory (default: arxiv_papers/)")
    parser.add_argument("--metadata", action="store_true", help="Also output metadata JSON")
    args = parser.parse_args()

    if not args.title and not args.arxiv_id:
        print("Error: must specify --title or --arxiv-id", file=sys.stderr)
        sys.exit(1)

    if args.arxiv_id:
        print(f"Downloading source for arXiv:{args.arxiv_id}", file=sys.stderr)
        result = download_source(args.arxiv_id, args.output_dir)
        if result:
            print(f"Saved to: {result}")
        else:
            sys.exit(1)
        return

    # Search by title
    print(f"Searching arXiv for: {args.title}", file=sys.stderr)
    papers = search_arxiv(args.title, max_results=args.max_results)
    if not papers:
        print("No results found.", file=sys.stderr)
        sys.exit(1)

    print(f"Found {len(papers)} results:", file=sys.stderr)
    for i, p in enumerate(papers):
        print(f"  [{i+1}] {p['title'][:80]} ({p['arxiv_id']})", file=sys.stderr)

    if args.metadata:
        meta_path = os.path.join(args.output_dir, "metadata.json")
        os.makedirs(args.output_dir, exist_ok=True)
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(papers, f, indent=2, ensure_ascii=False)
        print(f"Metadata saved to: {meta_path}", file=sys.stderr)

    # Download first result
    paper = papers[0]
    if not paper["arxiv_id"]:
        print("No arXiv ID found for top result.", file=sys.stderr)
        sys.exit(1)

    print(f"\nDownloading source for: {paper['title'][:60]}...", file=sys.stderr)
    time.sleep(1)  # Be polite to arXiv
    result = download_source(paper["arxiv_id"], args.output_dir)
    if result:
        print(f"Saved to: {result}")
    else:
        print("Download failed.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
