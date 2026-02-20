#!/usr/bin/env python3
"""Extract paper elements for slide generation.

Parses a .tex file and extracts title, authors, sections, equations,
figure paths with captions, tables, and generates a Beamer skeleton.

Self-contained: uses only stdlib.

Usage:
    python extract_paper_elements.py --tex main.tex --output slides_skeleton.tex
    python extract_paper_elements.py --tex main.tex --format json --output elements.json
    python extract_paper_elements.py --tex main.tex --output slides.tex --theme metropolis
"""

import argparse
import json
import os
import re
import sys


def load_tex(path: str) -> str:
    """Load .tex file, resolving \\input{} directives."""
    with open(path, encoding="utf-8", errors="replace") as f:
        content = f.read()

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


def extract_title(tex: str) -> str:
    """Extract paper title."""
    m = re.search(r"\\title(?:\[.*?\])?\{(.+?)\}", tex, re.DOTALL)
    return m.group(1).strip().replace("\n", " ") if m else ""


def extract_authors(tex: str) -> list[str]:
    """Extract author names."""
    m = re.search(r"\\author(?:\[.*?\])?\{(.+?)\}", tex, re.DOTALL)
    if not m:
        return []
    author_text = m.group(1)
    # Clean up LaTeX formatting
    author_text = re.sub(r"\\[a-zA-Z]+\{[^}]*\}", "", author_text)
    author_text = re.sub(r"\\\\", ",", author_text)
    author_text = re.sub(r"\s+", " ", author_text)
    authors = [a.strip() for a in author_text.split(",") if a.strip()]
    # Filter out affiliations (typically shorter or contain numbers)
    return [a for a in authors if len(a) > 3 and not re.match(r"^\d", a)]


def extract_abstract(tex: str) -> str:
    """Extract abstract text."""
    m = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", tex, re.DOTALL)
    return m.group(1).strip() if m else ""


def extract_sections(tex: str) -> list[dict]:
    """Extract section names and their content."""
    sections = []
    parts = re.split(r"(\\(?:sub)?section\*?\{[^}]+\})", tex)

    current_name = None
    current_text = ""
    current_level = 0

    for part in parts:
        sec_match = re.match(r"\\(sub)?section\*?\{([^}]+)\}", part)
        if sec_match:
            if current_name:
                sections.append({
                    "name": current_name,
                    "level": current_level,
                    "text": current_text.strip()[:500],
                })
            is_sub = sec_match.group(1) is not None
            current_name = sec_match.group(2).strip()
            current_level = 2 if is_sub else 1
            current_text = ""
        else:
            current_text += part

    if current_name:
        sections.append({
            "name": current_name,
            "level": current_level,
            "text": current_text.strip()[:500],
        })

    return sections


def extract_figures(tex: str) -> list[dict]:
    """Extract figure paths and captions."""
    figures = []
    fig_envs = re.finditer(
        r"\\begin\{figure\*?\}.*?\\end\{figure\*?\}", tex, re.DOTALL
    )
    for fig in fig_envs:
        fig_text = fig.group()
        path_match = re.search(r"\\includegraphics(?:\[.*?\])?\{([^}]+)\}", fig_text)
        caption_match = re.search(r"\\caption\{(.+?)\}", fig_text, re.DOTALL)
        label_match = re.search(r"\\label\{([^}]+)\}", fig_text)

        figures.append({
            "path": path_match.group(1) if path_match else "",
            "caption": caption_match.group(1).strip()[:200] if caption_match else "",
            "label": label_match.group(1) if label_match else "",
        })

    return figures


def extract_equations(tex: str) -> list[str]:
    """Extract key equations."""
    equations = []
    # Numbered equations
    for m in re.finditer(r"\\begin\{equation\*?\}(.*?)\\end\{equation\*?\}", tex, re.DOTALL):
        equations.append(m.group(1).strip())
    # Align environments
    for m in re.finditer(r"\\begin\{align\*?\}(.*?)\\end\{align\*?\}", tex, re.DOTALL):
        equations.append(m.group(1).strip())
    return equations


def extract_tables(tex: str) -> list[dict]:
    """Extract table captions and labels."""
    tables = []
    for m in re.finditer(r"\\begin\{table\*?\}.*?\\end\{table\*?\}", tex, re.DOTALL):
        table_text = m.group()
        caption_match = re.search(r"\\caption\{(.+?)\}", table_text, re.DOTALL)
        label_match = re.search(r"\\label\{([^}]+)\}", table_text)
        tables.append({
            "caption": caption_match.group(1).strip()[:200] if caption_match else "",
            "label": label_match.group(1) if label_match else "",
        })
    return tables


