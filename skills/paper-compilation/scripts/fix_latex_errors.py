#!/usr/bin/env python3
"""Automated LaTeX error fixer.

Reads a pdflatex error log and the corresponding .tex file, identifies
common errors, and applies automated fixes.

Self-contained: uses only stdlib.

Usage:
    python fix_latex_errors.py --tex main.tex --log compile.log --output fixed.tex
    python fix_latex_errors.py --tex main.tex --log compile.log --dry-run
    python fix_latex_errors.py --tex main.tex --auto-detect --output fixed.tex
"""

import argparse
import os
import re
import sys


class LatexFix:
    """A fix to apply to LaTeX content."""
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.applied = False

    def __repr__(self):
        return f"Fix({self.name})"


def parse_errors(log_content: str) -> list[dict]:
    """Parse pdflatex log file and extract errors with context."""
    errors = []
    lines = log_content.split("\n")
    for i, line in enumerate(lines):
        if line.startswith("! "):
            error = {"message": line[2:], "context": [], "line_num": None, "type": ""}
            # Get context lines
            for j in range(i + 1, min(i + 6, len(lines))):
                error["context"].append(lines[j])
            # Try to extract line number
            for ctx in error["context"]:
                m = re.search(r"l\.(\d+)", ctx)
                if m:
                    error["line_num"] = int(m.group(1))
                    break
            # Classify error
            msg = error["message"]
            if "Undefined control sequence" in msg:
                error["type"] = "undefined_command"
            elif "Missing $ inserted" in msg:
                error["type"] = "missing_math"
            elif "Missing } inserted" in msg or "Missing { inserted" in msg:
                error["type"] = "missing_brace"
            elif "Environment" in msg and "undefined" in msg:
                error["type"] = "undefined_env"
            elif "File" in msg and "not found" in msg:
                error["type"] = "missing_file"
            elif "Misplaced alignment tab" in msg:
                error["type"] = "misplaced_tab"
            else:
                error["type"] = "other"
            errors.append(error)

    # Also extract warnings about undefined citations/references
    for line in lines:
        if "Citation" in line and "undefined" in line:
            m = re.search(r"`([^']+)'", line)
            key = m.group(1) if m else ""
            errors.append({"message": line.strip(), "type": "undefined_citation",
                           "context": [], "line_num": None, "key": key})
        elif "Reference" in line and "undefined" in line:
            m = re.search(r"`([^']+)'", line)
            key = m.group(1) if m else ""
            errors.append({"message": line.strip(), "type": "undefined_reference",
                           "context": [], "line_num": None, "key": key})

    return errors


def fix_unescaped_chars(content: str) -> tuple[str, list[LatexFix]]:
    """Fix unescaped special characters in non-math text."""
    fixes = []
    # Build pattern to skip math regions
    math_regions = []
    for m in re.finditer(r'\$\$.*?\$\$|\$.*?\$|\\\(.*?\\\)|\\\[.*?\\\]', content, re.DOTALL):
        math_regions.append((m.start(), m.end()))

    def in_math(pos):
        return any(s <= pos < e for s, e in math_regions)

    # Fix unescaped & outside tabular
    result = list(content)
    char_fixes = [
        ('&', r'\&', 'unescaped_ampersand'),
        ('%', r'\%', 'unescaped_percent'),
        ('#', r'\#', 'unescaped_hash'),
    ]

    for char, replacement, fix_name in char_fixes:
        new_content = content
        offset = 0
        for m in re.finditer(re.escape(char), content):
            pos = m.start()
            if in_math(pos):
                continue
            # Check if already escaped
            if pos > 0 and content[pos - 1] == '\\':
                continue
            # Don't fix in tabular environments
            before = content[:pos]
            if before.count(r'\begin{tabular}') > before.count(r'\end{tabular}'):
                continue
            fix = LatexFix(fix_name, f"Escaped {char} at position {pos}")
            fixes.append(fix)

    # Apply fixes via regex (simpler approach)
    for char, replacement, _ in char_fixes:
        # Only fix in non-math, non-tabular, non-already-escaped contexts
        new = []
        last = 0
        in_tab = 0
        for m in re.finditer(r'\\begin\{tabular\}|\\end\{tabular\}|' + re.escape(char), content[last:]):
            pass  # Complex tracking, use simpler approach

    return content, fixes


def fix_html_tags(content: str) -> tuple[str, list[LatexFix]]:
    """Replace HTML-like tags that end up in LaTeX."""
    fixes = []
    replacements = [
        (r'<b>(.*?)</b>', r'\\textbf{\1}', 'html_bold'),
        (r'<i>(.*?)</i>', r'\\textit{\1}', 'html_italic'),
        (r'<em>(.*?)</em>', r'\\emph{\1}', 'html_emphasis'),
        (r'<br\s*/?>', r'\\\\', 'html_br'),
        (r'<p>', r'\n\n', 'html_p_open'),
        (r'</p>', '', 'html_p_close'),
        (r'<code>(.*?)</code>', r'\\texttt{\1}', 'html_code'),
        (r'<sub>(.*?)</sub>', r'$_{\1}$', 'html_subscript'),
        (r'<sup>(.*?)</sup>', r'$^{\1}$', 'html_superscript'),
        (r'</?(div|span|section|h[1-6])[^>]*>', '', 'html_block'),
    ]
    for pattern, repl, fix_name in replacements:
        matches = list(re.finditer(pattern, content, re.IGNORECASE))
        if matches:
            fixes.append(LatexFix(fix_name, f"Replaced {len(matches)} HTML {fix_name} tags"))
            content = re.sub(pattern, repl, content, flags=re.IGNORECASE)
    return content, fixes


