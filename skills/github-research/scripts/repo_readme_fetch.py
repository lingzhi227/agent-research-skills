#!/usr/bin/env python3
"""Fetch README content for GitHub repos without cloning.

Uses ``gh api`` to retrieve the README of one or more repositories,
decodes the base64 payload, and writes the results as JSONL.
"""

import argparse
import base64
import json
import subprocess
import sys
import time


def gh_api(endpoint: str) -> dict | None:
    """Call ``gh api`` and return parsed JSON, or *None* on failure."""
    try:
        proc = subprocess.run(
            ["gh", "api", endpoint],
            capture_output=True, text=True, timeout=30,
        )
        if proc.returncode == 0:
            return json.loads(proc.stdout)
        # Distinguish 404 (no README) from other errors.
        if "404" in proc.stderr or "Not Found" in proc.stderr:
            return None
        print(f"  gh api error ({proc.returncode}): {proc.stderr.strip()[:120]}",
              file=sys.stderr)
    except FileNotFoundError:
        print("  Error: 'gh' CLI not found. Please install GitHub CLI.", file=sys.stderr)
        sys.exit(1)
    except (subprocess.TimeoutExpired, json.JSONDecodeError) as exc:
        print(f"  gh api exception: {exc}", file=sys.stderr)
    return None


def fetch_readme(repo_id: str, max_chars: int) -> dict | None:
    """Return a dict with repo_id, readme_text, readme_length or *None*."""
    data = gh_api(f"/repos/{repo_id}/readme")
    if data is None:
        return None

    content_b64 = data.get("content", "")
    try:
        raw = base64.b64decode(content_b64).decode("utf-8", errors="replace")
    except Exception:
        raw = ""

    truncated = raw[:max_chars]
    return {
        "repo_id": repo_id,
        "readme_text": truncated,
        "readme_length": len(raw),
    }


def load_repo_ids_from_jsonl(path: str) -> list[str]:
    """Read repo_id values from a JSONL file."""
    ids: list[str] = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                rid = obj.get("repo_id")
                if rid:
                    ids.append(rid)
            except json.JSONDecodeError:
                continue
    return ids


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fetch README content for GitHub repos without cloning.",
    )
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--repos", nargs="+", metavar="OWNER/NAME",
                        help="One or more repos as owner/name")
    source.add_argument("--input", metavar="FILE",
                        help="JSONL file with repo_id fields")
    parser.add_argument("--output", required=True, help="Output JSONL file path")
    parser.add_argument("--max-chars", type=int, default=5000,
                        help="Max characters to keep from README (default: 5000)")

    args = parser.parse_args()

    repo_ids: list[str] = args.repos if args.repos else load_repo_ids_from_jsonl(args.input)

    if not repo_ids:
        print("No repos to process.", file=sys.stderr)
        sys.exit(0)

    total = len(repo_ids)
    results: list[dict] = []

    for idx, repo_id in enumerate(repo_ids, 1):
        print(f"Fetching README: {idx}/{total} — {repo_id}", file=sys.stderr)
        record = fetch_readme(repo_id, max_chars=args.max_chars)
        if record:
            results.append(record)
        else:
            print(f"  No README found for {repo_id}", file=sys.stderr)
        if idx < total:
            time.sleep(0.5)

    with open(args.output, "w", encoding="utf-8") as fout:
        for rec in results:
            fout.write(json.dumps(rec, ensure_ascii=False) + "\n")

    print(f"Done. {len(results)}/{total} README(s) written to {args.output}",
          file=sys.stderr)


if __name__ == "__main__":
    main()
