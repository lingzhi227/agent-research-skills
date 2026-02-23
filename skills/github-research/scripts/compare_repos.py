#!/usr/bin/env python3
"""Generate comparison matrix across analyzed repositories.

Reads analysis JSON files and dependency files to produce a structured comparison.

Usage:
    python compare_repos.py --input phase4_deep_dive/analyses/ --output comparison.json
"""

import argparse
import json
import os
import sys
from itertools import combinations
from pathlib import Path


# ---------------------------------------------------------------------------
# I/O helpers
# ---------------------------------------------------------------------------

def load_json(path: str) -> dict | None:
    """Load a JSON file, returning None on failure."""
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"  Warning: cannot load {path}: {exc}", file=sys.stderr)
        return None


def find_analysis_files(analyses_dir: str) -> dict[str, dict[str, dict | None]]:
    """Discover *_structure.json and *_deps.json files, grouped by repo name.

    Returns {repo_name: {"structure": <dict|None>, "deps": <dict|None>}}.
    """
    repos: dict[str, dict[str, dict | None]] = {}

    for fname in sorted(os.listdir(analyses_dir)):
        fpath = os.path.join(analyses_dir, fname)
        if not os.path.isfile(fpath):
            continue

        if fname.endswith("_structure.json"):
            name = fname.removesuffix("_structure.json")
            repos.setdefault(name, {"structure": None, "deps": None})
            repos[name]["structure"] = load_json(fpath)
        elif fname.endswith("_deps.json"):
            name = fname.removesuffix("_deps.json")
            repos.setdefault(name, {"structure": None, "deps": None})
            repos[name]["deps"] = load_json(fpath)

    return repos


# ---------------------------------------------------------------------------
# Dimension extractors
# ---------------------------------------------------------------------------

def _get(data: dict | None, *keys: str, default: object = None) -> object:
    """Try multiple keys on a dict, returning the first truthy value."""
    if data is None:
        return default
    for key in keys:
        val = data.get(key)
        if val is not None and val != "" and val != [] and val != {}:
            return val
    return default


def extract_repo_id(
    structure: dict | None, deps: dict | None, file_key: str,
) -> str:
    """Best-effort extraction of owner/name repo_id."""
    rid = _get(structure, "repo_id", "repo")
    if rid:
        return str(rid)
    rid = _get(deps, "repo_id", "repo")
    if rid:
        return str(rid)
    return file_key


def extract_primary_language(structure: dict | None) -> str:
    """Primary language from structure analysis."""
    lang = _get(structure, "primary_language", "language")
    if lang and isinstance(lang, str):
        return lang
    # Fall back: pick language with highest LOC
    langs = _get(structure, "languages", "language_stats", default={})
    if isinstance(langs, dict) and langs:
        return max(langs, key=lambda k: langs[k] if isinstance(langs[k], (int, float)) else 0)
    return "Unknown"


def extract_total_loc(structure: dict | None) -> int:
    """Total lines of code."""
    loc = _get(structure, "total_loc", "loc", default=0)
    if isinstance(loc, (int, float)):
        return int(loc)
    # Sum across languages
    langs = _get(structure, "languages", "language_stats", default={})
    if isinstance(langs, dict):
        return sum(v for v in langs.values() if isinstance(v, (int, float)))
    return 0


def extract_total_files(structure: dict | None) -> int:
    """Total file count."""
    count = _get(structure, "total_files", "file_count", default=0)
    if isinstance(count, (int, float)):
        return int(count)
    files = _get(structure, "files", "file_tree", default=[])
    if isinstance(files, list):
        return len(files)
    return 0


def extract_stars(structure: dict | None) -> int:
    """Star count."""
    return int(_get(structure, "stars", default=0) or 0)


def extract_ml_frameworks(deps: dict | None) -> list[str]:
    """Detect ML frameworks from dependency data."""
    if deps is None:
        return _get(deps, "ml_frameworks", default=[]) or []  # type: ignore[return-value]

    # If the deps file already has ml_frameworks, use it
    existing = deps.get("ml_frameworks")
    if existing and isinstance(existing, list):
        return existing

    return []


def extract_has_tests(structure: dict | None) -> bool:
    """Whether the repo has test files."""
    if structure is None:
        return False
    # Direct field
    test_files = _get(structure, "test_files", default=[])
    if isinstance(test_files, list) and test_files:
        return True
    # Check has_tests flag
    if structure.get("has_tests"):
        return True
    # Scan file list for test indicators
    files = _get(structure, "files", "file_tree", default=[])
    if isinstance(files, list):
        for f in files:
            name = f if isinstance(f, str) else (
                f.get("path", "") if isinstance(f, dict) else ""
            )
            name_lower = name.lower()
            if ("/test/" in name_lower or "/tests/" in name_lower
                    or name_lower.startswith("test") or "test_" in name_lower):
                return True
    # Check key directories
    key_dirs = _get(structure, "key_dirs", "directories", default=[])
    if isinstance(key_dirs, list):
        for d in key_dirs:
            d_name = d if isinstance(d, str) else (
                d.get("name", "") if isinstance(d, dict) else ""
            )
            if d_name.lower() in ("test", "tests", "testing", "test_suite"):
                return True
    return False


