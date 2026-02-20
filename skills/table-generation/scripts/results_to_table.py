#!/usr/bin/env python3
"""Convert experimental results to publication-quality LaTeX tables.

Self-contained: uses only stdlib.

Adapted from data-to-paper's df_to_latex and AI-Researcher's table patterns.

Usage:
    python results_to_table.py --input results.json --type comparison
    python results_to_table.py --input results.csv --type ablation --bold-best max
    python results_to_table.py --input results.json --type comparison \
        --caption "Main results" --label tab:main --bold-best max
"""

import argparse
import csv
import json
import os
import sys


def load_data(path: str) -> tuple[list[str], list[str], list[list[str]]]:
    """Load data from JSON or CSV. Returns (col_headers, row_headers, values)."""
    ext = os.path.splitext(path)[1].lower()

    if ext == ".json":
        with open(path, encoding="utf-8") as f:
            data = json.load(f)

        if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
            # List of dicts: [{method: X, metric1: Y, ...}, ...]
            col_headers = [k for k in data[0].keys() if k.lower() not in ("method", "model", "name", "variant")]
            method_key = next((k for k in data[0].keys() if k.lower() in ("method", "model", "name", "variant")), None)
            row_headers = [str(d.get(method_key, f"Row {i}")) for i, d in enumerate(data)] if method_key else [f"Row {i}" for i in range(len(data))]
            values = [[str(d.get(c, "")) for c in col_headers] for d in data]
        elif isinstance(data, dict):
            # Nested dict: {method: {metric: value, ...}, ...}
            row_headers = list(data.keys())
            all_cols = set()
            for v in data.values():
                if isinstance(v, dict):
                    all_cols.update(v.keys())
            col_headers = sorted(all_cols)
            values = [[str(data[r].get(c, "")) if isinstance(data[r], dict) else str(data[r]) for c in col_headers] for r in row_headers]
        else:
            raise ValueError(f"Unsupported JSON structure: expected list of dicts or nested dict")

    elif ext == ".csv":
        with open(path, encoding="utf-8") as f:
            reader = csv.reader(f)
            rows = list(reader)
        if len(rows) < 2:
            raise ValueError("CSV must have at least a header row and one data row")
        col_headers = rows[0][1:]  # Skip first column (method name)
        row_headers = [r[0] for r in rows[1:]]
        values = [r[1:] for r in rows[1:]]

    else:
        raise ValueError(f"Unsupported file format: {ext}. Use .json or .csv")

    return col_headers, row_headers, values


def parse_numeric(val: str) -> float | None:
    """Try to parse a numeric value, handling +/- notation."""
    val = val.strip()
    # Handle "84.2+/-0.4" or "84.2±0.4" or "84.2 +/- 0.4"
    for sep in ["±", "+/-", "+-"]:
        if sep in val:
            val = val.split(sep)[0].strip()
            break
    try:
        return float(val)
    except ValueError:
        return None


def find_best_indices(values: list[list[str]], col_headers: list[str],
                      bold_best: str) -> dict[int, int]:
    """Find the best value index in each column. Returns {col_idx: row_idx}."""
    best = {}
    if bold_best not in ("max", "min"):
        return best

    for col_idx in range(len(col_headers)):
        best_val = None
        best_row = None
        for row_idx in range(len(values)):
            if col_idx < len(values[row_idx]):
                num = parse_numeric(values[row_idx][col_idx])
                if num is not None:
                    if best_val is None:
                        best_val = num
                        best_row = row_idx
                    elif bold_best == "max" and num > best_val:
                        best_val = num
                        best_row = row_idx
                    elif bold_best == "min" and num < best_val:
                        best_val = num
                        best_row = row_idx
        if best_row is not None:
            best[col_idx] = best_row

    return best


def escape_latex(text: str) -> str:
    """Escape special LaTeX characters in text."""
    replacements = [
        ("_", r"\_"),
        ("%", r"\%"),
        ("&", r"\&"),
        ("#", r"\#"),
    ]
    for old, new in replacements:
        text = text.replace(old, new)
    # Convert +/- to $\pm$
    text = text.replace("±", "$\\pm$")
    text = text.replace("+/-", "$\\pm$")
    return text


