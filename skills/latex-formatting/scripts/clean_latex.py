#!/usr/bin/env python3
"""Clean and sanitize LaTeX text for compilation.

Replaces special characters with LaTeX equivalents, handles math/text
mode separation, fixes non-UTF8 characters, and cleans table content.

Extracted from data-to-paper. Stdlib-only (uses re instead of regex).

Usage:
    python clean_latex.py --input draft.tex --output cleaned.tex
    python clean_latex.py --input draft.tex --dry-run
    python clean_latex.py --input draft.tex --output cleaned.tex --tables-only
"""

import argparse
import os
import re
import sys

# Special characters to LaTeX escape sequences
CHARS = {
    '&': r'\&',
    '%': r'\%',
    '#': r'\#',
    '_': r'\_',
    '^': r'\textasciicircum{}',
    '<': r'$<$',
    '>': r'$>$',
    '\u2264': r'$\leq$',      # ≤
    '\u2265': r'$\geq$',      # ≥
    '\u2260': r'$\neq$',      # ≠
    '\u00b1': r'$\pm$',       # ±
    '\u00d7': r'$\times$',    # ×
    '\u00f7': r'$\div$',      # ÷
    '\u00b0': r'$^{\circ}$',  # °
    '\u221e': r'$\infty$',    # ∞
    '\u221a': r'$\sqrt{}$',   # √
    '\u2211': r'$\sum$',      # ∑
    '\u220f': r'$\prod$',     # ∏
    '|': r'\textbar{}',
    '\u2208': r'$\in$',       # ∈
    '\u2209': r'$\notin$',    # ∉
    '\u2200': r'$\forall$',   # ∀
    '\u2203': r'$\exists$',   # ∃
    '\u2205': r'$\emptyset$', # ∅
    '\u200b': '',              # zero width space
    '\u202f': ' ',             # narrow no-break space
}

# Non-UTF8 characters to LaTeX-safe replacements
NON_UTF8_CHARS = {
    '\u2013': '--',            # –
    '\u2019': "'",             # '
    '\u2018': "`",             # '
    '\u201c': "``",            # "
    '\u201d': "''",            # "
    '\u00b2': r'$^2$',        # ²
    '\u00b3': r'$^3$',        # ³
    '\u00bc': r'$\frac{1}{4}$', # ¼
    '\u00bd': r'$\frac{1}{2}$', # ½
    '\u00be': r'$\frac{3}{4}$', # ¾
    '\u2206': r'$\Delta$',    # ∆
    '\u2207': r'$\nabla$',    # ∇
    '\u2202': r'$\partial$',  # ∂
    '\u2014': '---',           # —
    '\u2026': r'\ldots{}',    # …
    '\u00e9': r"\'e",          # é
    '\u00e8': r"\`e",          # è
    '\u00fc': r'\"u',          # ü
    '\u00f6': r'\"o',          # ö
    '\u00e4': r'\"a',          # ä
}

TABLE_CHARS = {
    '>': r'$>$',
    '<': r'$<$',
    '=': r'$=$',
    '|': r'\textbar{}',
}

# Simplified math pattern (stdlib re, no recursion)
# Matches: $...$, $$...$$, \(...\), \[...\], \begin{equation}...\end{equation},
# \begin{align}...\end{align}, \begin{figure}...\end{figure}
MATH_ENVS = [
    (r'\$\$', r'\$\$'),                          # $$...$$
    (r'(?<!\$)\$(?!\$)', r'(?<!\$)\$(?!\$)'),    # $...$
    (r'\\\(', r'\\\)'),                           # \(...\)
    (r'\\\[', r'\\\]'),                           # \[...\]
]

LATEX_ENV_NAMES = [
    'equation', 'equation*', 'align', 'align*', 'gather', 'gather*',
    'math', 'displaymath', 'figure', 'figure*', 'lstlisting',
    'tabular', 'tabular*', 'array',
]

SKIP_COMMANDS = [r'\\ref\{[^}]*\}', r'\\label\{[^}]*\}', r'\\autoref\{[^}]*\}',
                 r'\\cite[a-z]*\{[^}]*\}', r'\\url\{[^}]*\}', r'\\href\{[^}]*\}\{[^}]*\}']


