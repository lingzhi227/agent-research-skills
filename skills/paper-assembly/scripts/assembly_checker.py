#!/usr/bin/env python3
"""Check paper pipeline completeness and report missing artifacts.

Scans a paper directory, checks which pipeline phases are complete
(literature, code, figures, tables, bib, sections), reports missing
artifacts, and suggests next steps.

Self-contained: uses only stdlib.

Usage:
    python assembly_checker.py --dir paper/ --output checkpoint.json
    python assembly_checker.py --dir paper/
    python assembly_checker.py --dir paper/ --verbose
"""

import argparse
import glob
import json
import os
import re
import sys


PIPELINE_PHASES = [
    {
        "name": "literature",
        "description": "Literature search and review",
        "artifacts": ["*.jsonl", "knowledge_base.*", "papers.bib"],
        "patterns": ["literature", "papers", "references"],
    },
    {
        "name": "planning",
        "description": "Research plan and paper structure",
        "artifacts": ["research_plan.*", "plan.*", "outline.*"],
        "patterns": ["plan", "outline"],
    },
    {
        "name": "code",
        "description": "Experiment code and scripts",
        "artifacts": ["*.py", "*.sh", "train.*", "eval.*"],
        "patterns": ["code", "scripts", "src", "experiments"],
    },
    {
        "name": "results",
        "description": "Experimental results",
        "artifacts": ["results.*", "*.csv", "metrics.*", "logs/"],
        "patterns": ["results", "output", "logs"],
    },
    {
        "name": "figures",
        "description": "Generated figures",
        "artifacts": ["*.png", "*.pdf", "*.eps"],
        "patterns": ["figures", "figs", "plots", "images"],
    },
    {
        "name": "tables",
        "description": "LaTeX tables",
        "artifacts": ["*table*.tex", "*results*.tex"],
        "patterns": ["tables"],
    },
    {
        "name": "bibliography",
        "description": "BibTeX bibliography",
        "artifacts": ["*.bib"],
        "patterns": ["."],
    },
    {
        "name": "sections",
        "description": "Paper sections (LaTeX)",
        "artifacts": ["*.tex"],
        "patterns": ["sections", "."],
    },
    {
        "name": "compilation",
        "description": "Compiled PDF",
        "artifacts": ["*.pdf"],
        "patterns": ["."],
    },
]

EXPECTED_SECTIONS = [
    "abstract", "introduction", "related", "method",
    "experiment", "result", "conclusion", "appendix",
]


def find_artifacts(base_dir: str, phase: dict) -> list[str]:
    """Find artifacts for a pipeline phase."""
    found = []
    search_dirs = [base_dir]
    for pattern_dir in phase["patterns"]:
        candidate = os.path.join(base_dir, pattern_dir)
        if os.path.isdir(candidate):
            search_dirs.append(candidate)

    for search_dir in search_dirs:
        for artifact_pattern in phase["artifacts"]:
            if artifact_pattern.endswith("/"):
                # Check for directory
                dpath = os.path.join(search_dir, artifact_pattern.rstrip("/"))
                if os.path.isdir(dpath):
                    found.append(dpath)
            else:
                matches = glob.glob(os.path.join(search_dir, artifact_pattern))
                found.extend(matches)

    # Deduplicate
    return sorted(set(found))


def check_tex_sections(base_dir: str) -> dict:
    """Check which paper sections exist in .tex files."""
    tex_files = glob.glob(os.path.join(base_dir, "**/*.tex"), recursive=True)
    all_tex = ""
    for tf in tex_files:
        try:
            with open(tf, encoding="utf-8", errors="replace") as f:
                all_tex += f.read() + "\n"
        except Exception:
            pass

    found_sections = set()
    for match in re.finditer(r"\\section\*?\{([^}]+)\}", all_tex):
        name = match.group(1).lower().strip()
        for expected in EXPECTED_SECTIONS:
            if expected in name:
                found_sections.add(expected)

    if re.search(r"\\begin\{abstract\}", all_tex):
        found_sections.add("abstract")

    return {
        "found": sorted(found_sections),
        "missing": sorted(set(EXPECTED_SECTIONS[:7]) - found_sections),
        "tex_files": [os.path.relpath(f, base_dir) for f in tex_files],
    }


def check_citations(base_dir: str) -> dict:
    """Check citation status."""
    tex_files = glob.glob(os.path.join(base_dir, "**/*.tex"), recursive=True)
    bib_files = glob.glob(os.path.join(base_dir, "**/*.bib"), recursive=True)

    cite_keys = set()
    for tf in tex_files:
        try:
            with open(tf, encoding="utf-8", errors="replace") as f:
                content = f.read()
            for match in re.findall(r"\\cite[a-z]*\{([^}]+)\}", content):
                for key in match.split(","):
                    cite_keys.add(key.strip())
        except Exception:
            pass

    bib_keys = set()
    for bf in bib_files:
        try:
            with open(bf, encoding="utf-8", errors="replace") as f:
                content = f.read()
            bib_keys.update(re.findall(r"@\w+\{([^,]+),", content))
        except Exception:
            pass

    return {
        "cited": len(cite_keys),
        "in_bib": len(bib_keys),
        "missing": sorted(cite_keys - bib_keys),
        "unused": len(bib_keys - cite_keys),
    }