def generate_comparison_table(col_headers, row_headers, values,
                              caption, label, bold_best, wide=False):
    """Generate a comparison table."""
    best = find_best_indices(values, col_headers, bold_best)

    # Determine alignment
    num_cols = len(col_headers)
    align = "l" + "c" * num_cols

    lines = []
    env = "table*" if wide else "table"
    lines.append(f"\\begin{{{env}}}[htbp]")
    lines.append("\\centering")
    if caption:
        lines.append(f"\\caption{{{escape_latex(caption)}}}")
    if label:
        lines.append(f"\\label{{{label}}}")
    lines.append(f"\\begin{{tabular}}{{{align}}}")
    lines.append("    \\toprule")

    # Header row
    header = "    Method & " + " & ".join(escape_latex(h) for h in col_headers) + " \\\\"
    lines.append(header)
    lines.append("    \\midrule")

    # Data rows
    for row_idx, (row_name, row_vals) in enumerate(zip(row_headers, values)):
        cells = [escape_latex(row_name)]
        for col_idx, val in enumerate(row_vals):
            val_str = escape_latex(val)
            if best.get(col_idx) == row_idx:
                val_str = f"\\textbf{{{val_str}}}"
            cells.append(val_str)
        lines.append("    " + " & ".join(cells) + " \\\\")

    lines.append("    \\bottomrule")
    lines.append("\\end{tabular}")
    lines.append(f"\\end{{{env}}}")

    return "\n".join(lines)


def generate_ablation_table(col_headers, row_headers, values,
                            caption, label, bold_best):
    """Generate an ablation table (first row assumed to be full model)."""
    best = find_best_indices(values, col_headers, bold_best)

    num_cols = len(col_headers)
    align = "l" + "c" * num_cols

    lines = []
    lines.append("\\begin{table}[htbp]")
    lines.append("\\centering")
    if caption:
        lines.append(f"\\caption{{{escape_latex(caption)}}}")
    if label:
        lines.append(f"\\label{{{label}}}")
    lines.append(f"\\begin{{tabular}}{{{align}}}")
    lines.append("    \\toprule")

    # Header
    header = "    Variant & " + " & ".join(escape_latex(h) for h in col_headers) + " \\\\"
    lines.append(header)
    lines.append("    \\midrule")

    # Data rows
    for row_idx, (row_name, row_vals) in enumerate(zip(row_headers, values)):
        cells = []
        name = escape_latex(row_name)
        if row_idx == 0:
            cells.append(name)
        else:
            cells.append(f"\\quad {name}")

        for col_idx, val in enumerate(row_vals):
            val_str = escape_latex(val)
            if best.get(col_idx) == row_idx:
                val_str = f"\\textbf{{{val_str}}}"
            cells.append(val_str)
        lines.append("    " + " & ".join(cells) + " \\\\")

    lines.append("    \\bottomrule")
    lines.append("\\end{tabular}")
    lines.append("\\end{table}")

    return "\n".join(lines)


def generate_descriptive_table(col_headers, row_headers, values,
                               caption, label):
    """Generate a descriptive/statistics table (no bolding)."""
    num_cols = len(col_headers)
    align = "l" + "r" * num_cols

    lines = []
    lines.append("\\begin{table}[htbp]")
    lines.append("\\centering")
    if caption:
        lines.append(f"\\caption{{{escape_latex(caption)}}}")
    if label:
        lines.append(f"\\label{{{label}}}")
    lines.append(f"\\begin{{tabular}}{{{align}}}")
    lines.append("    \\toprule")

    header = "    & " + " & ".join(escape_latex(h) for h in col_headers) + " \\\\"
    lines.append(header)
    lines.append("    \\midrule")

    for row_name, row_vals in zip(row_headers, values):
        cells = [escape_latex(row_name)]
        for val in row_vals:
            cells.append(escape_latex(val))
        lines.append("    " + " & ".join(cells) + " \\\\")

    lines.append("    \\bottomrule")
    lines.append("\\end{tabular}")
    lines.append("\\end{table}")

    return "\n".join(lines)


