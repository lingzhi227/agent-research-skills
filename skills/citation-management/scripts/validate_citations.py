#!/usr/bin/env python3
"""Validate LaTeX citations against BibTeX file.

Checks that all \\cite{key} references in .tex files have matching entries in .bib,
finds unused bib entries, and detects duplicates.

Self-contained: uses only stdlib.

Usage:
    python validate_citations.py --tex paper/main.tex --bib paper/references.bib
    python validate_citations.py --tex-dir paper/ --bib paper/references.bib
    python validate_citations.py --tex paper/main.tex --bib paper/references.bib --fix
"""

import argparse
import glob
import os
import re
import sys


def extract_cite_keys(tex_content: str) -> list[str]:
    """Extract all citation keys from LaTeX content."""
    # Match \cite{}, \citep{}, \citet{}, \citeauthor{}, etc.
    pattern = r"\\cite[a-z]*\{([^}]*)\}"
    matches = re.findall(pattern, tex_content)
    keys = []
    for match in matches:
        # Handle multiple keys in one \cite{key1, key2}
        for key in match.split(","):
            key = key.strip()
            if key:
                keys.append(key)
    return keys


def extract_bib_keys(bib_content: str) -> list[str]:
    """Extract all entry keys from BibTeX content."""
    pattern = r"@\w+\{([^,]+),"
    matches = re.findall(pattern, bib_content)
    return [m.strip() for m in matches]


def extract_figure_refs(tex_content: str) -> list[str]:
    """Extract all included graphics filenames."""
    pattern = r"\\includegraphics(?:\[.*?\])?\{([^}]*)\}"
    return re.findall(pattern, tex_content)


def extract_labels(tex_content: str) -> list[str]:
    """Extract all \\label{} definitions."""
    pattern = r"\\label\{([^}]*)\}"
    return re.findall(pattern, tex_content)


def extract_refs(tex_content: str) -> list[str]:
    """Extract all \\ref{} and \\cref{} references."""
    pattern = r"\\(?:c?C?ref|autoref|eqref)\{([^}]*)\}"
    return re.findall(pattern, tex_content)


def extract_sections(tex_content: str) -> list[str]:
    """Extract all \\section{} headers."""
    pattern = r"\\section\{([^}]*)\}"
    return re.findall(pattern, tex_content)


def find_duplicates(items: list[str]) -> dict[str, int]:
    """Find items that appear more than once."""
    counts = {}
    for item in items:
        counts[item] = counts.get(item, 0) + 1
    return {k: v for k, v in counts.items() if v > 1}


