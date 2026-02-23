#!/usr/bin/env python3
"""JSONL GitHub repo database management.

Subcommands: merge, filter, score, search, tag, stats, export, rank.
Deduplication by exact repo_id (owner/name) match.

Usage:
    python repo_db.py merge --inputs a.jsonl b.jsonl --output merged.jsonl
    python repo_db.py filter --input db.jsonl --output filtered.jsonl --min-stars 100
    python repo_db.py score --input db.jsonl --output scored.jsonl
    python repo_db.py search --input db.jsonl --query "transformer"
    python repo_db.py tag --input db.jsonl --ids owner/name --tags impl baseline
    python repo_db.py stats --input db.jsonl
    python repo_db.py export --input db.jsonl --format markdown
    python repo_db.py rank --input db.jsonl --output ranked.jsonl --by composite_score
"""

import argparse
import csv
import io
import json
import math
import os
import re
import sys
from datetime import datetime, timezone


# -- I/O helpers --------------------------------------------------------------

def load_jsonl(path: str) -> list[dict]:
    """Load records from a JSONL file."""
    records = []
    if not os.path.exists(path):
        return records
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def save_jsonl(records: list[dict], path: str):
    """Save records to a JSONL file."""
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def deduplicate(records: list[dict]) -> list[dict]:
    """Remove duplicate repos by exact repo_id match. Later entries win."""
    seen: dict[str, int] = {}
    for i, rec in enumerate(records):
        rid = rec.get("repo_id", "")
        if rid:
            seen[rid] = i
    # Preserve order of last occurrence
    indices = sorted(seen.values())
    return [records[i] for i in indices]


# -- Scoring ------------------------------------------------------------------

def _sigmoid(x: float) -> float:
    """Sigmoid with steepness 5 centered at 0.5."""
    return 1.0 / (1.0 + math.exp(-5.0 * (x - 0.5)))


def _parse_iso(dt_str: str | None) -> datetime | None:
    """Parse an ISO-8601 datetime string."""
    if not dt_str:
        return None
    # Handle trailing Z and optional fractional seconds
    dt_str = dt_str.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(dt_str)
    except (ValueError, TypeError):
        return None


def compute_activity_score(rec: dict, now: datetime) -> float:
    """Compute activity score in [0, 1]."""
    pushed = _parse_iso(rec.get("pushed_at"))
    if pushed is None:
        return _sigmoid(0.0)

    days_since_push = max((now - pushed).days, 0)
    recent_push = 1.0 if days_since_push < 90 else 0.0
    has_recent_commits = 1.0 if days_since_push < 180 else 0.0

    stars = max(rec.get("stars", 0), 1)
    open_issues = rec.get("open_issues", 0)
    ratio = min(open_issues / stars, 1.0)
    issues_component = 1.0 - ratio  # lower ratio is better

    raw = recent_push * 0.4 + has_recent_commits * 0.3 + issues_component * 0.3
    return _sigmoid(raw)


def compute_quality_score(rec: dict) -> float:
    """Compute quality score in [0, 1]."""
    stars = rec.get("stars", 0)
    forks = rec.get("forks", 0)

    # Normalize log components: log(x+1) / log(100001) gives ~0-1 for 0-100k
    max_log = math.log(100001)
    star_comp = min(math.log(stars + 1) / max_log, 1.0) * 0.3
    fork_comp = min(math.log(forks + 1) / max_log, 1.0) * 0.2

    has_license = 0.15 if rec.get("license") else 0.0
    has_readme = 0.15 if rec.get("readme_excerpt") else 0.0
    not_archived = 0.2 if not rec.get("archived", False) else 0.0

    raw = star_comp + fork_comp + has_license + has_readme + not_archived
    return min(raw, 1.0)


def score_record(rec: dict, now: datetime) -> dict:
    """Compute all scores for a single record and return updated copy."""
    rec = dict(rec)
    rec["activity_score"] = round(compute_activity_score(rec, now), 4)
    rec["quality_score"] = round(compute_quality_score(rec), 4)

    relevance = rec.get("relevance_score", 0.0) or 0.0
    quality = rec["quality_score"]
    activity = rec["activity_score"]
    rec["composite_score"] = round(
        relevance * 0.4 + quality * 0.35 + activity * 0.25, 4
    )
    return rec


# -- Subcommand implementations -----------------------------------------------

def cmd_merge(args):
    """Merge multiple JSONL files with deduplication by repo_id."""
    all_records = []
    for path in args.inputs:
        records = load_jsonl(path)
        print(f"Loaded {len(records)} from {path}", file=sys.stderr)
        all_records.extend(records)

    merged = deduplicate(all_records)
    save_jsonl(merged, args.output)
    print(f"Merged: {len(all_records)} -> {len(merged)} unique repos -> {args.output}",
          file=sys.stderr)


