#!/usr/bin/env python3
"""Extract GitHub URLs, paper refs, and keywords from deep-research output.

Scans markdown files for GitHub URLs (cleaning sub-paths to extract owner/name),
parses paper_db.jsonl for paper metadata, extracts keywords from titles and tags,
and outputs deduplicated JSONL records.

Usage:
    python extract_research_refs.py --research-dir ./deep-research-output/topic/ --output refs.jsonl
"""

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

GITHUB_URL_RE = re.compile(r'https://github\.com/[^\s\)\]\>\"\']+')

# Sub-paths to strip to get base repo URL
REPO_SUBPATH_RE = re.compile(
    r"/(?:tree|blob|issues|pull|releases|wiki|actions|commits|compare|archive|raw|discussions|pkgs|packages|security|stargazers|network)(?:/.*)?$"
)

# Non-repo top-level GitHub pages
NON_REPO_OWNERS = frozenset({
    "topics", "explore", "trending", "settings",
    "organizations", "sponsors", "features", "marketplace",
    "notifications", "new", "login", "signup", "pricing",
})

# Common English stopwords for keyword filtering
STOPWORDS = frozenset({
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "is", "are", "was", "were", "be", "been",
    "being", "have", "has", "had", "do", "does", "did", "will", "would",
    "could", "should", "may", "might", "can", "shall", "not", "no", "nor",
    "so", "if", "then", "than", "that", "this", "these", "those", "it",
    "its", "we", "our", "they", "their", "them", "you", "your", "he",
    "she", "his", "her", "as", "up", "out", "about", "into", "over",
    "after", "before", "between", "through", "during", "each", "every",
    "all", "both", "few", "more", "most", "other", "some", "such", "only",
    "same", "also", "how", "what", "which", "who", "when", "where", "why",
    "very", "just", "because", "while", "using", "via", "based", "new",
    "one", "two", "first", "use", "used", "paper", "method", "approach",
    "proposed", "show", "results", "model", "models",
})


def clean_github_url(raw_url: str) -> tuple[str, str]:
    """Clean a raw GitHub URL and extract owner/name repo_id.

    Returns (clean_url, repo_id) or ("", "") if invalid.
    """
    url = raw_url.rstrip(".,;:!?)]\">'/")
    url = url.rstrip("/")

    # Remove sub-paths (tree, blob, issues, etc.) to get base repo URL
    url = REPO_SUBPATH_RE.sub("", url)

    # Extract owner/name
    path = url.replace("https://github.com/", "")
    parts = path.split("/")
    if len(parts) >= 2 and parts[0] and parts[1]:
        owner, name = parts[0], parts[1]
        # Filter out non-repo pages
        if owner.lower() in NON_REPO_OWNERS:
            return "", ""
        # Strip .git suffix
        name = name.removesuffix(".git")
        repo_id = f"{owner}/{name}"
        clean_url = f"https://github.com/{repo_id}"
        return clean_url, repo_id
    return "", ""


def scan_md_files_for_urls(research_dir: Path) -> list[dict]:
    """Scan all .md files recursively for GitHub URLs."""
    results: list[dict] = []
    seen_repos: set[str] = set()

    for md_file in sorted(research_dir.rglob("*.md")):
        try:
            text = md_file.read_text(encoding="utf-8", errors="replace")
        except OSError as e:
            print(f"[warn] cannot read {md_file}: {e}", file=sys.stderr)
            continue

        rel_path = str(md_file.relative_to(research_dir))

        for match in GITHUB_URL_RE.finditer(text):
            raw_url = match.group(0)
            clean_url, repo_id = clean_github_url(raw_url)
            if not repo_id:
                continue

            # Extract surrounding context (the line containing the URL)
            line_start = text.rfind("\n", 0, match.start()) + 1
            line_end = text.find("\n", match.end())
            if line_end == -1:
                line_end = len(text)
            context = text[line_start:line_end].strip()

            # Deduplicate by repo_id (not raw URL) to merge /tree/... variants
            if repo_id in seen_repos:
                continue
            seen_repos.add(repo_id)

            results.append({
                "type": "github_url",
                "url": clean_url,
                "repo_id": repo_id,
                "source_file": rel_path,
                "context": context[:200],
            })

    return results


def parse_paper_db(research_dir: Path) -> list[dict]:
    """Parse paper_db.jsonl for paper titles, arxiv IDs, tags."""
    results: list[dict] = []
    paper_db = research_dir / "paper_db.jsonl"
    if not paper_db.exists():
        print("[info] paper_db.jsonl not found, skipping paper extraction", file=sys.stderr)
        return results

    try:
        for line_num, line in enumerate(paper_db.read_text(encoding="utf-8").splitlines(), 1):
            line = line.strip()
            if not line:
                continue
            try:
                paper = json.loads(line)
            except json.JSONDecodeError as e:
                print(f"[warn] paper_db.jsonl line {line_num}: {e}", file=sys.stderr)
                continue

            title = paper.get("title", "")
            arxiv_id = paper.get("arxiv_id", paper.get("id", ""))
            tags = paper.get("tags", paper.get("keywords", paper.get("categories", [])))
            paper_id = paper.get("paperId", arxiv_id)

            results.append({
                "type": "paper",
                "title": title,
                "arxiv_id": arxiv_id,
                "tags": tags if isinstance(tags, list) else [],
                "paper_id": paper_id,
            })
    except OSError as e:
        print(f"[warn] cannot read paper_db.jsonl: {e}", file=sys.stderr)

    return results