def generate_beamer(elements: dict, theme: str = "metropolis") -> str:
    """Generate a Beamer LaTeX skeleton from extracted elements."""
    lines = [
        f"\\documentclass[aspectratio=169]{{beamer}}",
        f"\\usetheme{{{theme}}}",
        f"\\title{{{elements['title']}}}",
    ]
    if elements["authors"]:
        lines.append(f"\\author{{{', '.join(elements['authors'][:4])}}}")
    lines.extend([
        "\\date{\\today}",
        "",
        "\\begin{document}",
        "\\maketitle",
        "",
    ])

    # Outline slide
    lines.extend([
        "\\begin{frame}{Outline}",
        "\\tableofcontents",
        "\\end{frame}",
        "",
    ])

    # Motivation / Introduction
    if elements["abstract"]:
        abstract_bullets = elements["abstract"][:300].split(". ")[:3]
        lines.append("\\begin{frame}{Motivation}")
        lines.append("\\begin{itemize}")
        for bullet in abstract_bullets:
            bullet = bullet.strip()
            if bullet and len(bullet) > 10:
                lines.append(f"    \\item {bullet}.")
        lines.append("\\end{itemize}")
        lines.append("\\end{frame}")
        lines.append("")

    # Section slides
    for sec in elements["sections"]:
        if sec["level"] > 1:
            continue  # Skip subsections
        sec_name = sec["name"]
        if any(skip in sec_name.lower() for skip in ["acknowledge", "appendix"]):
            continue

        lines.append(f"\\section{{{sec_name}}}")
        lines.append(f"\\begin{{frame}}{{{sec_name}}}")
        lines.append("\\begin{itemize}")
        lines.append("    \\item TODO: Key points")
        lines.append("\\end{itemize}")
        lines.append("\\end{frame}")
        lines.append("")

    # Figure slides
    for fig in elements["figures"][:6]:
        if fig["path"]:
            lines.append(f"\\begin{{frame}}{{{fig['caption'][:50] or 'Results'}}}")
            lines.append("\\centering")
            lines.append(f"\\includegraphics[width=0.8\\linewidth]{{{fig['path']}}}")
            if fig["caption"]:
                lines.append(f"% {fig['caption'][:100]}")
            lines.append("\\end{frame}")
            lines.append("")

    # Key equations
    for eq in elements["equations"][:3]:
        lines.append("\\begin{frame}{Key Equation}")
        lines.append("\\begin{equation*}")
        lines.append(f"  {eq}")
        lines.append("\\end{equation*}")
        lines.append("\\end{frame}")
        lines.append("")

    # Thank you slide
    lines.extend([
        "\\begin{frame}",
        "\\centering",
        "{\\Large Thank You!}",
        "",
        "\\vspace{1em}",
        "Questions?",
        "\\end{frame}",
        "",
        "\\end{document}",
    ])

    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description="Extract paper elements for slides")
    parser.add_argument("--tex", required=True, help="Main .tex file")
    parser.add_argument("--output", "-o", help="Output file")
    parser.add_argument("--format", choices=["beamer", "json"], default="beamer",
                        help="Output format (default: beamer)")
    parser.add_argument("--theme", default="metropolis", help="Beamer theme (default: metropolis)")
    args = parser.parse_args()

    if not os.path.exists(args.tex):
        print(f"Error: {args.tex} not found", file=sys.stderr)
        sys.exit(1)

    tex = load_tex(args.tex)
    elements = {
        "title": extract_title(tex),
        "authors": extract_authors(tex),
        "abstract": extract_abstract(tex),
        "sections": extract_sections(tex),
        "figures": extract_figures(tex),
        "equations": extract_equations(tex),
        "tables": extract_tables(tex),
    }

    print(f"Extracted from {args.tex}:", file=sys.stderr)
    print(f"  Title: {elements['title'][:60]}", file=sys.stderr)
    print(f"  Authors: {len(elements['authors'])}", file=sys.stderr)
    print(f"  Sections: {len(elements['sections'])}", file=sys.stderr)
    print(f"  Figures: {len(elements['figures'])}", file=sys.stderr)
    print(f"  Equations: {len(elements['equations'])}", file=sys.stderr)
    print(f"  Tables: {len(elements['tables'])}", file=sys.stderr)

    if args.format == "json":
        output = json.dumps(elements, indent=2, ensure_ascii=False)
    else:
        output = generate_beamer(elements, theme=args.theme)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"Written to {args.output}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