def main():
    parser = argparse.ArgumentParser(description="Validate LaTeX citations and references")
    parser.add_argument("--tex", help="Main .tex file")
    parser.add_argument("--tex-dir", help="Directory to scan for .tex files")
    parser.add_argument("--bib", required=True, help=".bib file")
    parser.add_argument("--check-figures", action="store_true", help="Also check figure files exist")
    parser.add_argument("--figures-dir", help="Directory containing figures")
    parser.add_argument("--fix", action="store_true", help="Output suggested fixes")
    args = parser.parse_args()

    # Load tex content
    tex_files = []
    if args.tex:
        tex_files = [args.tex]
    elif args.tex_dir:
        tex_files = glob.glob(os.path.join(args.tex_dir, "**/*.tex"), recursive=True)
    else:
        print("Error: must specify --tex or --tex-dir", file=sys.stderr)
        sys.exit(1)

    all_tex = ""
    for tf in tex_files:
        with open(tf, encoding="utf-8", errors="replace") as f:
            all_tex += f.read() + "\n"

    # Load bib content
    with open(args.bib, encoding="utf-8", errors="replace") as f:
        bib_content = f.read()

    # Also check for embedded bib in filecontents
    embedded_bib = re.search(
        r"\\begin\{filecontents\}\{references\.bib\}(.*?)\\end\{filecontents\}",
        all_tex, re.DOTALL
    )
    if embedded_bib:
        bib_content += "\n" + embedded_bib.group(1)

    cite_keys = extract_cite_keys(all_tex)
    bib_keys = extract_bib_keys(bib_content)

    cite_set = set(cite_keys)
    bib_set = set(bib_keys)

    issues = 0

    # 1. Missing citations
    missing = cite_set - bib_set
    if missing:
        print(f"\n## MISSING CITATIONS ({len(missing)})")
        print("These \\cite{{key}} are used in .tex but not defined in .bib:")
        for key in sorted(missing):
            count = cite_keys.count(key)
            print(f"  - {key} (used {count}x)")
        issues += len(missing)

    # 2. Unused bib entries
    unused = bib_set - cite_set
    if unused:
        print(f"\n## UNUSED BIB ENTRIES ({len(unused)})")
        print("These entries are in .bib but never cited:")
        for key in sorted(unused):
            print(f"  - {key}")

    # 3. Duplicate bib keys
    dup_bib = find_duplicates(extract_bib_keys(bib_content))
    if dup_bib:
        print(f"\n## DUPLICATE BIB KEYS ({len(dup_bib)})")
        for key, count in sorted(dup_bib.items()):
            print(f"  - {key} (defined {count}x)")
        issues += len(dup_bib)

    # 4. Duplicate section headers
    sections = extract_sections(all_tex)
    dup_sections = find_duplicates(sections)
    if dup_sections:
        print(f"\n## DUPLICATE SECTIONS ({len(dup_sections)})")
        for sec, count in sorted(dup_sections.items()):
            print(f"  - \\section{{{sec}}} (appears {count}x)")
        issues += len(dup_sections)

    # 5. Duplicate labels
    labels = extract_labels(all_tex)
    dup_labels = find_duplicates(labels)
    if dup_labels:
        print(f"\n## DUPLICATE LABELS ({len(dup_labels)})")
        for label, count in sorted(dup_labels.items()):
            print(f"  - \\label{{{label}}} (defined {count}x)")
        issues += len(dup_labels)

    # 6. Undefined references
    refs = extract_refs(all_tex)
    label_set = set(labels)
    undefined_refs = [r for r in refs if r not in label_set]
    if undefined_refs:
        print(f"\n## UNDEFINED REFERENCES ({len(set(undefined_refs))})")
        for ref in sorted(set(undefined_refs)):
            print(f"  - \\ref{{{ref}}}")
        issues += len(set(undefined_refs))

    # 7. Figure file checks
    if args.check_figures:
        fig_dir = args.figures_dir or os.path.dirname(tex_files[0]) if tex_files else "."
        fig_refs = extract_figure_refs(all_tex)
        for fig in fig_refs:
            fig_path = os.path.join(fig_dir, fig)
            if not os.path.exists(fig_path):
                print(f"\n## MISSING FIGURE: {fig}")
                print(f"  Not found at: {fig_path}")
                issues += 1

        # Duplicate figure references
        dup_figs = find_duplicates(fig_refs)
        if dup_figs:
            print(f"\n## DUPLICATE FIGURES ({len(dup_figs)})")
            for fig, count in sorted(dup_figs.items()):
                print(f"  - {fig} (included {count}x)")
            issues += len(dup_figs)

    # Summary
    print(f"\n## SUMMARY")
    print(f"  Citations used: {len(cite_set)}")
    print(f"  Bib entries: {len(bib_set)}")
    print(f"  Labels defined: {len(set(labels))}")
    print(f"  References used: {len(set(refs))}")
    print(f"  Issues found: {issues}")

    if issues == 0:
        print("  All checks passed!")

    if args.fix and missing:
        print(f"\n## AUTO-FIX: Generating placeholder entries for {len(missing)} missing keys")
        fix_entries = []
        for key in sorted(missing):
            entry = f"@misc{{{key},\n  title = {{{key.replace('_', ' ')}}},\n  note = {{TODO: Replace with actual reference}},\n  year = {{20XX}},\n}}"
            fix_entries.append(entry)

        fix_bib_path = args.bib.replace(".bib", "_fixed.bib")
        with open(args.bib, encoding="utf-8", errors="replace") as f:
            original_bib = f.read()
        with open(fix_bib_path, "w", encoding="utf-8") as f:
            f.write(original_bib)
            f.write("\n\n% === Auto-generated placeholder entries ===\n")
            for entry in fix_entries:
                f.write("\n" + entry + "\n")
        print(f"  Patched .bib written to: {fix_bib_path}")
        print(f"  {len(fix_entries)} placeholder entries added (marked with TODO)")

    sys.exit(1 if issues > 0 else 0)


if __name__ == "__main__":
    main()