def extract_has_docker(structure: dict | None) -> bool:
    """Whether the repo has Docker configuration."""
    if structure is None:
        return False
    config_files = _get(structure, "config_files", default=[])
    if isinstance(config_files, list):
        for f in config_files:
            name = f if isinstance(f, str) else (
                f.get("path", f.get("name", "")) if isinstance(f, dict) else ""
            )
            name_lower = name.lower()
            if name_lower in ("dockerfile", "docker-compose.yml",
                              "docker-compose.yaml", ".dockerignore"):
                return True
    # Also check files list
    files = _get(structure, "files", "file_tree", default=[])
    if isinstance(files, list):
        for f in files:
            name = f if isinstance(f, str) else (
                f.get("path", "") if isinstance(f, dict) else ""
            )
            basename = os.path.basename(name).lower()
            if basename in ("dockerfile", "docker-compose.yml",
                            "docker-compose.yaml"):
                return True
    return False


def extract_license(structure: dict | None) -> str:
    """License identifier."""
    return str(_get(structure, "license", default="") or "")


def extract_entry_points(structure: dict | None) -> list[str]:
    """Main entry points."""
    entries = _get(structure, "entry_points", "main_files", default=[])
    if isinstance(entries, list):
        return [str(e) for e in entries[:10]]
    return []


def extract_config_format(structure: dict | None) -> str:
    """Dominant config file format."""
    config_files = _get(structure, "config_files", default=[])
    if not isinstance(config_files, list):
        return ""

    format_counts: dict[str, int] = {}
    ext_map: dict[str, str] = {
        ".yaml": "yaml", ".yml": "yaml",
        ".toml": "toml",
        ".json": "json",
        ".ini": "ini", ".cfg": "ini",
    }

    for f in config_files:
        name = f if isinstance(f, str) else (
            f.get("path", f.get("name", "")) if isinstance(f, dict) else ""
        )
        _, ext = os.path.splitext(name.lower())
        fmt = ext_map.get(ext, "")
        if fmt:
            format_counts[fmt] = format_counts.get(fmt, 0) + 1

    if not format_counts:
        return ""
    return max(format_counts, key=lambda k: format_counts[k])


# ---------------------------------------------------------------------------
# Dependency overlap
# ---------------------------------------------------------------------------

def collect_all_packages(deps: dict | None) -> set[str]:
    """Collect a flat set of normalized package names from a deps record."""
    if deps is None:
        return set()

    # Prefer the pre-computed all_packages field
    all_pkgs = deps.get("all_packages")
    if isinstance(all_pkgs, list) and all_pkgs:
        return {p.lower() for p in all_pkgs}

    # Otherwise, gather from per-ecosystem sections
    names: set[str] = set()

    # Python
    py = deps.get("python")
    if isinstance(py, dict):
        for spec in py.get("requirements", []):
            if isinstance(spec, str):
                bare = spec.split(">=")[0].split("<=")[0].split("==")[0]
                bare = bare.split("~=")[0].split("!=")[0].split("[")[0].strip()
                if bare:
                    names.add(bare.lower())

    # Node
    node = deps.get("node")
    if isinstance(node, dict):
        for key in ("dependencies", "devDependencies"):
            val = node.get(key, {})
            if isinstance(val, dict):
                names.update(k.lower() for k in val)

    # Rust
    rust = deps.get("rust")
    if isinstance(rust, dict):
        for key in ("dependencies",):
            val = rust.get(key, {})
            if isinstance(val, dict):
                names.update(k.lower() for k in val)

    # Go
    go = deps.get("go")
    if isinstance(go, dict):
        for mod in go.get("modules", []):
            if isinstance(mod, str):
                parts = mod.rstrip("/").split("/")
                names.add(parts[-1].lower())

    return names