def check_figures(base_dir: str) -> dict:
    """Check figure status."""
    tex_files = glob.glob(os.path.join(base_dir, "**/*.tex"), recursive=True)
    fig_refs = set()
    for tf in tex_files:
        try:
            with open(tf, encoding="utf-8", errors="replace") as f:
                content = f.read()
            fig_refs.update(re.findall(r"\\includegraphics(?:\[.*?\])?\{([^}]+)\}", content))
        except Exception:
            pass

    missing_figs = []
    for fig in fig_refs:
        fig_path = os.path.join(base_dir, fig)
        found = os.path.exists(fig_path)
        if not found:
            for ext in [".png", ".pdf", ".jpg", ".eps"]:
                if os.path.exists(fig_path + ext):
                    found = True
                    break
        if not found:
            missing_figs.append(fig)

    return {
        "referenced": len(fig_refs),
        "missing": missing_figs,
    }


def suggest_next_steps(phase_status: dict) -> list[str]:
    """Suggest next steps based on pipeline status."""
    steps = []
    for phase_name, status in phase_status.items():
        if not status["complete"]:
            if phase_name == "literature":
                steps.append("Run literature search: use literature-search skill")
            elif phase_name == "planning":
                steps.append("Create research plan: use research-planning skill")
            elif phase_name == "code":
                steps.append("Write experiment code: use experiment-code skill")
            elif phase_name == "results":
                steps.append("Run experiments to generate results")
            elif phase_name == "figures":
                steps.append("Generate figures: use figure-generation skill")
            elif phase_name == "tables":
                steps.append("Generate tables: use table-generation skill")
            elif phase_name == "bibliography":
                steps.append("Add bibliography: use citation-management skill")
            elif phase_name == "sections":
                steps.append("Write paper sections: use paper-writing-section skill")
            elif phase_name == "compilation":
                steps.append("Compile paper: use paper-compilation skill")
    return steps


def main():
    parser = argparse.ArgumentParser(description="Check paper pipeline completeness")
    parser.add_argument("--dir", required=True, help="Paper directory")
    parser.add_argument("--output", "-o", help="Output JSON checkpoint file")
    parser.add_argument("--verbose", action="store_true", help="Show detailed artifacts")
    args = parser.parse_args()

    if not os.path.isdir(args.dir):
        print(f"Error: {args.dir} is not a directory", file=sys.stderr)
        sys.exit(1)

    phase_status = {}
    completed = 0

    for phase in PIPELINE_PHASES:
        artifacts = find_artifacts(args.dir, phase)
        is_complete = len(artifacts) > 0
        phase_status[phase["name"]] = {
            "complete": is_complete,
            "artifacts": [os.path.relpath(a, args.dir) for a in artifacts],
            "count": len(artifacts),
        }
        if is_complete:
            completed += 1

    # Detailed checks
    section_info = check_tex_sections(args.dir)
    citation_info = check_citations(args.dir)
    figure_info = check_figures(args.dir)
    next_steps = suggest_next_steps(phase_status)

    report = {
        "directory": os.path.abspath(args.dir),
        "phases_completed": completed,
        "phases_total": len(PIPELINE_PHASES),
        "completion_pct": round(100 * completed / len(PIPELINE_PHASES)),
        "phases": phase_status,
        "sections": section_info,
        "citations": citation_info,
        "figures": figure_info,
        "next_steps": next_steps,
    }

    # Print summary
    print(f"Paper Pipeline Status: {args.dir}")
    print(f"  Completion: {completed}/{len(PIPELINE_PHASES)} phases ({report['completion_pct']}%)\n")

    for name, status in phase_status.items():
        icon = "+" if status["complete"] else "-"
        print(f"  [{icon}] {name}: {status['count']} artifacts")
        if args.verbose and status["artifacts"]:
            for a in status["artifacts"][:5]:
                print(f"       {a}")

    if section_info["missing"]:
        print(f"\n  Missing sections: {', '.join(section_info['missing'])}")
    if citation_info["missing"]:
        print(f"  Missing citations: {len(citation_info['missing'])}")
    if figure_info["missing"]:
        print(f"  Missing figures: {', '.join(figure_info['missing'])}")

    if next_steps:
        print(f"\n  Next steps:")
        for step in next_steps:
            print(f"    -> {step}")

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"\n  Checkpoint saved to {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