def build_skip_pattern() -> re.Pattern:
    """Build a combined regex pattern for all math/skip regions."""
    patterns = []
    # Comments (% to end of line, unless escaped)
    patterns.append(r'(?<!\\)%[^\n]*')
    # Command definitions (contain # for parameters)
    patterns.append(r'\\(?:(?:re)?newcommand|providecommand|DeclareMathOperator)\*?'
                    r'(?:\{[^}]*\}|\[[^\]]*\])*\{[^}]*\}')
    patterns.append(r'\\def\\[a-zA-Z@]+[^{]*\{[^}]*\}')
    # Dollar signs
    patterns.append(r'\$\$.*?\$\$')
    patterns.append(r'(?<!\$)\$(?!\$).*?(?<!\$)\$(?!\$)')
    # Escaped delimiters
    patterns.append(r'\\\(.*?\\\)')
    patterns.append(r'\\\[.*?\\\]')
    # Named environments
    for env in LATEX_ENV_NAMES:
        esc = re.escape(env)
        patterns.append(rf'\\begin\{{{esc}\}}.*?\\end\{{{esc}\}}')
    # Skip commands
    patterns.extend(SKIP_COMMANDS)

    return re.compile('|'.join(patterns), re.DOTALL)


SKIP_RE = build_skip_pattern()


def replace_special_latex_chars(text: str) -> str:
    """Replace special characters in text (non-math) with LaTeX equivalents."""
    chars_pattern = '|'.join(re.escape(c) for c in CHARS.keys())
    pattern = re.compile(rf'(?<!\\)({chars_pattern})')
    return pattern.sub(lambda m: CHARS[m.group(1)], text)


def replace_non_utf8_chars(text: str) -> str:
    """Replace non-UTF8 characters with LaTeX-safe equivalents."""
    for char, replacement in NON_UTF8_CHARS.items():
        text = text.replace(char, replacement)
    return text


def process_latex_text_and_math(text: str, process_text=None, process_math=None) -> str:
    """Process text and math regions separately.

    Applies process_text to non-math regions and process_math to math regions.
    """
    if process_text is None:
        process_text = replace_special_latex_chars
    if process_math is None:
        process_math = lambda x: x

    result = []
    last_end = 0

    for match in SKIP_RE.finditer(text):
        # Process non-math text before this match
        non_math = text[last_end:match.start()]
        result.append(process_text(non_math))
        # Keep math region as-is (or apply process_math)
        result.append(process_math(match.group()))
        last_end = match.end()

    # Process remaining text after last match
    result.append(process_text(text[last_end:]))
    return "".join(result)


def escape_table_chars(text: str) -> str:
    """Escape special characters in table cells."""
    pattern = re.compile('|'.join(re.escape(k) for k in TABLE_CHARS.keys()))
    return pattern.sub(lambda m: TABLE_CHARS[m.group()], text)


def escape_special_chars_in_table(table: str,
                                   begin: str = r'\begin{tabular}',
                                   end: str = r'\end{tabular}') -> str:
    """Apply character escaping to the tabular content of a LaTeX table."""
    if begin not in table:
        return table
    if end not in table:
        return table
    before, rest = table.split(begin, 1)
    tabular, after = rest.split(end, 1)
    tabular = process_latex_text_and_math(tabular, escape_table_chars)
    return before + begin + tabular + end + after


def clean_latex_file(content: str, tables_only: bool = False) -> str:
    """Clean a full LaTeX file content."""
    if tables_only:
        # Only clean table environments
        parts = re.split(r'(\\begin\{tabular\}.*?\\end\{tabular\})', content, flags=re.DOTALL)
        result = []
        for part in parts:
            if part.startswith(r'\begin{tabular}'):
                result.append(escape_special_chars_in_table(part))
            else:
                result.append(part)
        return ''.join(result)

    # Full cleaning
    content = replace_non_utf8_chars(content)
    content = process_latex_text_and_math(content)
    return content


def main():
    parser = argparse.ArgumentParser(description="Clean and sanitize LaTeX text")
    parser.add_argument("--input", required=True, help="Input .tex file")
    parser.add_argument("--output", "-o", help="Output .tex file (default: stdout)")
    parser.add_argument("--dry-run", action="store_true", help="Show changes without writing")
    parser.add_argument("--tables-only", action="store_true", help="Only clean table environments")
    args = parser.parse_args()

    with open(args.input, encoding="utf-8", errors="replace") as f:
        content = f.read()

    cleaned = clean_latex_file(content, tables_only=args.tables_only)

    if args.dry_run:
        # Show diff summary
        orig_lines = content.splitlines()
        new_lines = cleaned.splitlines()
        changes = 0
        for i, (old, new) in enumerate(zip(orig_lines, new_lines)):
            if old != new:
                changes += 1
                if changes <= 20:
                    print(f"Line {i+1}:")
                    print(f"  - {old[:100]}")
                    print(f"  + {new[:100]}")
        if changes > 20:
            print(f"... and {changes - 20} more changes")
        print(f"\nTotal lines changed: {changes}")
        return

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(cleaned)
        print(f"Cleaned file written to {args.output}", file=sys.stderr)
    else:
        sys.stdout.write(cleaned)


if __name__ == "__main__":
    main()
