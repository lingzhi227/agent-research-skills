#!/usr/bin/env python3
"""Assemble final GitHub research report from all phase outputs.

Reads repo_db.jsonl and phase outputs to generate statistics and a comprehensive report.

Usage:
    python compile_github_report.py --topic-dir ./github-research-output/my-topic
"""

import argparse
import json
import math
import os
import sys
from datetime import datetime, timezone
from pathlib import Path


# -- I/O helpers --------------------------------------------------------------

def load_jsonl(path: str) -> list[dict]:
    """Load records from a JSONL file. Returns empty list if file missing."""
    records: list[dict] = []
    if not os.path.isfile(path):
        return records
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return records


def load_text(path: str) -> str:
    """Load a text file. Returns empty string if file missing."""
    if not os.path.isfile(path):
        return ""
    try:
        with open(path, encoding="utf-8") as f:
            return f.read()
    except OSError:
        return ""


def format_table(headers: list[str], rows: list[list[str]]) -> str:
    """Generate a markdown table from headers and row data."""
    if not headers:
        return ""
    lines: list[str] = []
    lines.append("| " + " | ".join(headers) + " |")
    # Alignment: right-align columns that look numeric in first data row
    seps: list[str] = []
    for i, h in enumerate(headers):
        if rows and i < len(rows[0]):
            try:
                float(str(rows[0][i]).replace(",", ""))
                seps.append("------:")
            except (ValueError, IndexError):
                seps.append("------")
        else:
            seps.append("------")
    lines.append("| " + " | ".join(seps) + " |")
    for row in rows:
        cells = [str(c) for c in row]
        while len(cells) < len(headers):
            cells.append("")
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def truncate(text: str, max_chars: int = 200) -> str:
    """Truncate text with ellipsis if it exceeds max_chars."""
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 3].rstrip() + "..."


# -- Statistics ---------------------------------------------------------------

