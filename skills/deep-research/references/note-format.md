# Note Format & Templates

## Per-Paper Note Template

Use this template when writing detailed notes for each paper read in Phase 2.

```markdown
### [@citation_key] Title of Paper

**Metadata**
- Authors: Author1, Author2, Author3
- Year: 2024 | Venue: NeurIPS
- arXiv: 2401.12345 | Citations: 150
- Code: https://github.com/org/repo

**Problem**
One sentence: what problem does this paper address?

**Key Contributions**
1. First major contribution
2. Second major contribution
3. Third major contribution

**Methodology**
- Approach type: (prompting / fine-tuning / RL / architecture / benchmark / ...)
- Key idea: Concise description of the core method
- Key components: List of major components or steps
- Novel aspects: What's new compared to prior work?

**Experiments**
- Datasets: List of datasets/benchmarks used
- Baselines: Key comparison methods
- Main results: 1-3 key quantitative findings
- Ablations: Key ablation findings

**Limitations**
- Acknowledged by authors:
- Observed by reader:

**Connections**
- Builds on: [@prior_work1], [@prior_work2]
- Extended by: [@follow_up1]
- Related approaches: [@related1], [@related2]

**Code & Resources**
- Repository: URL (stars, language, last updated)
- Datasets released: URL or name
- Models released: URL or name
```

## Survey Notes Template (Phase 1)

```markdown
# Survey: {Topic}
Date: YYYY-MM-DD | Papers found: N

## Search Queries Used
1. "query one" → N results
2. "query two" → N results
...

## Themes Identified

### Theme A: Name (N papers)
Key papers:
- [@key1] Title (Year, Citations) — one-line summary
- [@key2] Title (Year, Citations) — one-line summary

### Theme B: Name (N papers)
...

## Key Authors & Groups
- Author Name (Affiliation) — focus area, N papers in DB
- ...

## Venue Distribution
- arXiv preprints: N
- NeurIPS: N
- ICML: N
- ...

## Year Distribution
- 2024-2025: N papers
- 2022-2023: N papers
- Before 2022: N papers

## Initial Observations
- [High-level observation 1]
- [High-level observation 2]
```

## Synthesis Notes Template (Phase 3)

```markdown
# Synthesis: {Topic}

## Taxonomy
Topic
├── Category A
│   ├── Subcategory A1: [@key1], [@key2]
│   └── Subcategory A2: [@key3]
├── Category B
│   └── ...
└── Category C: [@key4], [@key5]

## Comparative Table
| Method | Paper | Task | Metric | Result | Code |
|--------|-------|------|--------|--------|------|
| Method1 | [@key1] | TaskX | Acc | 85.3% | ✓ |
| Method2 | [@key2] | TaskX | Acc | 87.1% | ✗ |

## Timeline
- **2017**: Foundation work — [@key] description
- **2020**: Key advance — [@key] description
- **2023**: Current SOTA — [@key] description

## Cross-Cutting Insights
1. Insight connecting multiple papers
2. Emerging consensus
3. Methodological trends
```

## Gap Analysis Template (Phase 4)

```markdown
# Gap Analysis: {Topic}

## Open Problems
1. **Problem Name**: Description. Mentioned by [@key1], [@key2].
2. ...

## Contradictions
1. [@key1] claims X, but [@key2] shows Y. Possible explanation: ...

## Missing Evaluations
- No evaluation on [benchmark/domain]
- Lack of real-world deployment studies
- Missing comparison between [method A] and [method B]

## Under-Explored Directions
1. **Direction**: Why it matters, what's needed
2. ...

## Concrete Research Questions
1. RQ1: ...
2. RQ2: ...
```

## Code Repository Tracking Format

```markdown
# Code Resources: {Topic}

## Key Repositories

### repo-name
- **URL**: https://github.com/org/repo
- **Paper**: [@citation_key] Title
- **Description**: What it implements
- **Language**: Python | Stars: 1.2k | Last updated: 2024-06
- **Notes**: Installation notes, key features

## Datasets
| Name | URL | Size | Task | Used by |
|------|-----|------|------|---------|
| Dataset1 | URL | 10K | Task | [@key1] |

## Benchmarks
| Name | URL | Papers using it | Metrics |
|------|-----|-----------------|---------|
| Bench1 | URL | [@key1], [@key2] | Acc, F1 |
```

## BibTeX Entry Format

Citation keys follow the pattern: `firstauthorlastnameYearfirsttitleword`

```bibtex
@article{vaswani2017attention,
  title = {Attention Is All You Need},
  author = {Ashish Vaswani and Noam Shazeer and Niki Parmar and ...},
  year = {2017},
  eprint = {1706.03762},
  archivePrefix = {arXiv},
  journal = {arXiv preprint arXiv:1706.03762},
}
```

Rules:
- Author last name: lowercase, ASCII only (strip accents)
- Year: 4 digits from publication date
- Title word: first non-article word (skip a/an/the/on/in/of/for/to/with/and/or), lowercase
- Collision handling: append a/b/c suffix (e.g., `smith2024transformera`, `smith2024transformerb`)
