#!/usr/bin/env python3
"""Statistical summary and comparison of experimental results.

Takes experiment results in CSV/JSON, detects data types, recommends
statistical tests, runs comparisons, and outputs formatted results.

Requires: numpy, scipy

Usage:
    python stat_summary.py --input results.csv --compare method --metric accuracy --output summary.json
    python stat_summary.py --input results.json --compare model --metric f1_score
    python stat_summary.py --input results.csv --describe
"""

import argparse
import csv
import json
import math
import os
import sys

try:
    import numpy as np
    from scipy import stats
except ImportError:
    print("Error: numpy and scipy required. Install: pip install numpy scipy", file=sys.stderr)
    sys.exit(1)


def load_data(path: str) -> list[dict]:
    """Load data from CSV or JSON."""
    ext = os.path.splitext(path)[1].lower()
    if ext == ".csv":
        with open(path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            return list(reader)
    elif ext == ".json":
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return data
        raise ValueError("JSON must be a list of records")
    else:
        raise ValueError(f"Unsupported format: {ext}")


def detect_numeric_columns(data: list[dict]) -> list[str]:
    """Detect which columns contain numeric data."""
    if not data:
        return []
    numeric = []
    for key in data[0].keys():
        try:
            vals = [float(row[key]) for row in data if row.get(key, "") != ""]
            if len(vals) > len(data) * 0.5:
                numeric.append(key)
        except (ValueError, TypeError):
            pass
    return numeric


def get_column_values(data: list[dict], col: str) -> list[float]:
    """Extract numeric values from a column."""
    vals = []
    for row in data:
        try:
            vals.append(float(row[col]))
        except (ValueError, TypeError, KeyError):
            pass
    return vals


def describe_column(values: list[float]) -> dict:
    """Compute descriptive statistics for a numeric column."""
    arr = np.array(values)
    return {
        "count": len(arr),
        "mean": float(np.mean(arr)),
        "std": float(np.std(arr, ddof=1)) if len(arr) > 1 else 0.0,
        "min": float(np.min(arr)),
        "q25": float(np.percentile(arr, 25)),
        "median": float(np.median(arr)),
        "q75": float(np.percentile(arr, 75)),
        "max": float(np.max(arr)),
    }


def recommend_test(groups: list[list[float]]) -> str:
    """Recommend a statistical test based on the data."""
    n_groups = len(groups)
    if n_groups < 2:
        return "none"

    # Check normality (Shapiro-Wilk for each group)
    all_normal = True
    for g in groups:
        if len(g) < 3:
            all_normal = False
            break
        if len(g) <= 5000:
            _, p = stats.shapiro(g)
            if p < 0.05:
                all_normal = False
                break

    if n_groups == 2:
        # Check if paired (same length)
        if len(groups[0]) == len(groups[1]):
            return "paired_ttest" if all_normal else "wilcoxon"
        return "independent_ttest" if all_normal else "mann_whitney"
    else:
        return "anova" if all_normal else "kruskal_wallis"


def run_comparison(groups: dict[str, list[float]], test: str) -> dict:
    """Run a statistical comparison between groups."""
    group_names = list(groups.keys())
    group_values = list(groups.values())

    result = {
        "test": test,
        "groups": {name: describe_column(vals) for name, vals in groups.items()},
    }

    if test == "independent_ttest" and len(group_values) == 2:
        stat, p = stats.ttest_ind(group_values[0], group_values[1])
        result["statistic"] = float(stat)
        result["p_value"] = float(p)

    elif test == "paired_ttest" and len(group_values) == 2:
        stat, p = stats.ttest_rel(group_values[0], group_values[1])
        result["statistic"] = float(stat)
        result["p_value"] = float(p)

    elif test == "mann_whitney" and len(group_values) == 2:
        stat, p = stats.mannwhitneyu(group_values[0], group_values[1], alternative='two-sided')
        result["statistic"] = float(stat)
        result["p_value"] = float(p)

    elif test == "wilcoxon" and len(group_values) == 2:
        stat, p = stats.wilcoxon(group_values[0], group_values[1])
        result["statistic"] = float(stat)
        result["p_value"] = float(p)

    elif test == "anova":
        stat, p = stats.f_oneway(*group_values)
        result["statistic"] = float(stat)
        result["p_value"] = float(p)

    elif test == "kruskal_wallis":
        stat, p = stats.kruskal(*group_values)
        result["statistic"] = float(stat)
        result["p_value"] = float(p)

    # Effect size (Cohen's d for two groups)
    if len(group_values) == 2:
        n1, n2 = len(group_values[0]), len(group_values[1])
        m1, m2 = np.mean(group_values[0]), np.mean(group_values[1])
        s1, s2 = np.std(group_values[0], ddof=1), np.std(group_values[1], ddof=1)
        pooled_std = math.sqrt(((n1 - 1) * s1**2 + (n2 - 1) * s2**2) / (n1 + n2 - 2))
        if pooled_std > 0:
            result["cohens_d"] = float((m1 - m2) / pooled_std)

    # Significance stars
    if "p_value" in result:
        p = result["p_value"]
        if p < 0.001:
            result["significance"] = "***"
        elif p < 0.01:
            result["significance"] = "**"
        elif p < 0.05:
            result["significance"] = "*"
        else:
            result["significance"] = "ns"

    return result


def pairwise_comparisons(groups: dict[str, list[float]]) -> list[dict]:
    """Run pairwise comparisons between all groups."""
    names = list(groups.keys())
    results = []
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            pair = {names[i]: groups[names[i]], names[j]: groups[names[j]]}
            test = recommend_test(list(pair.values()))
            comp = run_comparison(pair, test)
            comp["pair"] = [names[i], names[j]]
            results.append(comp)
    return results


def main():
    parser = argparse.ArgumentParser(description="Statistical summary of experimental results")
    parser.add_argument("--input", required=True, help="Input file (.csv or .json)")
    parser.add_argument("--compare", help="Column to group by for comparison")
    parser.add_argument("--metric", help="Metric column to compare")
    parser.add_argument("--describe", action="store_true", help="Show descriptive statistics only")
    parser.add_argument("--pairwise", action="store_true", help="Run all pairwise comparisons")
    parser.add_argument("--output", "-o", help="Output JSON file")
    args = parser.parse_args()

    data = load_data(args.input)
    if not data:
        print("No data loaded.", file=sys.stderr)
        sys.exit(1)

    numeric_cols = detect_numeric_columns(data)

    if args.describe:
        result = {"columns": {}}
        for col in numeric_cols:
            vals = get_column_values(data, col)
            result["columns"][col] = describe_column(vals)
        print(f"Descriptive statistics for {len(numeric_cols)} numeric columns:", file=sys.stderr)
    elif args.compare and args.metric:
        # Group by compare column
        groups = {}
        for row in data:
            group = str(row.get(args.compare, "unknown"))
            val = row.get(args.metric)
            try:
                val = float(val)
            except (ValueError, TypeError):
                continue
            groups.setdefault(group, []).append(val)

        if len(groups) < 2:
            print(f"Need at least 2 groups, found {len(groups)}", file=sys.stderr)
            sys.exit(1)

        test = recommend_test(list(groups.values()))
        print(f"Groups: {list(groups.keys())}", file=sys.stderr)
        print(f"Recommended test: {test}", file=sys.stderr)

        result = run_comparison(groups, test)

        if args.pairwise and len(groups) > 2:
            result["pairwise"] = pairwise_comparisons(groups)
    else:
        print("Error: specify --describe or both --compare and --metric", file=sys.stderr)
        sys.exit(1)

    output = json.dumps(result, indent=2, ensure_ascii=False)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"Written to {args.output}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
