# Related Work Writing Prompts Reference

## Per-Section Tips (from AI-Scientist + AgentLaboratory)

### Related Work Section Guidelines
```
- Academic siblings of our work, i.e. alternative attempts in literature at trying to solve the same problem.
- Goal is to "Compare and contrast" — how does their approach differ in either assumptions or method?
- If their method is applicable to our Problem Setting, I expect a comparison in the experimental section.
- If not, there needs to be a clear statement why a given method is not applicable.
- Note: Just describing what another paper is doing is not enough. We need to compare and contrast.
- Organize by theme, not chronologically.
- Cite broadly — not just the most popular papers.
```

## Writing Strategy

### Step 1: Thematic Clustering
Organize cited papers into thematic groups. Common themes:

1. **Problem formulation variants** — Different ways the same problem has been formulated
2. **Methodology families** — Groups of methods sharing a core technique (e.g., attention-based, graph-based)
3. **Application domains** — Where similar techniques have been applied
4. **Evaluation approaches** — Different benchmarks or evaluation paradigms
5. **Theoretical foundations** — Relevant theoretical results

### Step 2: Per-Theme Paragraph Structure

```
[Topic sentence introducing the theme]
[Key work 1: what they did + how it relates to ours]
[Key work 2: what they did + contrast with work 1 and ours]
[Key work 3: extension or variation]
[Summary: what's missing / our advantage in this theme]
```

### Step 3: Comparison Patterns

**Assumption differences:**
```latex
Unlike \citet{smith2023} who assume access to labeled data, our method operates in a fully unsupervised setting.
```

**Methodology differences:**
```latex
While \citet{jones2024} employ a two-stage pipeline, our approach integrates feature extraction and classification in an end-to-end manner, avoiding the error propagation inherent in decoupled approaches.
```

**Scope differences:**
```latex
\citet{chen2023} address the related problem of X in the context of Y. Our work differs in that we consider the more general setting of Z, which subsumes their formulation as a special case.
```

**Complementary work:**
```latex
Complementary to our approach, \citet{wang2024} propose a method for X that could potentially be combined with our framework to further improve performance.
```

## LaTeX Patterns

### Citation Commands
- `\cite{key}` — Parenthetical: (Smith et al., 2024)
- `\citet{key}` — Textual: Smith et al. (2024) — preferred for subject position
- `\citep{key}` — Same as `\cite` in most styles
- `\citeauthor{key}` — Just the name: Smith et al.

### Example Paragraph

```latex
\paragraph{Attention Mechanisms.}
The seminal work of \citet{vaswani2017attention} introduced the Transformer architecture,
which relies entirely on self-attention mechanisms. Subsequent works have sought to
reduce the quadratic complexity of attention. \citet{kitaev2020reformer} propose locality-sensitive
hashing to approximate attention, while \citet{wang2020linformer} project keys and values
to a lower-dimensional space. Unlike these approaches, which sacrifice exact attention
computation for efficiency, our method maintains exact attention while achieving
sub-quadratic complexity through a novel sparse attention pattern that
exploits the inherent structure of the input data.
```

## Refinement Checklist

- [ ] Every cited paper has a clear reason for inclusion
- [ ] The section is organized by theme, not chronologically
- [ ] Each paragraph compares and contrasts, not just describes
- [ ] Our work's novelty is clear from the comparisons
- [ ] All `\cite{}` / `\citet{}` keys exist in the `.bib` file
- [ ] Recent work (last 2-3 years) is well-represented
- [ ] Foundational/seminal papers are included where relevant
- [ ] No self-citations that violate anonymization
- [ ] The section positions our work clearly at the end