def compute_dependency_overlap(
    repo_packages: dict[str, set[str]],
    min_shared: int = 3,
) -> list[dict]:
    """Compute shared packages for each pair of repos.

    Only includes pairs with at least min_shared common packages.
    """
    overlaps: list[dict] = []
    repo_ids = sorted(repo_packages.keys())
    for a, b in combinations(repo_ids, 2):
        shared = sorted(repo_packages[a] & repo_packages[b])
        if len(shared) >= min_shared:
            overlaps.append({
                "repos": [a, b],
                "shared": shared,
            })
    return overlaps


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate comparison matrix across analyzed repositories",
    )
    parser.add_argument(
        "--input", required=True,
        help="Directory containing *_structure.json and *_deps.json files",
    )
    parser.add_argument(
        "--output", required=True,
        help="Output comparison JSON file path",
    )
    parser.add_argument(
        "--repo-db", default=None,
        help="Optional repo_db.jsonl to enrich with stars/metadata",
    )

    args = parser.parse_args()

    if not os.path.isdir(args.input):
        print(f"Error: analyses directory not found: {args.input}",
              file=sys.stderr)
        sys.exit(1)

    # Load optional repo_db for enrichment (stars, etc.)
    repo_db_map: dict[str, dict] = {}
    if args.repo_db and os.path.isfile(args.repo_db):
        with open(args.repo_db, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    rec = json.loads(line)
                    rid = rec.get("repo_id", "")
                    # Index by both full id and short name
                    repo_db_map[rid] = rec
                    repo_db_map[rid.split("/")[-1]] = rec

    # Discover and load analysis files
    repos = find_analysis_files(args.input)
    if not repos:
        print("Error: no *_structure.json or *_deps.json files found",
              file=sys.stderr)
        sys.exit(1)

    print(f"Found analysis files for {len(repos)} repo(s)", file=sys.stderr)

    # --- Build dimension maps ---
    repo_ids: list[str] = []
    dim_primary_language: dict[str, str] = {}
    dim_total_loc: dict[str, int] = {}
    dim_total_files: dict[str, int] = {}
    dim_stars: dict[str, int] = {}
    dim_ml_framework: dict[str, list[str]] = {}
    dim_has_tests: dict[str, bool] = {}
    dim_has_docker: dict[str, bool] = {}
    dim_license: dict[str, str] = {}
    dim_entry_points: dict[str, list[str]] = {}
    dim_config_format: dict[str, str] = {}

    repo_packages: dict[str, set[str]] = {}

    for file_key, data in sorted(repos.items()):
        structure = data.get("structure")
        deps = data.get("deps")
        rid = extract_repo_id(structure, deps, file_key)
        repo_ids.append(rid)

        dim_primary_language[rid] = extract_primary_language(structure)
        dim_total_loc[rid] = extract_total_loc(structure)
        dim_total_files[rid] = extract_total_files(structure)
        # Stars from structure.json, fallback to repo_db
        stars = extract_stars(structure)
        if stars == 0 and rid in repo_db_map:
            stars = int(repo_db_map[rid].get("stars", 0))
        if stars == 0:
            # Try matching by short name
            short = rid.split("/")[-1]
            if short in repo_db_map:
                stars = int(repo_db_map[short].get("stars", 0))
        dim_stars[rid] = stars
        dim_ml_framework[rid] = extract_ml_frameworks(deps)
        dim_has_tests[rid] = extract_has_tests(structure)
        dim_has_docker[rid] = extract_has_docker(structure)
        dim_license[rid] = extract_license(structure)
        dim_entry_points[rid] = extract_entry_points(structure)
        dim_config_format[rid] = extract_config_format(structure)

        repo_packages[rid] = collect_all_packages(deps)

    # --- Compute pairwise dependency overlap ---
    dependency_overlap = compute_dependency_overlap(repo_packages)

    # --- Assemble output ---
    comparison: dict = {
        "repos": repo_ids,
        "dimensions": {
            "primary_language": dim_primary_language,
            "total_loc": dim_total_loc,
            "total_files": dim_total_files,
            "stars": dim_stars,
            "ml_framework": dim_ml_framework,
            "has_tests": dim_has_tests,
            "has_docker": dim_has_docker,
            "license": dim_license,
            "entry_points": dim_entry_points,
            "config_format": dim_config_format,
        },
        "dependency_overlap": dependency_overlap,
    }

    # --- Write output ---
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(comparison, f, indent=2, ensure_ascii=False)
        f.write("\n")

    # --- Summary to stderr ---
    n_dims = len(comparison["dimensions"])
    lang_counts: dict[str, int] = {}
    for lang in dim_primary_language.values():
        lang_counts[lang] = lang_counts.get(lang, 0) + 1
    lang_summary = ", ".join(
        f"{l}({c})" for l, c in sorted(lang_counts.items(), key=lambda x: -x[1])
    )

    fw_counts: dict[str, int] = {}
    for fws in dim_ml_framework.values():
        for fw in fws:
            fw_counts[fw] = fw_counts.get(fw, 0) + 1
    fw_summary = ", ".join(
        f"{f}({c})" for f, c in sorted(fw_counts.items(), key=lambda x: -x[1])
    ) if fw_counts else "none"

    test_count = sum(1 for v in dim_has_tests.values() if v)
    docker_count = sum(1 for v in dim_has_docker.values() if v)

    print(f"Compared {len(repo_ids)} repos across {n_dims} dimensions",
          file=sys.stderr)
    print(f"  Languages: {lang_summary}", file=sys.stderr)
    print(f"  ML frameworks: {fw_summary}", file=sys.stderr)
    print(f"  With tests: {test_count}/{len(repo_ids)}", file=sys.stderr)
    print(f"  With Docker: {docker_count}/{len(repo_ids)}", file=sys.stderr)
    print(f"  Dependency overlaps: {len(dependency_overlap)} pair(s)",
          file=sys.stderr)
    print(f"  Output: {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
