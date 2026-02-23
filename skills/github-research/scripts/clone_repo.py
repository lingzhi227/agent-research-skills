#!/usr/bin/env python3
"""Shallow-clone GitHub repos for local code analysis.

Usage:
    python clone_repo.py --repo owner/name --output-dir /tmp/repos [--depth 1] [--branch main]

Outputs JSON to stdout with clone result; stats to stderr.
"""

import argparse
import json
import os
import subprocess
import sys


def get_dir_size(path: str) -> int:
    """Walk directory and sum all file sizes in bytes."""
    total = 0
    for dirpath, _dirnames, filenames in os.walk(path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            try:
                total += os.path.getsize(fp)
            except OSError:
                pass
    return total


def clone_repo(repo: str, output_dir: str, depth: int, branch: str | None) -> dict:
    """Clone a GitHub repo and return result metadata."""
    parts = repo.split("/")
    if len(parts) != 2:
        return {
            "repo_id": repo,
            "local_path": None,
            "clone_success": False,
            "error": f"Invalid repo format '{repo}', expected 'owner/name'",
        }

    owner, name = parts
    url = f"https://github.com/{owner}/{name}.git"
    target = os.path.join(output_dir, name)

    os.makedirs(output_dir, exist_ok=True)

    # Build clone command
    cmd = ["git", "clone", f"--depth={depth}", "--single-branch"]
    if branch:
        cmd += ["--branch", branch]
    cmd += [url, target]

    print(f"[clone] Running: {' '.join(cmd)}", file=sys.stderr)

    result = subprocess.run(cmd, capture_output=True, text=True)

    # If branch-specific clone fails, retry without --branch
    if result.returncode != 0 and branch:
        print(f"[clone] Branch '{branch}' failed, retrying with default branch...", file=sys.stderr)
        cmd_retry = ["git", "clone", f"--depth={depth}", "--single-branch", url, target]
        result = subprocess.run(cmd_retry, capture_output=True, text=True)

    # Validate clone
    if result.returncode != 0:
        return {
            "repo_id": repo,
            "local_path": target,
            "clone_success": False,
            "error": result.stderr.strip(),
        }

    if not os.path.isdir(target) or not os.listdir(target):
        return {
            "repo_id": repo,
            "local_path": target,
            "clone_success": False,
            "error": "Clone directory is empty or missing",
        }

    # Compute clone size
    size_bytes = get_dir_size(target)
    size_mb = size_bytes / (1024 * 1024)
    file_count = sum(len(files) for _, _, files in os.walk(target))

    print(f"[clone] Success: {target}", file=sys.stderr)
    print(f"[clone] Size: {size_mb:.1f} MB, Files: {file_count}", file=sys.stderr)

    return {
        "repo_id": repo,
        "local_path": os.path.abspath(target),
        "clone_success": True,
        "error": None,
    }


def main():
    parser = argparse.ArgumentParser(description="Shallow-clone a GitHub repo for local analysis.")
    parser.add_argument("--repo", required=True, help="Repository in owner/name format")
    parser.add_argument("--output-dir", required=True, help="Parent directory for the clone")
    parser.add_argument("--depth", type=int, default=1, help="Clone depth (default: 1)")
    parser.add_argument("--branch", default=None, help="Branch to clone (default: repo default branch)")
    args = parser.parse_args()

    result = clone_repo(args.repo, args.output_dir, args.depth, args.branch)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