def cmd_filter(args):
    """Filter repos by various criteria."""
    records = load_jsonl(args.input)
    kept = []

    for rec in records:
        if args.min_stars is not None and rec.get("stars", 0) < args.min_stars:
            continue
        if args.min_score is not None and rec.get("composite_score", 0.0) < args.min_score:
            continue
        if args.language and rec.get("language", "").lower() != args.language.lower():
            continue
        if args.not_archived and rec.get("archived", False):
            continue
        kept.append(rec)

    # Sort by composite_score descending
    kept.sort(key=lambda r: -(r.get("composite_score", 0.0) or 0.0))

    if args.max_repos and args.max_repos > 0 and len(kept) > args.max_repos:
        kept = kept[:args.max_repos]

    save_jsonl(kept, args.output)
    print(f"Filtered: {len(records)} -> {len(kept)} repos -> {args.output}",
          file=sys.stderr)


def cmd_score(args):
    """Compute composite scores for all repos."""
    records = load_jsonl(args.input)
    now = datetime.now(timezone.utc)

    scored = [score_record(rec, now) for rec in records]
    save_jsonl(scored, args.output)
    print(f"Scored {len(scored)} repos -> {args.output}", file=sys.stderr)


def cmd_search(args):
    """Search repos by keyword match in a field."""
    records = load_jsonl(args.input)
    query_lower = args.query.lower()
    results = []

    for rec in records:
        value = rec.get(args.field, "")
        if isinstance(value, list):
            value = " ".join(str(v) for v in value)
        if query_lower in str(value).lower():
            results.append(rec)

    for rec in results:
        print(json.dumps(rec, ensure_ascii=False))
    print(f"Found {len(results)} matches", file=sys.stderr)


def cmd_tag(args):
    """Add tags to specific repos. Supports 'relevance:0.85' format."""
    records = load_jsonl(args.input)
    id_set = set(args.ids)
    tagged = 0

    # Separate relevance assignments from plain tags
    plain_tags = []
    relevance_val = None
    for t in args.tags:
        if t.startswith("relevance:"):
            try:
                relevance_val = float(t.split(":", 1)[1])
            except ValueError:
                plain_tags.append(t)
        else:
            plain_tags.append(t)

    for rec in records:
        rid = rec.get("repo_id", "")
        if rid in id_set:
            if plain_tags:
                existing = rec.get("tags", [])
                rec["tags"] = sorted(set(existing + plain_tags))
            if relevance_val is not None:
                rec["relevance_score"] = relevance_val
            tagged += 1

    save_jsonl(records, args.input)
    msg_parts = []
    if plain_tags:
        msg_parts.append(f"tags={plain_tags}")
    if relevance_val is not None:
        msg_parts.append(f"relevance_score={relevance_val}")
    print(f"Tagged {tagged} repos with {', '.join(msg_parts)}", file=sys.stderr)


def cmd_stats(args):
    """Compute and print JSON summary statistics."""
    records = load_jsonl(args.input)
    if not records:
        print(json.dumps({"total": 0}, indent=2))
        return

    languages: dict[str, int] = {}
    sources: dict[str, int] = {}
    tags_dist: dict[str, int] = {}
    total_stars = 0
    total_forks = 0
    archived_count = 0
    with_readme = 0
    with_papers = 0
    scored_count = 0
    score_sum = 0.0

    for rec in records:
        lang = rec.get("language") or "Unknown"
        languages[lang] = languages.get(lang, 0) + 1

        src = rec.get("source", "unknown")
        sources[src] = sources.get(src, 0) + 1

        total_stars += rec.get("stars", 0)
        total_forks += rec.get("forks", 0)

        if rec.get("archived"):
            archived_count += 1
        if rec.get("readme_excerpt"):
            with_readme += 1
        if rec.get("paper_ids"):
            with_papers += 1

        cs = rec.get("composite_score", 0.0) or 0.0
        if cs > 0:
            scored_count += 1
            score_sum += cs

        for tag in rec.get("tags", []):
            tags_dist[tag] = tags_dist.get(tag, 0) + 1

    stats = {
        "total": len(records),
        "archived": archived_count,
        "with_readme": with_readme,
        "with_papers": with_papers,
        "total_stars": total_stars,
        "total_forks": total_forks,
        "avg_stars": round(total_stars / len(records), 1),
        "avg_composite_score": round(score_sum / scored_count, 4) if scored_count else 0.0,
        "languages": dict(sorted(languages.items(), key=lambda x: -x[1])[:15]),
        "sources": sources,
        "tags": tags_dist,
    }
    print(json.dumps(stats, indent=2))


def cmd_export(args):
    """Export database in csv, jsonl, or markdown format."""
    records = load_jsonl(args.input)
    if not records:
        print("No records to export.", file=sys.stderr)
        return

    fmt = args.format

    if fmt == "csv":
        output = _export_csv(records)
    elif fmt == "jsonl":
        output = "\n".join(json.dumps(r, ensure_ascii=False) for r in records) + "\n"
    elif fmt == "markdown":
        output = _export_markdown(records)
    else:
        print(f"Unknown format: {fmt}", file=sys.stderr)
        return

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"Exported {len(records)} repos to {args.output}", file=sys.stderr)
    else:
        print(output, end="")


