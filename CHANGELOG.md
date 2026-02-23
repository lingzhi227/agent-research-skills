# Changelog

All notable changes to this project will be documented in this file.

## [1.1.0] - 2026-02-23

### Added

- **github-research skill**: 6-phase pipeline for discovering, evaluating, and deeply analyzing GitHub repositories related to a research topic
  - Phase 1: Intake — extract refs, URLs, keywords from deep-research output
  - Phase 2: Discovery — multi-source GitHub search (repos, code, Papers With Code)
  - Phase 3: Filtering — score, rank, and select top repos
  - Phase 4: Deep Dive — clone and deeply analyze code structure, dependencies, implementations
  - Phase 5: Analysis — cross-repo comparison matrix, technique mapping, gap analysis
  - Phase 6: Blueprint — integration plan, reusable components catalog
- **13 Python scripts** for github-research: `extract_research_refs.py`, `search_github.py`, `search_github_code.py`, `search_paperswithcode.py`, `repo_db.py`, `repo_metadata.py`, `repo_readme_fetch.py`, `clone_repo.py`, `analyze_repo_structure.py`, `extract_dependencies.py`, `find_implementations.py`, `compare_repos.py`, `compile_github_report.py`
- **Phase guide reference** (`references/phase-guide.md`) with search strategy matrix and per-repo analysis templates

## [1.0.0] - 2026-02-20

### Added

- **30 research skills** covering the full academic paper lifecycle:
  - Phase 0: `deep-research`, `literature-search`, `literature-review`, `idea-generation`, `novelty-assessment`, `research-planning`
  - Phase 1: `atomic-decomposition`, `algorithm-design`, `math-reasoning`, `symbolic-equation`
  - Phase 2: `experiment-design`, `experiment-code`, `code-debugging`, `data-analysis`
  - Phase 3: `paper-writing-section`, `related-work-writing`, `survey-generation`, `paper-to-code`
  - Phase 4: `figure-generation`, `table-generation`, `citation-management`, `backward-traceability`
  - Phase 5: `latex-formatting`, `paper-compilation`, `excalidraw-skill`
  - Phase 6: `self-review`, `paper-revision`, `rebuttal-writing`, `slide-generation`, `paper-assembly`
- **20 Python scripts** with CLI interfaces (argparse + `--help`)
- **Slash command**: `/research <topic>` for deep literature reviews
- **Installer** (`install.sh`) with dependency checking and script verification
- **Design specifications** (`SKILLS_DESIGN.md`) extracted from 17 GitHub repos
- **Implementation checklist** (`SKILLS_IMPLEMENTED.md`)
