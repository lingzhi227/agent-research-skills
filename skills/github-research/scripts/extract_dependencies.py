#!/usr/bin/env python3
"""Extract and parse dependency files from a cloned repository.

Identifies Python, Node, Rust, Go, and system dependencies.
Self-contained: stdlib only (regex-based parsing, no toml/yaml libraries).

Usage:
    python extract_dependencies.py --repo-dir ./repos/owner_name --output deps.json
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# ML framework detection mapping
# ---------------------------------------------------------------------------

ML_FRAMEWORK_MAP: dict[str, str] = {
    # PyTorch ecosystem
    "torch": "pytorch", "torchvision": "pytorch", "torchaudio": "pytorch",
    "pytorch-lightning": "pytorch", "lightning": "pytorch",
    # TensorFlow ecosystem
    "tensorflow": "tensorflow", "tensorflow-gpu": "tensorflow",
    "tf-nightly": "tensorflow", "tf-estimator-nightly": "tensorflow",
    "keras": "tensorflow",
    # JAX ecosystem
    "jax": "jax", "jaxlib": "jax", "flax": "jax", "optax": "jax",
    # HuggingFace ecosystem
    "transformers": "huggingface", "datasets": "huggingface",
    "tokenizers": "huggingface", "accelerate": "huggingface",
    "diffusers": "huggingface", "peft": "huggingface",
    # scikit-learn
    "scikit-learn": "scikit-learn", "sklearn": "scikit-learn",
    # Other ML tools
    "onnx": "onnx", "onnxruntime": "onnx",
    "tensorrt": "tensorrt", "triton": "triton",
    "deepspeed": "deepspeed", "fairscale": "fairscale",
}

SYSTEM_KEYWORDS: list[str] = [
    "cuda", "cudnn", "nvidia", "ffmpeg", "libsndfile", "sox",
    "opencv", "libgl", "libglib", "cmake", "gcc", "g++",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _read_text(path: Path) -> str | None:
    """Read a file as UTF-8, returning None on failure."""
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None


def _strip_version(spec: str) -> str:
    """Extract bare package name from a version specifier string."""
    return re.split(r"[><=!~;\[\s@]", spec.strip())[0].strip().lower()


def _extract_quoted_strings(text: str) -> list[str]:
    """Extract all single- or double-quoted strings from text."""
    return re.findall(r"""['"]([^'"]+)['"]""", text)


# ---------------------------------------------------------------------------
# Python: requirements.txt
# ---------------------------------------------------------------------------

def parse_requirements_txt(repo_dir: Path) -> dict | None:
    """Parse requirements*.txt files."""
    candidates = [
        "requirements.txt", "requirements-dev.txt", "requirements_dev.txt",
        "requirements-test.txt", "requirements_test.txt",
        "requirements/base.txt", "requirements/main.txt",
    ]
    all_specs: list[str] = []
    source_files: list[str] = []

    for name in candidates:
        path = repo_dir / name
        if not path.is_file():
            continue
        text = _read_text(path)
        if text is None:
            continue
        source_files.append(name)
        for line in text.splitlines():
            line = line.strip()
            if not line or line.startswith("#") or line.startswith("-"):
                continue
            all_specs.append(line)

    if not all_specs:
        return None
    # Deduplicate while preserving order
    seen: set[str] = set()
    deduped: list[str] = []
    for spec in all_specs:
        if spec not in seen:
            seen.add(spec)
            deduped.append(spec)
    return {"requirements": deduped, "source_file": ", ".join(source_files)}


# ---------------------------------------------------------------------------
# Python: setup.py
# ---------------------------------------------------------------------------

def parse_setup_py(repo_dir: Path) -> dict | None:
    """Parse setup.py for install_requires and extras_require."""
    path = repo_dir / "setup.py"
    if not path.is_file():
        return None
    text = _read_text(path)
    if text is None:
        return None

    specs: list[str] = []

    # install_requires = [...]
    match = re.search(r"install_requires\s*=\s*\[([^\]]+)\]", text, re.DOTALL)
    if match:
        specs.extend(_extract_quoted_strings(match.group(1)))

    # extras_require = { ... }
    match = re.search(r"extras_require\s*=\s*\{([^}]+)\}", text, re.DOTALL)
    if match:
        specs.extend(_extract_quoted_strings(match.group(1)))

    if not specs:
        return None
    return {"requirements": specs, "source_file": "setup.py"}


# ---------------------------------------------------------------------------
# Python: pyproject.toml
# ---------------------------------------------------------------------------

def parse_pyproject_toml(repo_dir: Path) -> dict | None:
    """Parse pyproject.toml for dependencies (regex-based, no toml lib)."""
    path = repo_dir / "pyproject.toml"
    if not path.is_file():
        return None
    text = _read_text(path)
    if text is None:
        return None

    specs: list[str] = []

    # [project] dependencies = [...]
    match = re.search(r"dependencies\s*=\s*\[([^\]]*)\]", text, re.DOTALL)
    if match:
        specs.extend(_extract_quoted_strings(match.group(1)))

    # [project.optional-dependencies] section -- grab all arrays
    section_match = re.search(
        r"\[project\.optional-dependencies\](.*?)(?=\n\[|\Z)", text, re.DOTALL,
    )
    if section_match:
        for array_match in re.finditer(r"=\s*\[([^\]]*)\]", section_match.group(1)):
            specs.extend(_extract_quoted_strings(array_match.group(1)))

    if not specs:
        return None
    return {"requirements": specs, "source_file": "pyproject.toml"}


# ---------------------------------------------------------------------------
# Python: environment.yml / environment.yaml
# ---------------------------------------------------------------------------

def parse_environment_yml(repo_dir: Path) -> dict | None:
    """Parse environment.yml / environment.yaml for conda dependencies."""
    source_name: str | None = None
    for name in ("environment.yml", "environment.yaml"):
        path = repo_dir / name
        if path.is_file():
            source_name = name
            break
    if source_name is None:
        return None

    text = _read_text(repo_dir / source_name)
    if text is None:
        return None

    specs: list[str] = []
    in_deps = False
    in_pip = False

    for line in text.splitlines():
        stripped = line.strip()

        # Detect dependencies: section
        if re.match(r"^dependencies\s*:", stripped):
            in_deps = True
            continue

        if not in_deps:
            continue

        # End of section on non-indented, non-list line
        if stripped and not stripped.startswith("-") and not stripped.startswith("#"):
            if not in_pip:
                in_deps = False
                continue

        # pip sub-section
        if stripped == "- pip:" or stripped == "- pip":
            in_pip = True
            continue
        if in_pip:
            if stripped.startswith("- "):
                pkg = stripped[2:].strip()
                if pkg:
                    specs.append(pkg)
                continue
            if not stripped.startswith("-") and stripped:
                in_pip = False

        if stripped.startswith("- "):
            pkg = stripped[2:].strip()
            if pkg and pkg not in ("pip", "pip:"):
                specs.append(pkg)

    if not specs:
        return None
    return {"requirements": specs, "source_file": source_name}


# ---------------------------------------------------------------------------
# Node: package.json
# ---------------------------------------------------------------------------

def parse_package_json(repo_dir: Path) -> dict | None:
    """Parse package.json for dependencies and devDependencies."""
    path = repo_dir / "package.json"
    if not path.is_file():
        return None
    text = _read_text(path)
    if text is None:
        return None
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return None

    deps = data.get("dependencies") or {}
    dev_deps = data.get("devDependencies") or {}
    if not deps and not dev_deps:
        return None

    result: dict = {"source_file": "package.json"}
    if deps:
        result["dependencies"] = deps
    if dev_deps:
        result["devDependencies"] = dev_deps
    return result


# ---------------------------------------------------------------------------
# Rust: Cargo.toml
# ---------------------------------------------------------------------------

def parse_cargo_toml(repo_dir: Path) -> dict | None:
    """Parse Cargo.toml for [dependencies] section."""
    path = repo_dir / "Cargo.toml"
    if not path.is_file():
        return None
    text = _read_text(path)
    if text is None:
        return None

    deps: dict[str, str] = {}
    match = re.search(
        r"\[dependencies\](.*?)(?=\n\[|\Z)", text, re.DOTALL,
    )
    if match:
        for line in match.group(1).splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            # name = "version"
            m = re.match(r'^(\S+)\s*=\s*"([^"]*)"', line)
            if m:
                deps[m.group(1)] = m.group(2)
            else:
                # name = { version = "...", ... }
                m = re.match(r"^(\S+)\s*=\s*\{", line)
                if m:
                    ver = re.search(r'version\s*=\s*"([^"]*)"', line)
                    deps[m.group(1)] = ver.group(1) if ver else "*"

    if not deps:
        return None
    return {"dependencies": deps, "source_file": "Cargo.toml"}


# ---------------------------------------------------------------------------
# Go: go.mod
# ---------------------------------------------------------------------------

def parse_go_mod(repo_dir: Path) -> dict | None:
    """Parse go.mod for require block."""
    path = repo_dir / "go.mod"
    if not path.is_file():
        return None
    text = _read_text(path)
    if text is None:
        return None

    modules: list[str] = []
    in_require = False

    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("require ("):
            in_require = True
            continue
        if in_require:
            if stripped == ")":
                in_require = False
                continue
            parts = stripped.split()
            if parts and not parts[0].startswith("//"):
                modules.append(parts[0])
        elif stripped.startswith("require "):
            parts = stripped.split()
            if len(parts) >= 2:
                modules.append(parts[1])

    if not modules:
        return None
    return {"modules": modules, "source_file": "go.mod"}


# ---------------------------------------------------------------------------
# System dependency detection
# ---------------------------------------------------------------------------

def detect_system_deps(repo_dir: Path) -> list[str]:
    """Detect system-level dependencies from Dockerfile, README, setup.py."""
    found: set[str] = set()
    scan_files = [
        "Dockerfile", "docker-compose.yml", "docker-compose.yaml",
        "README.md", "README.rst", "readme.md",
        "setup.py", "Makefile", "CMakeLists.txt",
    ]

    for name in scan_files:
        path = repo_dir / name
        if not path.is_file():
            continue
        text = _read_text(path)
        if text is None:
            continue
        text_lower = text.lower()

        # Check for known system keywords
        for kw in SYSTEM_KEYWORDS:
            if kw in text_lower:
                found.add(kw)

        # Extract apt-get install packages from Dockerfiles
        if name.lower().startswith("dockerfile") or name.lower() == "dockerfile":
            for m in re.finditer(r"apt-get\s+install[^&\n]*", text):
                tokens = m.group(0).split()
                for tok in tokens:
                    tok = tok.strip().rstrip("\\")
                    if tok and not tok.startswith("-") and tok not in (
                        "apt-get", "install", "&&", "||", "RUN",
                    ):
                        found.add(tok)

    return sorted(found)


# ---------------------------------------------------------------------------
# ML framework detection
# ---------------------------------------------------------------------------

def detect_ml_frameworks(all_packages: list[str]) -> list[str]:
    """Identify ML frameworks from the combined package list."""
    frameworks: set[str] = set()
    for pkg in all_packages:
        pkg_lower = pkg.lower()
        if pkg_lower in ML_FRAMEWORK_MAP:
            frameworks.add(ML_FRAMEWORK_MAP[pkg_lower])
        # Handle tf-* prefix patterns
        elif pkg_lower.startswith("tf-") or pkg_lower.startswith("tensorflow-"):
            frameworks.add("tensorflow")
    return sorted(frameworks)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extract and parse dependency files from a cloned repository",
    )
    parser.add_argument(
        "--repo-dir", required=True,
        help="Path to cloned repository directory",
    )
    parser.add_argument(
        "--output", required=True,
        help="Output JSON file path",
    )
    parser.add_argument(
        "--repo-id", default=None,
        help="Repository identifier (owner/name); inferred from dir name if omitted",
    )

    args = parser.parse_args()

    repo_dir = Path(args.repo_dir).resolve()
    if not repo_dir.is_dir():
        print(f"Error: repo directory not found: {repo_dir}", file=sys.stderr)
        sys.exit(1)

    # Infer repo_id from directory name if not provided
    repo_id: str = args.repo_id or ""
    if not repo_id:
        dir_name = repo_dir.name
        repo_id = dir_name.replace("_", "/", 1) if "_" in dir_name else dir_name

    print(f"Extracting dependencies from {repo_dir} ...", file=sys.stderr)

    # --- Python: merge results from all parsers ---
    python_info: dict | None = None
    for parser_fn in (parse_requirements_txt, parse_setup_py,
                      parse_pyproject_toml, parse_environment_yml):
        result = parser_fn(repo_dir)
        if result is not None:
            if python_info is None:
                python_info = result
            else:
                # Merge: append specs, combine source_file
                existing = set(python_info["requirements"])
                for spec in result["requirements"]:
                    if spec not in existing:
                        python_info["requirements"].append(spec)
                        existing.add(spec)
                python_info["source_file"] += f", {result['source_file']}"
    if python_info:
        print(f"  Python: {len(python_info['requirements'])} packages "
              f"from {python_info['source_file']}", file=sys.stderr)

    # --- Node ---
    node_info = parse_package_json(repo_dir)
    if node_info:
        n = len(node_info.get("dependencies", {})) + len(node_info.get("devDependencies", {}))
        print(f"  Node: {n} packages from {node_info['source_file']}", file=sys.stderr)

    # --- Rust ---
    rust_info = parse_cargo_toml(repo_dir)
    if rust_info:
        print(f"  Rust: {len(rust_info['dependencies'])} crates "
              f"from {rust_info['source_file']}", file=sys.stderr)

    # --- Go ---
    go_info = parse_go_mod(repo_dir)
    if go_info:
        print(f"  Go: {len(go_info['modules'])} modules "
              f"from {go_info['source_file']}", file=sys.stderr)

    # --- Collect all package names (flat, normalized) ---
    all_packages: set[str] = set()

    if python_info:
        for spec in python_info["requirements"]:
            name = _strip_version(spec)
            if name:
                all_packages.add(name)

    if node_info:
        for key in ("dependencies", "devDependencies"):
            for pkg_name in node_info.get(key, {}):
                all_packages.add(pkg_name.lower())

    if rust_info:
        for crate_name in rust_info["dependencies"]:
            all_packages.add(crate_name.lower())

    if go_info:
        for mod_path in go_info["modules"]:
            # Use last path segment as package name
            parts = mod_path.rstrip("/").split("/")
            all_packages.add(parts[-1].lower())

    all_packages_sorted = sorted(all_packages)

    # --- System dependencies ---
    system_deps = detect_system_deps(repo_dir)
    if system_deps:
        print(f"  System: {len(system_deps)} system dependencies detected",
              file=sys.stderr)

    # --- ML frameworks ---
    ml_frameworks = detect_ml_frameworks(all_packages_sorted)
    if ml_frameworks:
        print(f"  ML frameworks: {', '.join(ml_frameworks)}", file=sys.stderr)

    # --- Build output ---
    output: dict = {
        "repo_id": repo_id,
        "python": python_info,
        "node": node_info,
        "rust": rust_info,
        "go": go_info,
        "system": system_deps,
        "ml_frameworks": ml_frameworks,
        "all_packages": all_packages_sorted,
        "overlap_with": {},
    }

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
        f.write("\n")

    ecosystems = sum(1 for x in (python_info, node_info, rust_info, go_info)
                     if x is not None)
    print(
        f"Extracted {len(all_packages_sorted)} packages across "
        f"{ecosystems} ecosystem(s) -> {args.output}",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
