#!/usr/bin/env python3
"""Map repo file tree, identify key files, and compute LOC stats.

Usage:
    python analyze_repo_structure.py --repo-dir /tmp/repos/myrepo --output analysis.json [--repo-id owner/name]

Writes analysis JSON to the specified output file.
"""

import argparse
import json
import os
import re
import sys

# Directories to skip during traversal
SKIP_DIRS = {
    ".git", "node_modules", "__pycache__", ".venv", "venv",
    ".tox", ".eggs", "dist", "build",
}

# File extension to language mapping
EXT_TO_LANG = {
    ".py": "Python",
    ".js": "JavaScript",
    ".ts": "TypeScript",
    ".rs": "Rust",
    ".go": "Go",
    ".java": "Java",
    ".cpp": "C++",
    ".cc": "C++",
    ".cxx": "C++",
    ".c": "C",
    ".rb": "Ruby",
    ".sh": "Shell",
    ".yaml": "YAML",
    ".yml": "YAML",
    ".json": "JSON",
    ".md": "Markdown",
}

# Known config file names
CONFIG_FILES = {
    "pyproject.toml", "setup.py", "setup.cfg", "package.json",
    "Cargo.toml", "go.mod", "Makefile", "Dockerfile",
    "docker-compose.yml", "docker-compose.yaml",
    ".env.example", "tox.ini",
}

# Known entry-point file names
ENTRY_POINT_NAMES = {"main.py", "app.py", "run.py", "train.py", "setup.py", "Makefile", "Dockerfile"}


def is_egg_info_dir(name: str) -> bool:
    return name.endswith(".egg-info")


def count_loc(filepath: str) -> int:
    """Count non-empty lines in a text file."""
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            return sum(1 for line in f if line.strip())
    except (OSError, UnicodeDecodeError):
        return 0


def has_shebang(filepath: str) -> bool:
    """Check if file starts with a shebang line."""
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            first_line = f.readline()
            return first_line.startswith("#!")
    except (OSError, UnicodeDecodeError):
        return False


def has_main_guard(filepath: str) -> bool:
    """Check if a Python file has `if __name__` guard."""
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                if re.search(r'if\s+__name__\s*==\s*["\']__main__["\']', line):
                    return True
    except (OSError, UnicodeDecodeError):
        pass
    return False


def should_skip_dir(name: str) -> bool:
    return name in SKIP_DIRS or is_egg_info_dir(name)


def build_tree(repo_dir: str, max_lines: int = 200) -> str:
    """Generate an indented file tree string, truncated to max_lines."""
    lines = []
    base = os.path.basename(os.path.abspath(repo_dir))

    for dirpath, dirnames, filenames in os.walk(repo_dir):
        # Filter out skipped dirs in-place
        dirnames[:] = sorted([d for d in dirnames if not should_skip_dir(d)])
        filenames = sorted(filenames)

        rel = os.path.relpath(dirpath, repo_dir)
        depth = 0 if rel == "." else rel.count(os.sep) + 1
        indent = "  " * depth

        if rel == ".":
            lines.append(f"{base}/")
        else:
            lines.append(f"{indent}{os.path.basename(dirpath)}/")

        if len(lines) >= max_lines:
            break

        file_indent = "  " * (depth + 1)
        for fname in filenames:
            lines.append(f"{file_indent}{fname}")
            if len(lines) >= max_lines:
                break
        if len(lines) >= max_lines:
            break

    if len(lines) >= max_lines:
        lines.append("  ... (truncated)")
    return "\n".join(lines)


def analyze(repo_dir: str, repo_id: str) -> dict:
    """Perform full repo structure analysis."""
    total_files = 0
    total_loc = 0
    languages: dict[str, int] = {}
    key_files: list[str] = []
    entry_points: list[str] = []
    config_files: list[str] = []
    test_files: list[str] = []
    doc_files: list[str] = []
    file_loc: list[tuple[str, int]] = []

    print(f"[analyze] Scanning {repo_dir} ...", file=sys.stderr)

    for dirpath, dirnames, filenames in os.walk(repo_dir):
        dirnames[:] = [d for d in dirnames if not should_skip_dir(d)]

        rel_dir = os.path.relpath(dirpath, repo_dir)

        for fname in filenames:
            filepath = os.path.join(dirpath, fname)
            rel_path = os.path.join(rel_dir, fname) if rel_dir != "." else fname
            # Normalize path separators
            rel_path = rel_path.replace(os.sep, "/")

            total_files += 1

            _, ext = os.path.splitext(fname)
            ext_lower = ext.lower()

            # LOC counting for known languages
            lang = EXT_TO_LANG.get(ext_lower)
            loc = 0
            if lang:
                loc = count_loc(filepath)
                languages[lang] = languages.get(lang, 0) + loc
                total_loc += loc
                file_loc.append((rel_path, loc))

            # Entry points detection
            if fname in ENTRY_POINT_NAMES:
                entry_points.append(rel_path)
            elif ext_lower == ".py" and has_main_guard(filepath):
                entry_points.append(rel_path)
            elif has_shebang(filepath):
                entry_points.append(rel_path)

            # Config files
            if fname in CONFIG_FILES:
                config_files.append(rel_path)

            # Test files
            if (fname.startswith("test_") or fname.endswith(("_test.py", "_test.js", "_test.ts", "_test.go"))
                    or "/tests/" in f"/{rel_path}/" or "/test/" in f"/{rel_path}/"
                    or "/spec/" in f"/{rel_path}/"):
                test_files.append(rel_path)

            # Doc files
            if ext_lower == ".md" or "/docs/" in f"/{rel_path}/" or "/doc/" in f"/{rel_path}/":
                doc_files.append(rel_path)

    # Sort files by LOC descending, take top 10
    file_loc.sort(key=lambda x: x[1], reverse=True)
    file_size_top10 = file_loc[:10]

    # Key files = top LOC files + entry points
    key_set = set()
    for path, _ in file_size_top10:
        key_set.add(path)
    for path in entry_points:
        key_set.add(path)
    key_files = sorted(key_set)

    # Sort languages by LOC descending
    languages = dict(sorted(languages.items(), key=lambda x: x[1], reverse=True))

    tree = build_tree(repo_dir)

    print(f"[analyze] Files: {total_files}, LOC: {total_loc}, Languages: {len(languages)}", file=sys.stderr)

    return {
        "repo_id": repo_id,
        "total_files": total_files,
        "total_loc": total_loc,
        "languages": languages,
        "key_files": key_files,
        "entry_points": sorted(set(entry_points)),
        "config_files": sorted(set(config_files)),
        "test_files": sorted(set(test_files)),
        "doc_files": sorted(set(doc_files)),
        "tree": tree,
        "file_size_top10": file_size_top10,
    }


def main():
    parser = argparse.ArgumentParser(description="Analyze repository structure, files, and LOC stats.")
    parser.add_argument("--repo-dir", required=True, help="Path to the cloned repository")
    parser.add_argument("--output", required=True, help="Output JSON file path")
    parser.add_argument("--repo-id", default="unknown/unknown", help="Repository identifier (owner/name)")
    args = parser.parse_args()

    if not os.path.isdir(args.repo_dir):
        print(f"Error: {args.repo_dir} is not a directory", file=sys.stderr)
        sys.exit(1)

    result = analyze(args.repo_dir, args.repo_id)

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"[analyze] Output written to {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