def extract_keywords(papers: list[dict]) -> list[dict]:
    """Extract search keywords from paper titles and tags."""
    tag_counter: Counter[str] = Counter()
    title_term_counter: Counter[str] = Counter()

    for paper in papers:
        # Count tags
        for tag in paper.get("tags", []):
            if isinstance(tag, str):
                tag_lower = tag.strip().lower()
                if tag_lower and len(tag_lower) > 2:
                    tag_counter[tag_lower] += 1

        # Extract terms from titles
        title = paper.get("title", "")
        if not title:
            continue
        words = re.findall(r"[A-Za-z][-A-Za-z]+", title)
        filtered = [w.lower() for w in words
                     if w.lower() not in STOPWORDS and len(w) > 2]

        # Unigrams
        for w in filtered:
            title_term_counter[w] += 1

        # Bigrams (multi-word technical terms)
        for i in range(len(filtered) - 1):
            bigram = f"{filtered[i]} {filtered[i + 1]}"
            title_term_counter[bigram] += 1

    keywords: list[dict] = []

    # Tags with frequency
    for tag, freq in tag_counter.most_common():
        keywords.append({
            "type": "keyword",
            "value": tag,
            "frequency": freq,
            "source": "paper_tags",
        })

    # Title terms (2+ occurrences, or bigrams with 1+ occurrence)
    for term, freq in title_term_counter.most_common():
        if freq >= 2 or (freq >= 1 and " " in term):
            # Skip if already covered by tags
            if term not in tag_counter:
                keywords.append({
                    "type": "keyword",
                    "value": term,
                    "frequency": freq,
                    "source": "paper_titles",
                })

    return keywords


def extract_synthesis_themes(research_dir: Path) -> list[dict]:
    """Extract research themes from synthesis/report markdown headings."""
    results: list[dict] = []

    # Check several possible locations for synthesis/report files
    candidates = [
        research_dir / "phase5_synthesis" / "synthesis.md",
        research_dir / "phase6_report" / "report.md",
        research_dir / "phase3_deep_dive" / "deep_dive.md",
    ]

    for filepath in candidates:
        if not filepath.exists():
            continue
        try:
            text = filepath.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        for match in re.finditer(r'^#{1,3}\s+(.+)$', text, re.MULTILINE):
            heading = match.group(1).strip()
            if len(heading) > 3:
                results.append({
                    "type": "keyword",
                    "value": heading.lower(),
                    "frequency": 1,
                    "source": "paper_titles",
                })

    return results


def main():
    parser = argparse.ArgumentParser(
        description="Extract GitHub URLs, paper refs, and keywords from deep-research output."
    )
    parser.add_argument("--research-dir", required=True,
                        help="Path to deep-research output directory")
    parser.add_argument("--output", required=True,
                        help="Output JSONL file path")
    args = parser.parse_args()

    research_dir = Path(args.research_dir).resolve()
    if not research_dir.is_dir():
        print(f"[error] research dir not found: {research_dir}", file=sys.stderr)
        sys.exit(1)

    print(f"[info] scanning {research_dir} ...", file=sys.stderr)

    # 1. Extract GitHub URLs from all markdown files
    github_refs = scan_md_files_for_urls(research_dir)
    print(f"  GitHub URLs: {len(github_refs)}", file=sys.stderr)

    # 2. Parse paper_db.jsonl
    papers = parse_paper_db(research_dir)
    print(f"  Papers: {len(papers)}", file=sys.stderr)

    # 3. Extract keywords from papers
    keywords = extract_keywords(papers)

    # 4. Extract themes from synthesis/report headings
    themes = extract_synthesis_themes(research_dir)
    keywords.extend(themes)

    # Deduplicate keywords by value
    seen_kw: set[str] = set()
    deduped_kw: list[dict] = []
    for kw in keywords:
        if kw["value"] not in seen_kw:
            seen_kw.add(kw["value"])
            deduped_kw.append(kw)
    keywords = deduped_kw

    print(f"  Keywords: {len(keywords)}", file=sys.stderr)

    # Write output
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        for record in github_refs:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
        for record in papers:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
        for record in keywords:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    # Summary stats
    unique_repos = len({r["repo_id"] for r in github_refs})
    print(
        f"Extracted {unique_repos} GitHub URLs, "
        f"{len(papers)} papers, {len(keywords)} keywords "
        f"-> {output_path}",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
