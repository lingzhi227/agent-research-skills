#!/usr/bin/env python3
"""Search cloned repo for specific implementations (classes, functions, algorithms).

Usage:
    python find_implementations.py --repo-dir ./repos/owner_name --patterns "class Transformer" "def train" --output matches.jsonl
    python find_implementations.py --repo-dir ./repos/owner_name --keywords "attention" "embedding" --output matches.jsonl
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SKIP_DIRS: frozenset[str] = frozenset({
    ".git", "node_modules", "__pycache__", ".venv", "venv",
    ".tox", ".mypy_cache", ".pytest_cache", ".eggs", "dist", "build",
    ".next", ".nuxt",
})

TEST_INDICATORS: tuple[str, ...] = (
    "/test/", "/tests/", "test_", "_test.py", ".test.", ".spec.",
)

MAX_FILE_SIZE: int = 1_048_576  # 1 MB


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def is_binary(filepath: Path) -> bool:
    """Check if a file is likely binary by reading the first 8 KB."""
    try:
        with open(filepath, "rb") as f:
            chunk = f.read(8192)
            return b"\x00" in chunk
    except OSError:
        return True


def is_test_path(rel_path: str) -> bool:
    """Return True if the relative path looks like a test file."""
    rel_lower = rel_path.lower()
    for indicator in TEST_INDICATORS:
        if indicator in rel_lower:
            return True
    # Also check basename prefix
    basename = os.path.basename(rel_lower)
    if basename.startswith("test_"):
        return True
    return False


def classify_pattern(pattern: str) -> tuple[str, re.Pattern[str]]:
    """Classify a search pattern and return (match_type, compiled_regex).

    Patterns starting with "class " or "def " get special match types.
    Other patterns are compiled as-is (user-supplied regex).
    """
    if pattern.startswith("class "):
        name = pattern[6:].strip()
        return "class", re.compile(r"class\s+" + re.escape(name))
    elif pattern.startswith("def "):
        name = pattern[4:].strip()
        return "function", re.compile(r"def\s+" + re.escape(name))
    else:
        try:
            return "keyword", re.compile(pattern)
        except re.error:
            # Fall back to escaped literal if pattern is not valid regex
            return "keyword", re.compile(re.escape(pattern))


def read_lines(filepath: Path) -> list[str] | None:
    """Read all lines from a text file. Returns None on decode failure."""
    try:
        with open(filepath, "r", encoding="utf-8", errors="strict") as f:
            return f.readlines()
    except (OSError, UnicodeDecodeError):
        return None


# ---------------------------------------------------------------------------
# Search logic
# ---------------------------------------------------------------------------

def search_file(
    filepath: Path,
    rel_path: str,
    patterns: list[tuple[str, re.Pattern[str]]],
    keywords: list[str],
    context: int,
    repo_id: str,
) -> list[dict]:
    """Search a single file for patterns and keywords. Returns match dicts."""
    lines = read_lines(filepath)
    if lines is None:
        return []

    results: list[dict] = []

    # --- Pattern search (regex) ---
    for match_type, regex in patterns:
        for i, line in enumerate(lines):
            if regex.search(line):
                start = max(0, i - context)
                end = min(len(lines), i + context + 1)
                results.append({
                    "repo_id": repo_id,
                    "file_path": rel_path,
                    "line_number": i + 1,
                    "match_type": match_type,
                    "matched_text": line.rstrip("\n"),
                    "context_before": [
                        l.rstrip("\n") for l in lines[start:i]
                    ],
                    "context_after": [
                        l.rstrip("\n") for l in lines[i + 1:end]
                    ],
                })

    # --- Keyword search (case-insensitive substring) ---
    for kw in keywords:
        kw_lower = kw.lower()
        for i, line in enumerate(lines):
            if kw_lower in line.lower():
                start = max(0, i - context)
                end = min(len(lines), i + context + 1)
                results.append({
                    "repo_id": repo_id,
                    "file_path": rel_path,
                    "line_number": i + 1,
                    "match_type": "keyword",
                    "matched_text": line.rstrip("\n"),
                    "context_before": [
                        l.rstrip("\n") for l in lines[start:i]
                    ],
                    "context_after": [
                        l.rstrip("\n") for l in lines[i + 1:end]
                    ],
                })

    return results


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Search cloned repo for specific implementations "
                    "(classes, functions, algorithms)",
    )
    parser.add_argument(
        "--repo-dir", required=True,
        help="Path to the cloned repository",
    )
    parser.add_argument(
        "--patterns", nargs="+", default=None,
        help='Regex patterns (e.g. "class Transformer" "def train")',
    )
    parser.add_argument(
        "--keywords", nargs="+", default=None,
        help="Simple keyword search terms (case-insensitive substring match)",
    )
    parser.add_argument(
        "--output", required=True,
        help="Output JSONL file path",
    )
    parser.add_argument(
        "--context", type=int, default=5,
        help="Lines of context before and after each match (default: 5)",
    )
    parser.add_argument(
        "--skip-tests", action="store_true",
        help="Skip test files and test directories",
    )
    parser.add_argument(
        "--repo-id", default=None,
        help="Repository identifier (owner/name); inferred from dir name if omitted",
    )

    args = parser.parse_args()

    if not args.patterns and not args.keywords:
        parser.error("Provide at least one of --patterns or --keywords")

    repo_dir = Path(args.repo_dir).resolve()
    if not repo_dir.is_dir():
        print(f"Error: repo directory not found: {repo_dir}", file=sys.stderr)
        sys.exit(1)

    # Infer repo_id
    repo_id: str = args.repo_id or ""
    if not repo_id:
        dir_name = repo_dir.name
        repo_id = dir_name.replace("_", "/", 1) if "_" in dir_name else dir_name

    # Classify patterns
    classified_patterns: list[tuple[str, re.Pattern[str]]] = []
    if args.patterns:
        for p in args.patterns:
            match_type, regex = classify_pattern(p)
            classified_patterns.append((match_type, regex))
            print(f"  Pattern: '{p}' -> type={match_type}", file=sys.stderr)

    keyword_list: list[str] = args.keywords or []
    if keyword_list:
        print(f"  Keywords: {keyword_list}", file=sys.stderr)

    # Walk and search
    total_matches = 0
    files_with_matches = 0
    files_scanned = 0
    files_skipped = 0

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Searching {repo_dir} ...", file=sys.stderr)

    with open(output_path, "w", encoding="utf-8") as out_f:
        for dirpath, dirnames, filenames in os.walk(repo_dir):
            # Filter directories in-place to prune traversal
            dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]

            for fname in filenames:
                filepath = Path(dirpath) / fname
                rel_path = str(filepath.relative_to(repo_dir)).replace(os.sep, "/")

                # Skip test files if requested
                if args.skip_tests and is_test_path(rel_path):
                    files_skipped += 1
                    continue

                # Skip files that are too large
                try:
                    size = filepath.stat().st_size
                except OSError:
                    continue
                if size > MAX_FILE_SIZE:
                    files_skipped += 1
                    continue

                # Skip binary files
                if is_binary(filepath):
                    files_skipped += 1
                    continue

                files_scanned += 1
                matches = search_file(
                    filepath, rel_path,
                    classified_patterns, keyword_list,
                    args.context, repo_id,
                )

                if matches:
                    files_with_matches += 1
                    for m in matches:
                        out_f.write(json.dumps(m, ensure_ascii=False) + "\n")
                        total_matches += 1

    print(
        f"Found {total_matches} matches across {files_with_matches} files "
        f"({files_scanned} scanned, {files_skipped} skipped) -> {args.output}",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
