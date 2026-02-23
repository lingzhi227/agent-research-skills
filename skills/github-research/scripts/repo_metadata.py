#!/usr/bin/env python3
"""Fetch detailed metadata for GitHub repos via ``gh api``.

Retrieves main repo info and language breakdown, then maps the response
to the repo_db schema.  Can enrich existing JSONL records or create new
ones from scratch.
"""

import argparse
import json
import subprocess
import sys
import time


# ---------------------------------------------------------------------------
# GitHub helpers
# ---------------------------------------------------------------------------

def gh_api(endpoint: str) -> dict | None:
    """Call ``gh api`` and return parsed JSON, or *None* on failure."""
    try:
        proc = subprocess.run(
            ["gh", "api", endpoint],
            capture_output=True, text=True, timeout=30,
        )
        if proc.returncode == 0:
            return json.loads(proc.stdout)
        stderr = proc.stderr.strip()
        if "404" in stderr or "Not Found" in stderr:
            print(f"  404 — repo not found", file=sys.stderr)
        elif "rate limit" in stderr.lower() or "403" in stderr:
            print(f"  Rate limited. Consider increasing --delay.", file=sys.stderr)
        else:
            print(f"  gh api error ({proc.returncode}): {stderr[:120]}", file=sys.stderr)
    except FileNotFoundError:
        print("Error: 'gh' CLI not found. Please install GitHub CLI.", file=sys.stderr)
        sys.exit(1)
    except (subprocess.TimeoutExpired, json.JSONDecodeError) as exc:
        print(f"  gh api exception: {exc}", file=sys.stderr)
    return None


# ---------------------------------------------------------------------------
# Language breakdown
# ---------------------------------------------------------------------------

def compute_languages_pct(lang_data: dict) -> dict[str, float]:
    """Convert raw byte counts to percentages (0–100)."""
    total = sum(lang_data.values())
    if total == 0:
        return {}
    return {lang: round(count / total * 100, 2) for lang, count in lang_data.items()}


# ---------------------------------------------------------------------------
# Record building
# ---------------------------------------------------------------------------

def build_record(repo_id: str, meta: dict, lang_data: dict) -> dict:
    """Build a repo_db-schema record from GitHub API responses."""
    license_info = meta.get("license") or {}
    languages_pct = compute_languages_pct(lang_data)

    return {
        "repo_id": repo_id,
        "github_url": meta.get("html_url", f"https://github.com/{repo_id}"),
        "description": meta.get("description", ""),
        "homepage": meta.get("homepage", ""),
        "stars": meta.get("stargazers_count", 0),
        "forks_count": meta.get("forks_count", 0),
        "open_issues_count": meta.get("open_issues_count", 0),
        "watchers_count": meta.get("watchers_count", 0),
        "default_branch": meta.get("default_branch", ""),
        "license": license_info.get("spdx_id") or license_info.get("name", ""),
        "language": meta.get("language", ""),
        "languages_pct": languages_pct,
        "topics": meta.get("topics", []),
        "is_fork": meta.get("fork", False),
        "is_archived": meta.get("archived", False),
        "size_kb": meta.get("size", 0),
        "created_at": meta.get("created_at", ""),
        "updated_at": meta.get("updated_at", ""),
        "pushed_at": meta.get("pushed_at", ""),
        "owner_type": (meta.get("owner") or {}).get("type", ""),
        "network_count": meta.get("network_count", 0),
        "subscribers_count": meta.get("subscribers_count", 0),
    }


def enrich_record(existing: dict, fresh: dict) -> dict:
    """Merge *fresh* metadata into an *existing* record.

    Fresh values overwrite existing ones, except we preserve fields
    that exist only in the original (e.g. ``source``, ``paper_ids``).
    """
    merged = dict(existing)
    merged.update(fresh)
    # Preserve provenance fields from the original record.
    for key in ("source", "paper_ids", "paper_titles", "is_official", "framework"):
        if key in existing:
            merged[key] = existing[key]
    return merged


# ---------------------------------------------------------------------------
# I/O helpers
# ---------------------------------------------------------------------------

def load_jsonl(path: str) -> list[dict]:
    """Load a JSONL file into a list of dicts."""
    records: list[dict] = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return records


def write_jsonl(records: list[dict], path: str) -> None:
    """Write a list of dicts as JSONL."""
    with open(path, "w", encoding="utf-8") as fout:
        for rec in records:
            fout.write(json.dumps(rec, ensure_ascii=False) + "\n")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fetch detailed GitHub repo metadata via gh api.",
    )
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--repos", nargs="+", metavar="OWNER/NAME",
                        help="One or more repos as owner/name")
    source.add_argument("--input", metavar="FILE",
                        help="JSONL file with existing repo records to enrich")
    parser.add_argument("--output", required=True, help="Output JSONL file path")
    parser.add_argument("--delay", type=float, default=0.5,
                        help="Seconds between API requests per repo (default: 0.5)")

    args = parser.parse_args()

    # Determine which repos to process.
    existing_records: dict[str, dict] = {}  # keyed by repo_id

    if args.input:
        for rec in load_jsonl(args.input):
            rid = rec.get("repo_id")
            if rid:
                existing_records[rid] = rec
        repo_ids = list(existing_records.keys())
    else:
        repo_ids = args.repos or []

    if not repo_ids:
        print("No repos to process.", file=sys.stderr)
        sys.exit(0)

    total = len(repo_ids)
    results: list[dict] = []

    for idx, repo_id in enumerate(repo_ids, 1):
        print(f"Fetching metadata: {idx}/{total} — {repo_id}", file=sys.stderr)

        meta = gh_api(f"/repos/{repo_id}")
        if meta is None:
            print(f"  Skipping {repo_id} (metadata unavailable)", file=sys.stderr)
            # Keep the original record if enriching.
            if repo_id in existing_records:
                results.append(existing_records[repo_id])
            continue

        time.sleep(args.delay)

        lang_data = gh_api(f"/repos/{repo_id}/languages") or {}

        fresh = build_record(repo_id, meta, lang_data)

        if repo_id in existing_records:
            record = enrich_record(existing_records[repo_id], fresh)
        else:
            record = fresh

        results.append(record)

        if idx < total:
            time.sleep(args.delay)

    write_jsonl(results, args.output)
    print(f"Done. {len(results)}/{total} record(s) written to {args.output}",
          file=sys.stderr)


if __name__ == "__main__":
    main()