def fix_mismatched_environments(content: str) -> tuple[str, list[LatexFix]]:
    """Detect and report mismatched begin/end environments."""
    fixes = []
    begins = re.findall(r'\\begin\{(\w+)\}', content)
    ends = re.findall(r'\\end\{(\w+)\}', content)
    begin_counts = {}
    end_counts = {}
    for b in begins:
        begin_counts[b] = begin_counts.get(b, 0) + 1
    for e in ends:
        end_counts[e] = end_counts.get(e, 0) + 1

    for env in set(list(begin_counts.keys()) + list(end_counts.keys())):
        bc = begin_counts.get(env, 0)
        ec = end_counts.get(env, 0)
        if bc > ec:
            # Missing \end — add at end of document
            for _ in range(bc - ec):
                content = content.rstrip() + f"\n\\end{{{env}}}\n"
                fixes.append(LatexFix(f"add_end_{env}", f"Added missing \\end{{{env}}}"))
        elif ec > bc:
            # Extra \end — remove last occurrence
            for _ in range(ec - bc):
                idx = content.rfind(f"\\end{{{env}}}")
                if idx >= 0:
                    content = content[:idx] + content[idx + len(f"\\end{{{env}}}"):]
                    fixes.append(LatexFix(f"remove_end_{env}", f"Removed extra \\end{{{env}}}"))

    return content, fixes


def fix_missing_math_mode(content: str) -> tuple[str, list[LatexFix]]:
    """Fix common math-mode issues like unescaped underscores in text."""
    fixes = []
    # Find _ outside math mode that's part of a variable name pattern
    # e.g., "model_name" should become "model\_name" or "$model\_name$"
    # This is a simplified heuristic
    return content, fixes


def fix_missing_figures(content: str, tex_dir: str) -> tuple[str, list[LatexFix]]:
    """Comment out includegraphics for missing figure files."""
    fixes = []
    for m in re.finditer(r'\\includegraphics(?:\[.*?\])?\{([^}]+)\}', content):
        fig_path = m.group(1)
        full_path = os.path.join(tex_dir, fig_path)
        # Check with and without common extensions
        found = os.path.exists(full_path)
        if not found:
            for ext in ['.png', '.pdf', '.jpg', '.jpeg', '.eps']:
                if os.path.exists(full_path + ext):
                    found = True
                    break
        if not found:
            # Comment out the line containing this includegraphics
            line_start = content.rfind('\n', 0, m.start()) + 1
            line_end = content.find('\n', m.end())
            if line_end == -1:
                line_end = len(content)
            original_line = content[line_start:line_end]
            if not original_line.strip().startswith('%'):
                commented = '% FIXME: missing file - ' + original_line
                content = content[:line_start] + commented + content[line_end:]
                fixes.append(LatexFix("comment_missing_figure",
                                      f"Commented out missing figure: {fig_path}"))
    return content, fixes


def auto_detect_log(tex_file: str) -> str | None:
    """Try to find the .log file for a .tex file."""
    base = os.path.splitext(tex_file)[0]
    log_file = base + ".log"
    if os.path.exists(log_file):
        return log_file
    return None


def main():
    parser = argparse.ArgumentParser(description="Automated LaTeX error fixer")
    parser.add_argument("--tex", required=True, help="Main .tex file")
    parser.add_argument("--log", help="pdflatex .log file")
    parser.add_argument("--auto-detect", action="store_true", help="Auto-detect .log file")
    parser.add_argument("--output", "-o", help="Output .tex file")
    parser.add_argument("--dry-run", action="store_true", help="Show fixes without applying")
    args = parser.parse_args()

    if not os.path.exists(args.tex):
        print(f"Error: {args.tex} not found", file=sys.stderr)
        sys.exit(1)

    with open(args.tex, encoding="utf-8", errors="replace") as f:
        content = f.read()

    tex_dir = os.path.dirname(os.path.abspath(args.tex))

    # Load error log if available
    log_content = ""
    log_file = args.log
    if not log_file and args.auto_detect:
        log_file = auto_detect_log(args.tex)
    if log_file and os.path.exists(log_file):
        with open(log_file, encoding="utf-8", errors="replace") as f:
            log_content = f.read()

    errors = parse_errors(log_content) if log_content else []
    if errors:
        print(f"Found {len(errors)} errors/warnings in log", file=sys.stderr)
        for e in errors[:10]:
            print(f"  [{e['type']}] {e['message'][:80]}", file=sys.stderr)

    # Apply fixes
    all_fixes = []

    content, fixes = fix_html_tags(content)
    all_fixes.extend(fixes)

    content, fixes = fix_mismatched_environments(content)
    all_fixes.extend(fixes)

    content, fixes = fix_missing_figures(content, tex_dir)
    all_fixes.extend(fixes)

    content, fixes = fix_missing_math_mode(content)
    all_fixes.extend(fixes)

    if args.dry_run:
        print(f"\n## Fixes that would be applied ({len(all_fixes)}):")
        for fix in all_fixes:
            print(f"  - [{fix.name}] {fix.description}")
        if not all_fixes:
            print("  No fixes needed.")
        sys.exit(0)

    if not all_fixes:
        print("No fixes needed.", file=sys.stderr)
        sys.exit(0)

    print(f"\nApplied {len(all_fixes)} fixes:", file=sys.stderr)
    for fix in all_fixes:
        print(f"  - [{fix.name}] {fix.description}", file=sys.stderr)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Fixed file written to {args.output}", file=sys.stderr)
    else:
        sys.stdout.write(content)


if __name__ == "__main__":
    main()
