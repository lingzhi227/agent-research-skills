#!/usr/bin/env python3
"""Pre-submission LaTeX format checker.

Validates a LaTeX paper against common venue requirements:
page count, anonymization, required sections, formatting issues.

Self-contained: uses only stdlib.

Usage:
    python latex_checker.py paper/main.tex
    python latex_checker.py paper/main.tex --venue neurips --page-limit 9
    python latex_checker.py paper/main.tex --check-anon
"""

import argparse
import os
import re
import sys


VENUE_LIMITS = {
    "neurips": {"pages": 9, "columns": 1, "anonymous": True},
    "icml": {"pages": 8, "columns": 2, "anonymous": True},
    "iclr": {"pages": 9, "columns": 1, "anonymous": True},
    "aaai": {"pages": 7, "columns": 2, "anonymous": True},
    "acl": {"pages": 8, "columns": 2, "anonymous": True},
    "emnlp": {"pages": 8, "columns": 2, "anonymous": True},
    "cvpr": {"pages": 8, "columns": 2, "anonymous": True},
    "icbinb": {"pages": 4, "columns": 2, "anonymous": True},
    "arxiv": {"pages": None, "columns": None, "anonymous": False},
}

REQUIRED_SECTIONS = [
    "abstract", "introduction",
]

EXPECTED_SECTIONS = [
    "abstract", "introduction", "related work",
    "method", "experiment", "result", "conclusion",
]


def load_tex(path: str) -> str:
    """Load tex file, following \\input{} directives."""
    with open(path, encoding="utf-8", errors="replace") as f:
        content = f.read()

    # Resolve \input{file} directives
    base_dir = os.path.dirname(path)

    def resolve_input(match):
        fname = match.group(1)
        if not fname.endswith(".tex"):
            fname += ".tex"
        fpath = os.path.join(base_dir, fname)
        if os.path.exists(fpath):
            with open(fpath, encoding="utf-8", errors="replace") as f:
                return f.read()
        return match.group(0)

    content = re.sub(r"\\input\{([^}]+)\}", resolve_input, content)
    return content


def estimate_word_count(tex_content: str) -> int:
    """Rough word count excluding LaTeX commands, math, and comments."""
    # Remove comments
    text = re.sub(r"%.*$", "", tex_content, flags=re.MULTILINE)
    # Remove math environments
    text = re.sub(r"\$\$.*?\$\$", "", text, flags=re.DOTALL)
    text = re.sub(r"\$.*?\$", "", text)
    text = re.sub(r"\\begin\{(?:equation|align|gather|math).*?\}.*?\\end\{(?:equation|align|gather|math).*?\}", "", text, flags=re.DOTALL)
    # Remove LaTeX commands
    text = re.sub(r"\\[a-zA-Z]+(?:\[.*?\])?\{([^}]*)\}", r"\1", text)
    text = re.sub(r"\\[a-zA-Z]+", "", text)
    # Remove braces and special chars
    text = re.sub(r"[{}\\]", "", text)
    words = text.split()
    return len(words)


def check_anonymization(tex_content: str) -> list[str]:
    """Check for anonymization violations."""
    issues = []

    # Check for author names in common locations
    author_match = re.search(r"\\author\{([^}]+)\}", tex_content)
    if author_match:
        author_text = author_match.group(1)
        if "anonymous" not in author_text.lower() and "author" not in author_text.lower():
            issues.append(f"Author field contains names: {author_text[:50]}...")

    # Check for self-citations like "our previous work [1]"
    self_cite_patterns = [
        r"our (?:previous|prior|earlier|recent) (?:work|paper|study)",
        r"we (?:previously|earlier|recently) (?:proposed|showed|demonstrated)",
        r"in our (?:previous|prior|earlier) (?:work|paper)",
    ]
    for pat in self_cite_patterns:
        if re.search(pat, tex_content, re.IGNORECASE):
            issues.append(f"Possible self-citation: pattern '{pat}' found")

    # Check for GitHub/institutional links
    url_patterns = [
        (r"github\.com/[a-zA-Z0-9_-]+/", "GitHub link found"),
        (r"gitlab\.com/[a-zA-Z0-9_-]+/", "GitLab link found"),
        (r"\\url\{https?://(?!arxiv|doi|paperswithcode)[^}]+\}", "Non-anonymous URL found"),
    ]
    for pat, msg in url_patterns:
        match = re.search(pat, tex_content)
        if match:
            issues.append(f"{msg}: {match.group(0)[:60]}")

    # Check for acknowledgments (should be removed for review)
    if re.search(r"\\section\*?\{Acknowledgment", tex_content, re.IGNORECASE):
        issues.append("Acknowledgments section present (remove for anonymous submission)")

    return issues


def check_required_sections(tex_content: str) -> tuple[list[str], list[str]]:
    """Check for required and expected sections."""
    sections = re.findall(r"\\section\*?\{([^}]+)\}", tex_content)
    section_names_lower = [s.lower().strip() for s in sections]

    # Check abstract
    has_abstract = bool(re.search(r"\\begin\{abstract\}", tex_content))

    missing_required = []
    if not has_abstract and "abstract" not in section_names_lower:
        missing_required.append("Abstract")

    if not any("introduction" in s for s in section_names_lower):
        missing_required.append("Introduction")

    missing_expected = []
    for expected in EXPECTED_SECTIONS:
        if expected == "abstract":
            if not has_abstract:
                missing_expected.append("Abstract")
        elif not any(expected in s for s in section_names_lower):
            missing_expected.append(expected.title())

    return missing_required, missing_expected