def find_second_best_indices(values, col_headers, bold_best):
    """Find the second-best value index in each column."""
    second = {}
    if bold_best not in ("max", "min"):
        return second
    best = find_best_indices(values, col_headers, bold_best)
    for col_idx in range(len(col_headers)):
        second_val = None
        second_row = None
        best_row = best.get(col_idx)
        for row_idx in range(len(values)):
            if row_idx == best_row:
                continue
            if col_idx < len(values[row_idx]):
                num = parse_numeric(values[row_idx][col_idx])
                if num is not None:
                    if second_val is None:
                        second_val = num
                        second_row = row_idx
                    elif bold_best == "max" and num > second_val:
                        second_val = num
                        second_row = row_idx
                    elif bold_best == "min" and num < second_val:
                        second_val = num
                        second_row = row_idx
        if second_row is not None:
            second[col_idx] = second_row
    return second


def generate_multi_dataset_table(col_headers, row_headers, values,
                                  caption, label, bold_best,
                                  underline_second=False):
    """Generate a multi-dataset table (methods x datasets x metrics)."""
    best = find_best_indices(values, col_headers, bold_best)
    second = find_second_best_indices(values, col_headers, bold_best) if underline_second else {}

    num_cols = len(col_headers)
    align = "l" + "c" * num_cols

    lines = []
    lines.append("\\begin{table*}[htbp]")
    lines.append("\\centering")
    if caption:
        lines.append(f"\\caption{{{escape_latex(caption)}}}")
    if label:
        lines.append(f"\\label{{{label}}}")
    lines.append(f"\\begin{{tabular}}{{{align}}}")
    lines.append("    \\toprule")

    header = "    Method & " + " & ".join(escape_latex(h) for h in col_headers) + " \\\\"
    lines.append(header)
    lines.append("    \\midrule")

    for row_idx, (row_name, row_vals) in enumerate(zip(row_headers, values)):
        cells = [escape_latex(row_name)]
        for col_idx, val in enumerate(row_vals):
            val_str = escape_latex(val)
            if best.get(col_idx) == row_idx:
                val_str = f"\\textbf{{{val_str}}}"
            elif second.get(col_idx) == row_idx and underline_second:
                val_str = f"\\underline{{{val_str}}}"
            cells.append(val_str)
        lines.append("    " + " & ".join(cells) + " \\\\")

    lines.append("    \\bottomrule")
    lines.append("\\end{tabular}")
    lines.append("\\end{table*}")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Convert results to LaTeX table")
    parser.add_argument("--input", required=True, help="Input file (.json or .csv)")
    parser.add_argument("--type", choices=["comparison", "ablation", "descriptive", "multi-dataset"],
                        default="comparison", help="Table type (default: comparison)")
    parser.add_argument("--bold-best", choices=["max", "min", "none"],
                        default="none", help="Bold best values (default: none)")
    parser.add_argument("--caption", type=str, default="", help="Table caption")
    parser.add_argument("--label", type=str, default="", help="Table label (e.g., tab:main)")
    parser.add_argument("--wide", action="store_true", help="Use table* for two-column layout")
    parser.add_argument("--output", type=str, help="Output .tex file (default: stdout)")
    parser.add_argument("--significance", action="store_true", help="Add p-value significance stars")
    parser.add_argument("--underline-second", action="store_true", help="Underline second-best results")
    args = parser.parse_args()

    col_headers, row_headers, values = load_data(args.input)

    if args.type == "comparison":
        latex = generate_comparison_table(
            col_headers, row_headers, values,
            args.caption, args.label, args.bold_best, args.wide
        )
    elif args.type == "ablation":
        latex = generate_ablation_table(
            col_headers, row_headers, values,
            args.caption, args.label, args.bold_best
        )
    elif args.type == "descriptive":
        latex = generate_descriptive_table(
            col_headers, row_headers, values,
            args.caption, args.label
        )
    elif args.type == "multi-dataset":
        latex = generate_multi_dataset_table(
            col_headers, row_headers, values,
            args.caption, args.label, args.bold_best,
            underline_second=args.underline_second
        )

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(latex)
        print(f"Table written to {args.output}", file=sys.stderr)
    else:
        print(latex)


if __name__ == "__main__":
    main()