def _export_csv(records: list[dict]) -> str:
    fields = [
        "repo_id", "name", "owner", "stars", "forks", "language", "license",
        "composite_score", "quality_score", "activity_score", "relevance_score",
        "topics", "tags", "archived", "source",
    ]
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=fields, extrasaction="ignore")
    writer.writeheader()
    for rec in records:
        row = dict(rec)
        if isinstance(row.get("topics"), list):
            row["topics"] = "; ".join(row["topics"])
        if isinstance(row.get("tags"), list):
            row["tags"] = "; ".join(row["tags"])
        writer.writerow(row)
    return buf.getvalue()


def _export_markdown(records: list[dict]) -> str:
    lines = ["| Repo | Stars | Language | Score | Description |",
             "|------|------:|----------|------:|-------------|"]
    for rec in records:
        rid = rec.get("repo_id", "")
        url = rec.get("url", f"https://github.com/{rid}")
        stars = rec.get("stars", 0)
        lang = rec.get("language", "")
        score = rec.get("composite_score", 0.0) or 0.0
        desc = (rec.get("description") or "")[:80]
        desc = desc.replace("|", "\\|")
        lines.append(f"| [{rid}]({url}) | {stars} | {lang} | {score:.3f} | {desc} |")
    return "\n".join(lines) + "\n"


def cmd_rank(args):
    """Rank repos by a given field descending."""
    records = load_jsonl(args.input)
    # Map CLI choice to actual record field name
    field_map = {
        "composite_score": "composite_score",
        "stars": "stars",
        "updated": "updated_at",
    }
    field = field_map.get(args.by, args.by)

    def sort_key(r):
        val = r.get(field, 0)
        if val is None:
            return ""
        # For date strings, lexicographic sort works with ISO format
        if isinstance(val, str):
            return val
        return val

    records.sort(key=sort_key, reverse=True)

    for i, rec in enumerate(records):
        rec["rank"] = i + 1

    save_jsonl(records, args.output)
    print(f"Ranked {len(records)} repos by {field} -> {args.output}", file=sys.stderr)


# -- CLI -----------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="JSONL GitHub repo database management tool"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # merge
    p = sub.add_parser("merge", help="Merge multiple JSONL files with dedup by repo_id")
    p.add_argument("--inputs", nargs="+", required=True, help="Input JSONL files")
    p.add_argument("--output", required=True, help="Output JSONL file")

    # filter
    p = sub.add_parser("filter", help="Filter repos by stars, score, language, etc.")
    p.add_argument("--input", required=True, help="Input JSONL file")
    p.add_argument("--output", required=True, help="Output JSONL file")
    p.add_argument("--min-stars", type=int, default=None, help="Minimum star count")
    p.add_argument("--min-score", type=float, default=None, help="Minimum composite score")
    p.add_argument("--max-repos", type=int, default=None, help="Max repos to keep (0=unlimited)")
    p.add_argument("--language", default=None, help="Filter by primary language")
    p.add_argument("--not-archived", action="store_true", help="Exclude archived repos")

    # score
    p = sub.add_parser("score", help="Compute composite scores for all repos")
    p.add_argument("--input", required=True, help="Input JSONL file")
    p.add_argument("--output", required=True, help="Output scored JSONL file")

    # search
    p = sub.add_parser("search", help="Search repos by keyword in a field")
    p.add_argument("--input", required=True, help="Input JSONL file")
    p.add_argument("--query", required=True, help="Search query string")
    p.add_argument("--field", default="description",
                   choices=["description", "topics", "name"],
                   help="Field to search (default: description)")

    # tag
    p = sub.add_parser("tag", help="Add tags to repos; supports 'relevance:0.85' format")
    p.add_argument("--input", required=True, help="Input JSONL file (modified in-place)")
    p.add_argument("--ids", nargs="+", required=True, help="Repo IDs (owner/name)")
    p.add_argument("--tags", nargs="+", required=True,
                   help="Tags to add; use 'relevance:0.85' to set relevance_score")

    # stats
    p = sub.add_parser("stats", help="Print JSON summary statistics")
    p.add_argument("--input", required=True, help="Input JSONL file")

    # export
    p = sub.add_parser("export", help="Export database to csv, jsonl, or markdown")
    p.add_argument("--input", required=True, help="Input JSONL file")
    p.add_argument("--format", choices=["csv", "jsonl", "markdown"], default="jsonl",
                   help="Output format (default: jsonl)")
    p.add_argument("--output", "-o", default=None, help="Output file (default: stdout)")

    # rank
    p = sub.add_parser("rank", help="Rank repos by a field descending")
    p.add_argument("--input", required=True, help="Input JSONL file")
    p.add_argument("--output", required=True, help="Output ranked JSONL file")
    p.add_argument("--by", default="composite_score",
                   choices=["composite_score", "stars", "updated"],
                   help="Field to rank by (default: composite_score)")

    args = parser.parse_args()

    dispatch = {
        "merge": cmd_merge,
        "filter": cmd_filter,
        "score": cmd_score,
        "search": cmd_search,
        "tag": cmd_tag,
        "stats": cmd_stats,
        "export": cmd_export,
        "rank": cmd_rank,
    }
    dispatch[args.command](args)


if __name__ == "__main__":
    main()