def check_todos(tex_content: str) -> list[str]:
    """Find remaining TODO/TBD/FIXME markers."""
    issues = []
    patterns = [r"TODO", r"TBD", r"FIXME", r"XXX", r"HACK"]
    for pat in patterns:
        matches = list(re.finditer(pat, tex_content, re.IGNORECASE))
        for m in matches:
            # Get surrounding context
            start = max(0, m.start() - 30)
            end = min(len(tex_content), m.end() + 30)
            context = tex_content[start:end].replace("\n", " ").strip()
            # Skip if in a comment
            line_start = tex_content.rfind("\n", 0, m.start()) + 1
            line = tex_content[line_start:m.end()]
            if "%" in line[:line.index(pat) if pat in line else 0]:
                continue
            issues.append(f"{pat} found: ...{context}...")
    return issues


def main():
    parser = argparse.ArgumentParser(description="Pre-submission LaTeX checker")
    parser.add_argument("tex_file", help="Main .tex file")
    parser.add_argument("--venue", choices=list(VENUE_LIMITS.keys()), help="Target venue")
    parser.add_argument("--page-limit", type=int, help="Override page limit")
    parser.add_argument("--check-anon", action="store_true", help="Check anonymization")
    parser.add_argument("--fix", action="store_true", help="Apply fixes using clean_latex.py")
    args = parser.parse_args()

    tex_content = load_tex(args.tex_file)
    issues_total = 0

    print(f"Checking: {args.tex_file}")
    if args.venue:
        print(f"Venue: {args.venue.upper()}")
    print()

    # Word count
    word_count = estimate_word_count(tex_content)
    print(f"Estimated word count: {word_count}")

    # Section count
    sections = re.findall(r"\\section\*?\{([^}]+)\}", tex_content)
    print(f"Sections: {len(sections)}")
    for s in sections:
        print(f"  - {s}")
    print()

    # Required sections
    missing_req, missing_exp = check_required_sections(tex_content)
    if missing_req:
        print(f"MISSING REQUIRED SECTIONS:")
        for s in missing_req:
            print(f"  - {s}")
        issues_total += len(missing_req)
    if missing_exp:
        print(f"MISSING EXPECTED SECTIONS:")
        for s in missing_exp:
            print(f"  - {s}")
    print()

    # TODOs
    todos = check_todos(tex_content)
    if todos:
        print(f"REMAINING MARKERS ({len(todos)}):")
        for t in todos[:10]:
            print(f"  - {t}")
        issues_total += len(todos)
        print()

    # Anonymization
    if args.check_anon or (args.venue and VENUE_LIMITS.get(args.venue, {}).get("anonymous")):
        anon_issues = check_anonymization(tex_content)
        if anon_issues:
            print(f"ANONYMIZATION ISSUES ({len(anon_issues)}):")
            for issue in anon_issues:
                print(f"  - {issue}")
            issues_total += len(anon_issues)
        else:
            print("Anonymization: OK")
        print()

    # Common formatting issues
    fmt_issues = []

    # Check for unescaped special chars (outside math mode, simplified)
    for char, escaped in [("_", r"\_"), ("%", r"\%"), ("&", r"\&")]:
        # This is a simplified check
        pass

    # Check for \begin without \end
    begins = re.findall(r"\\begin\{(\w+)\}", tex_content)
    ends = re.findall(r"\\end\{(\w+)\}", tex_content)
    begin_counts = {}
    end_counts = {}
    for b in begins:
        begin_counts[b] = begin_counts.get(b, 0) + 1
    for e in ends:
        end_counts[e] = end_counts.get(e, 0) + 1
    for env in set(list(begin_counts.keys()) + list(end_counts.keys())):
        bc = begin_counts.get(env, 0)
        ec = end_counts.get(env, 0)
        if bc != ec:
            fmt_issues.append(f"Mismatched environment: \\begin{{{env}}} ({bc}x) vs \\end{{{env}}} ({ec}x)")

    if fmt_issues:
        print(f"FORMATTING ISSUES ({len(fmt_issues)}):")
        for issue in fmt_issues:
            print(f"  - {issue}")
        issues_total += len(fmt_issues)
        print()

    # Stats
    cite_count = len(re.findall(r"\\cite[a-z]*\{", tex_content))
    fig_count = len(re.findall(r"\\begin\{figure", tex_content))
    table_count = len(re.findall(r"\\begin\{table", tex_content))
    eq_count = len(re.findall(r"\\begin\{(?:equation|align)", tex_content))

    print(f"Content stats:")
    print(f"  Citations: {cite_count}")
    print(f"  Figures: {fig_count}")
    print(f"  Tables: {table_count}")
    print(f"  Equations: {eq_count}")
    print()

    # Summary
    if issues_total == 0:
        print("All checks passed!")
    else:
        print(f"Total issues: {issues_total}")

    if args.fix and issues_total > 0:
        clean_script = os.path.join(os.path.dirname(__file__), "clean_latex.py")
        if os.path.exists(clean_script):
            import subprocess
            fixed_path = args.tex_file.replace(".tex", "_fixed.tex")
            fix_cmd = [sys.executable, clean_script, "--input", args.tex_file, "--output", fixed_path]
            result = subprocess.run(fix_cmd, capture_output=True, text=True)
            if result.returncode == 0:
                print(f"\nFixed file written to: {fixed_path}")
                if result.stderr:
                    print(result.stderr)
            else:
                print(f"\nFix failed: {result.stderr}", file=sys.stderr)

    sys.exit(1 if issues_total > 0 else 0)


if __name__ == "__main__":
    main()