def compute_stats(repos: list[dict]) -> dict:
    """Compute all statistics from repo records."""
    if not repos:
        return {
            "total_discovered": 0, "total_filtered": 0, "total_analyzed": 0,
            "sources": {}, "languages": {}, "stars": {},
            "activity": {}, "score_buckets": {}, "ml_frameworks": {}, "licenses": {},
        }

    now = datetime.now(timezone.utc)

    # -- By source --
    sources: dict[str, int] = {}
    for rec in repos:
        src = rec.get("source", "unknown")
        sources[src] = sources.get(src, 0) + 1

    # -- By language --
    languages: dict[str, int] = {}
    for rec in repos:
        lang = rec.get("language") or "Unknown"
        languages[lang] = languages.get(lang, 0) + 1
    languages = dict(sorted(languages.items(), key=lambda x: -x[1]))

    # -- Stars distribution --
    star_values = [rec.get("stars", 0) or 0 for rec in repos]
    star_values_sorted = sorted(star_values)
    n = len(star_values_sorted)
    stars_info: dict[str, float | int] = {
        "min": star_values_sorted[0],
        "max": star_values_sorted[-1],
        "median": star_values_sorted[n // 2] if n % 2 else
                  (star_values_sorted[n // 2 - 1] + star_values_sorted[n // 2]) / 2,
        "mean": round(sum(star_values) / n, 1),
        "p25": star_values_sorted[max(n // 4 - 1, 0)],
        "p75": star_values_sorted[min(3 * n // 4, n - 1)],
    }

    # -- Activity --
    activity: dict[str, int] = {"last_90d": 0, "last_year": 0, "older": 0}
    for rec in repos:
        pushed_str = rec.get("pushed_at") or rec.get("updated_at") or ""
        if not pushed_str:
            activity["older"] += 1
            continue
        try:
            pushed = datetime.fromisoformat(pushed_str.replace("Z", "+00:00"))
            days = (now - pushed).days
            if days <= 90:
                activity["last_90d"] += 1
            elif days <= 365:
                activity["last_year"] += 1
            else:
                activity["older"] += 1
        except (ValueError, TypeError):
            activity["older"] += 1

    # -- Composite score histogram --
    score_buckets: dict[str, int] = {
        "0.0-0.2": 0, "0.2-0.4": 0, "0.4-0.6": 0, "0.6-0.8": 0, "0.8-1.0": 0,
    }
    for rec in repos:
        cs = rec.get("composite_score", 0.0) or 0.0
        if cs >= 0.8:
            score_buckets["0.8-1.0"] += 1
        elif cs >= 0.6:
            score_buckets["0.6-0.8"] += 1
        elif cs >= 0.4:
            score_buckets["0.4-0.6"] += 1
        elif cs >= 0.2:
            score_buckets["0.2-0.4"] += 1
        else:
            score_buckets["0.0-0.2"] += 1

    # -- ML frameworks --
    ml_keywords = {
        "torch": "PyTorch", "pytorch": "PyTorch",
        "tensorflow": "TensorFlow", "tf-": "TensorFlow",
        "jax": "JAX", "flax": "JAX",
        "keras": "Keras", "sklearn": "scikit-learn",
        "transformers": "HuggingFace Transformers",
        "lightning": "PyTorch Lightning", "paddle": "PaddlePaddle",
    }
    ml_frameworks: dict[str, int] = {}
    for rec in repos:
        topics = rec.get("topics", []) or []
        desc = (rec.get("description") or "").lower()
        readme = (rec.get("readme_excerpt") or "").lower()
        combined = desc + " " + readme + " " + " ".join(str(t) for t in topics)
        found_for_repo: set[str] = set()
        for kw, framework in ml_keywords.items():
            if kw in combined:
                found_for_repo.add(framework)
        for fw in found_for_repo:
            ml_frameworks[fw] = ml_frameworks.get(fw, 0) + 1
    ml_frameworks = dict(sorted(ml_frameworks.items(), key=lambda x: -x[1]))

    # -- Licenses --
    licenses: dict[str, int] = {}
    for rec in repos:
        lic = rec.get("license") or "None/Unknown"
        if isinstance(lic, dict):
            lic = lic.get("spdx_id") or lic.get("name") or "None/Unknown"
        licenses[lic] = licenses.get(lic, 0) + 1
    licenses = dict(sorted(licenses.items(), key=lambda x: -x[1]))

    # -- Counts for filtered / analyzed --
    scored_repos = [r for r in repos if r.get("composite_score")]
    analyzed_repos = [r for r in repos if r.get("tags") and "deep-dived" in r.get("tags", [])]
    # Fallback: count repos with rank field as proxy for filtered
    ranked_repos = [r for r in repos if r.get("rank")]

    return {
        "total_discovered": len(repos),
        "total_filtered": len(ranked_repos) if ranked_repos else len(scored_repos),
        "total_analyzed": len(analyzed_repos),
        "num_sources": len(sources),
        "sources": sources,
        "languages": languages,
        "stars": stars_info,
        "activity": activity,
        "score_buckets": score_buckets,
        "ml_frameworks": ml_frameworks,
        "licenses": licenses,
    }


# -- Report sections ----------------------------------------------------------

def build_header(topic_dir: str) -> str:
    """Build the report header with topic name and date."""
    slug = os.path.basename(topic_dir.rstrip("/"))
    topic = slug.replace("-", " ").title()
    date = datetime.now().strftime("%Y-%m-%d %H:%M")
    return f"# GitHub Research Report: {topic}\n\nGenerated: {date}\n"


def build_executive_summary(stats: dict, blueprint_summary: str) -> str:
    """Build the executive summary section."""
    lines = ["## Executive Summary\n"]
    if blueprint_summary:
        lines.append(blueprint_summary.strip())
    else:
        total = stats["total_discovered"]
        ns = stats["num_sources"]
        filtered = stats["total_filtered"]
        analyzed = stats["total_analyzed"]
        top_lang = next(iter(stats["languages"]), "N/A")
        active = stats["activity"].get("last_90d", 0)
        lines.append(
            f"This report covers a systematic GitHub research effort that discovered "
            f"**{total} repositories** from **{ns} source(s)**. "
            f"After scoring and filtering, **{filtered}** repos were shortlisted "
            f"and **{analyzed or 'several'}** received deep code analysis. "
            f"The dominant language is **{top_lang}** and "
            f"**{active}** repos have been active in the last 90 days."
        )
    lines.append("")
    return "\n".join(lines)


def build_discovery_stats(stats: dict) -> str:
    """Build the discovery statistics section."""
    lines = ["## 1. Discovery Statistics\n"]
    lines.append(
        f"- Repos discovered: **{stats['total_discovered']}** "
        f"from **{stats['num_sources']}** sources"
    )
    lines.append(
        f"- After filtering: **{stats['total_filtered']}** repos "
        f"(top by composite score)"
    )
    lines.append(f"- Deep-dived: **{stats['total_analyzed']}** repos\n")

    # Source table
    if stats["sources"]:
        lines.append("### Repos by Source\n")
        rows = [[src, str(cnt)] for src, cnt in
                sorted(stats["sources"].items(), key=lambda x: -x[1])]
        lines.append(format_table(["Source", "Count"], rows))
        lines.append("")

    # Language table
    if stats["languages"]:
        lines.append("### Repos by Language\n")
        rows = [[lang, str(cnt)] for lang, cnt in list(stats["languages"].items())[:15]]
        lines.append(format_table(["Language", "Count"], rows))
        lines.append("")

    # Stars distribution
    stars = stats.get("stars", {})
    if stars:
        lines.append("### Stars Distribution\n")
        lines.append(f"- Min: **{stars.get('min', 0)}** | "
                     f"Max: **{stars.get('max', 0)}** | "
                     f"Median: **{stars.get('median', 0)}** | "
                     f"Mean: **{stars.get('mean', 0)}**")
        lines.append(f"- P25: **{stars.get('p25', 0)}** | P75: **{stars.get('p75', 0)}**\n")

    # Score buckets
    if stats["score_buckets"]:
        lines.append("### Composite Score Distribution\n")
        rows = [[bucket, str(cnt)] for bucket, cnt in stats["score_buckets"].items()]
        lines.append(format_table(["Score Range", "Count"], rows))
        lines.append("")

    # Activity
    if stats["activity"]:
        lines.append("### Activity\n")
        act = stats["activity"]
        lines.append(f"- Pushed in last 90 days: **{act.get('last_90d', 0)}**")
        lines.append(f"- Pushed in last year: **{act.get('last_year', 0)}**")
        lines.append(f"- Older / unknown: **{act.get('older', 0)}**\n")

    # ML frameworks
    if stats["ml_frameworks"]:
        lines.append("### ML Frameworks\n")
        rows = [[fw, str(cnt)] for fw, cnt in stats["ml_frameworks"].items()]
        lines.append(format_table(["Framework", "Repos"], rows))
        lines.append("")

    # Licenses
    if stats["licenses"]:
        lines.append("### License Distribution\n")
        rows = [[lic, str(cnt)] for lic, cnt in list(stats["licenses"].items())[:10]]
        lines.append(format_table(["License", "Count"], rows))
        lines.append("")

    return "\n".join(lines)


def build_top_repos(ranked_repos: list[dict]) -> str:
    """Build the top repositories table from ranked_repos.jsonl."""
    lines = ["## 2. Top Repositories\n"]
    if not ranked_repos:
        lines.append("_No ranked repos available._\n")
        return "\n".join(lines)

    headers = ["Rank", "Repo", "Stars", "Language", "Composite", "Description"]
    rows: list[list[str]] = []
    for i, rec in enumerate(ranked_repos[:30], 1):
        rid = rec.get("repo_id", "")
        url = rec.get("url", f"https://github.com/{rid}")
        stars = str(rec.get("stars", 0))
        lang = rec.get("language", "")
        score = f"{(rec.get('composite_score', 0.0) or 0.0):.3f}"
        desc = truncate((rec.get("description") or "").replace("|", "/"), 60)
        rows.append([str(i), f"[{rid}]({url})", stars, lang, score, desc])

    lines.append(format_table(headers, rows))
    lines.append("")
    return "\n".join(lines)


def build_deep_analysis_summaries(analyses_dir: str) -> str:
    """Build condensed summaries from per-repo analyses/*.md files."""
    lines = ["## 3. Deep Analysis Summaries\n"]
    if not os.path.isdir(analyses_dir):
        lines.append("_No deep analysis files found._\n")
        return "\n".join(lines)

    analysis_files = sorted(
        f for f in os.listdir(analyses_dir) if f.endswith("_analysis.md")
    )
    if not analysis_files:
        lines.append("_No per-repo analysis files found._\n")
        return "\n".join(lines)

    for fname in analysis_files:
        content = load_text(os.path.join(analyses_dir, fname))
        if not content:
            continue
        # Extract repo name from filename
        repo_name = fname.removesuffix("_analysis.md")
        lines.append(f"### {repo_name}\n")
        # Include the first ~600 chars as a condensed summary
        lines.append(truncate(content.strip(), 600))
        lines.append("")

    return "\n".join(lines)


def build_section(title: str, content: str) -> str:
    """Wrap phase content in a section. Return empty section note if no content."""
    lines = [f"{title}\n"]
    if content.strip():
        lines.append(content.strip())
    else:
        heading_text = title.lstrip("#").strip()
        lines.append(f"_{heading_text} not available._")
    lines.append("")
    return "\n".join(lines)


def build_appendix(repos: list[dict]) -> str:
    """Build the full repo database appendix table."""
    lines = ["## Appendix A: Full Repo Database\n"]
    if not repos:
        lines.append("_No repos in database._\n")
        return "\n".join(lines)

    sorted_repos = sorted(repos, key=lambda r: -(r.get("composite_score", 0) or 0))
    headers = ["Repo", "Stars", "Language", "Score", "Source", "Description"]
    rows: list[list[str]] = []
    for rec in sorted_repos:
        rid = rec.get("repo_id", "")
        url = rec.get("url", f"https://github.com/{rid}")
        stars = str(rec.get("stars", 0))
        lang = rec.get("language", "")
        score = f"{(rec.get('composite_score', 0.0) or 0.0):.3f}"
        src = rec.get("source", "")
        desc = truncate((rec.get("description") or "").replace("|", "/"), 60)
        rows.append([f"[{rid}]({url})", stars, lang, score, src, desc])

    lines.append(format_table(headers, rows))
    lines.append("")
    return "\n".join(lines)


def build_methodology() -> str:
    """Build the methodology appendix."""
    return """## Appendix B: Methodology

- **Phase 1: Intake** -- Parse deep-research output for GitHub URLs, paper references, and search keywords
- **Phase 2: Discovery** -- Multi-source search (GitHub repo search, Papers With Code, GitHub code search, direct URLs)
- **Phase 3: Scoring & Filtering** -- Composite score = relevance x 0.4 + quality x 0.35 + activity x 0.25; select top repos
- **Phase 4: Deep Dive** -- Shallow clone + deep code reading of top repos (architecture, algorithms, quality, reusability)
- **Phase 5: Cross-Repo Analysis** -- Comparison matrix, technique-to-code mapping, gap analysis
- **Phase 6: Integration Blueprint** -- Recommended architecture, reuse catalog, license compatibility, effort estimates
"""


# -- Main ---------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Assemble final GitHub research report from all phase outputs."
    )
    parser.add_argument(
        "--topic-dir", required=True,
        help="Path to the github-research-output/{slug}/ directory",
    )
    args = parser.parse_args()

    topic_dir = args.topic_dir.rstrip("/")
    if not os.path.isdir(topic_dir):
        print(f"[error] topic directory not found: {topic_dir}", file=sys.stderr)
        sys.exit(1)

    print(f"[compile] loading data from {topic_dir}", file=sys.stderr)

    # -- Load repo database --
    repo_db_path = os.path.join(topic_dir, "repo_db.jsonl")
    all_repos = load_jsonl(repo_db_path)
    print(f"  repo_db.jsonl: {len(all_repos)} repos", file=sys.stderr)

    # -- Load ranked repos --
    ranked_path = os.path.join(topic_dir, "phase3_filtering", "ranked_repos.jsonl")
    ranked_repos = load_jsonl(ranked_path)
    print(f"  ranked_repos.jsonl: {len(ranked_repos)} repos", file=sys.stderr)

    # -- Load phase text outputs --
    phase_paths = {
        "intake_summary":    os.path.join(topic_dir, "phase1_intake", "intake_summary.md"),
        "discovery_log":     os.path.join(topic_dir, "phase2_discovery", "discovery_log.md"),
        "filtering_report":  os.path.join(topic_dir, "phase3_filtering", "filtering_report.md"),
        "deep_dive_summary": os.path.join(topic_dir, "phase4_deep_dive", "deep_dive_summary.md"),
        "comparison_matrix": os.path.join(topic_dir, "phase5_analysis", "comparison_matrix.md"),
        "technique_map":     os.path.join(topic_dir, "phase5_analysis", "technique_map.md"),
        "analysis_report":   os.path.join(topic_dir, "phase5_analysis", "analysis_report.md"),
        "integration_plan":  os.path.join(topic_dir, "phase6_blueprint", "integration_plan.md"),
        "reuse_catalog":     os.path.join(topic_dir, "phase6_blueprint", "reuse_catalog.md"),
        "blueprint_summary": os.path.join(topic_dir, "phase6_blueprint", "blueprint_summary.md"),
    }

    phases: dict[str, str] = {}
    for key, path in phase_paths.items():
        phases[key] = load_text(path)
        status = "loaded" if phases[key] else "not found"
        print(f"  {key}: {status}", file=sys.stderr)

    analyses_dir = os.path.join(topic_dir, "phase4_deep_dive", "analyses")

    # -- Compute statistics --
    stats = compute_stats(all_repos)
    # Override total_filtered with actual ranked count if available
    if ranked_repos:
        stats["total_filtered"] = len(ranked_repos)
    # Count analysis files for total_analyzed
    if os.path.isdir(analyses_dir):
        analysis_count = sum(
            1 for f in os.listdir(analyses_dir) if f.endswith("_analysis.md")
        )
        if analysis_count > 0:
            stats["total_analyzed"] = analysis_count

    print(f"[compile] assembling report...", file=sys.stderr)

    # -- Assemble report --
    sections: list[str] = [
        build_header(topic_dir),
        "---\n",
        build_executive_summary(stats, phases["blueprint_summary"]),
        build_discovery_stats(stats),
        build_top_repos(ranked_repos if ranked_repos else all_repos),
        build_deep_analysis_summaries(analyses_dir),
        build_section("## 4. Cross-Repository Comparison", phases["comparison_matrix"]),
        build_section("## 5. Technique-to-Code Mapping", phases["technique_map"]),
        build_section("## 6. Integration Blueprint", phases["integration_plan"]),
        build_section("## 7. Reusable Components", phases["reuse_catalog"]),
        build_appendix(all_repos),
        build_methodology(),
    ]

    report = "\n".join(sections)

    # -- Write outputs --
    output_dir = os.path.join(topic_dir, "phase6_blueprint")
    os.makedirs(output_dir, exist_ok=True)

    report_path = os.path.join(output_dir, "final_report.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)

    stats_path = os.path.join(output_dir, "stats.json")
    with open(stats_path, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)

    # -- Summary --
    section_count = sum(1 for s in sections if s.strip().startswith("##"))
    print(
        f"\nReport compiled: {section_count} sections, "
        f"{stats['total_discovered']} repos, "
        f"{stats['total_analyzed']} analyzed",
        file=sys.stderr,
    )
    print(f"  -> {report_path}", file=sys.stderr)
    print(f"  -> {stats_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
