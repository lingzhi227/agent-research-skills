#!/usr/bin/env python3
"""Format p-values for academic papers.

Formats p-values with proper precision, significance stars,
and LaTeX-compatible output.

Self-contained: uses only stdlib.

Extracted from data-to-paper's pvalue.py formatting utilities.

Usage:
    python format_pvalue.py --values "0.001 0.05 0.23" --format stars
    python format_pvalue.py --values "0.0001 0.03 0.5" --format latex
    python format_pvalue.py --values "1e-8 0.01 0.1" --format text
    python format_pvalue.py --csv results.csv --column pvalue --format stars
"""

import argparse
import csv
import json
import sys

P_VALUE_MIN = 1e-6
DEFAULT_LEVELS = (0.05, 0.01, 0.001)


def format_p_value(p: float, min_val: float = P_VALUE_MIN,
                   smaller_than: str = "<") -> str:
    """Format a p-value to a string with appropriate precision."""
    if not isinstance(p, (int, float)):
        return str(p)
    if p < 0 or p > 1:
        return f"invalid({p})"
    if p >= min_val:
        return f"{p:.3g}"
    return f"{smaller_than}{min_val}"


def format_p_value_latex(p: float, min_val: float = P_VALUE_MIN) -> str:
    """Format a p-value for LaTeX output."""
    if p >= min_val:
        return f"${p:.3g}$"
    return f"$<${min_val}"


def p_to_stars(p: float, levels: tuple = DEFAULT_LEVELS) -> str:
    """Convert p-value to significance stars.

    Default levels: * p<0.05, ** p<0.01, *** p<0.001
    """
    if p < levels[2]:
        return "***"
    if p < levels[1]:
        return "**"
    if p < levels[0]:
        return "*"
    return "ns"


def stars_legend(levels: tuple = DEFAULT_LEVELS) -> str:
    """Generate a legend string for significance stars."""
    parts = [f"ns p >= {levels[0]}"]
    symbols = ["*", "**", "***"]
    for i, level in enumerate(levels):
        parts.append(f"{symbols[i]} p < {level}")
    return ", ".join(parts)


def format_comparison(name1: str, name2: str, p: float,
                      fmt: str = "text") -> str:
    """Format a comparison result with p-value."""
    if fmt == "stars":
        return f"{name1} vs {name2}: p={format_p_value(p)} {p_to_stars(p)}"
    elif fmt == "latex":
        star = p_to_stars(p)
        pstr = format_p_value_latex(p)
        return f"{name1} vs {name2}: {pstr} {star}"
    else:
        return f"{name1} vs {name2}: p={format_p_value(p)}"


def main():
    parser = argparse.ArgumentParser(description="Format p-values for academic papers")
    parser.add_argument("--values", help="Space-separated p-values")
    parser.add_argument("--csv", help="CSV file with p-values")
    parser.add_argument("--column", default="pvalue", help="Column name in CSV (default: pvalue)")
    parser.add_argument("--format", choices=["text", "stars", "latex", "json"],
                        default="text", help="Output format (default: text)")
    parser.add_argument("--levels", help="Significance levels (comma-separated, default: 0.05,0.01,0.001)")
    parser.add_argument("--output", "-o", help="Output file")
    args = parser.parse_args()

    levels = DEFAULT_LEVELS
    if args.levels:
        levels = tuple(float(x) for x in args.levels.split(","))

    p_values = []

    if args.values:
        for v in args.values.split():
            try:
                p_values.append(float(v))
            except ValueError:
                print(f"Warning: skipping invalid value '{v}'", file=sys.stderr)
    elif args.csv:
        with open(args.csv, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    p_values.append(float(row[args.column]))
                except (ValueError, KeyError):
                    pass
    else:
        print("Error: specify --values or --csv", file=sys.stderr)
        sys.exit(1)

    if not p_values:
        print("No valid p-values found.", file=sys.stderr)
        sys.exit(1)

    results = []
    for p in p_values:
        entry = {"p_value": p}
        entry["formatted"] = format_p_value(p)
        entry["stars"] = p_to_stars(p, levels)
        entry["latex"] = format_p_value_latex(p)
        results.append(entry)

    output_lines = []
    if args.format == "json":
        output_lines.append(json.dumps(results, indent=2))
    elif args.format == "stars":
        for r in results:
            output_lines.append(f"p={r['formatted']}  {r['stars']}")
        output_lines.append(f"\nLegend: {stars_legend(levels)}")
    elif args.format == "latex":
        for r in results:
            output_lines.append(f"{r['latex']}  {r['stars']}")
    else:
        for r in results:
            output_lines.append(f"p = {r['formatted']}")

    text = "\n".join(output_lines) + "\n"
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"Written to {args.output}", file=sys.stderr)
    else:
        sys.stdout.write(text)


if __name__ == "__main__":
    main()
