# Novelty Assessment Prompts

Extracted from AI-Scientist (check_idea_novelty in generate_ideas.py), data-to-paper, and SciMON.

## Harsh Critic System Prompt (AI-Scientist)

```
You are a harsh but fair academic critic. Your task is to determine whether
a research idea is truly novel or merely a trivial extension of existing work.

Be a harsh critic for novelty. Ensure there is a sufficient contribution
for a new conference or workshop paper. You will be given access to the
Semantic Scholar API to survey the literature and check whether the
proposed idea already exists.

A trivial extension of existing work is NOT novel. The idea must offer
a meaningfully different approach, formulation, or insight.
```

## Multi-Round Search Protocol (AI-Scientist)

```
Round {N} of novelty assessment:

Idea: {idea_description}

Previous search queries and results:
{previous_rounds}

Instructions:
1. Generate a NEW search query that hasn't been tried before
2. Focus on the most specific aspect of the idea
3. Try to find the MOST SIMILAR existing paper
4. Consider different phrasings and related concepts

Search query: [your query]

After reviewing results:
- Most relevant paper found: [title]
- Overlap with our idea: [description]
- Key difference: [description]

Decision: [CONTINUE_SEARCHING / NOVEL / NOT_NOVEL]
Reasoning: [explanation]
```

## Search Query Generation Strategies

```
For a given research idea, generate queries that target:

1. Direct match: Use the exact technique name
   e.g., "adaptive attention pruning gradient importance"

2. Component match: Search for individual components
   e.g., "attention head pruning", "gradient-guided importance scoring"

3. Application match: Search for same application with different methods
   e.g., "transformer efficiency attention reduction"

4. Method match: Search for same method in different applications
   e.g., "gradient-based pruning neural networks"

5. Concurrent work: Search recent arXiv preprints
   e.g., add year filter: 2024-2025
```

## Overlap Assessment Criteria

```
Rate the overlap between the idea and each found paper:

| Overlap Level | Description |
|---------------|-------------|
| None | Different problem and different method |
| Low | Same broad area but different specific approach |
| Medium | Similar approach but different formulation or application |
| High | Very similar approach with minor differences |
| Exact | Essentially the same idea |

An idea is NOT NOVEL if any paper has "High" or "Exact" overlap.
An idea MAY BE novel if all papers have "Medium" or lower overlap.
```

## Final Decision Prompt

```
After {N} rounds of searching, make your final decision:

Idea: {idea_description}

All papers found across all rounds:
{all_papers_with_overlap}

Consider:
1. Is there sufficient differentiation from ALL found papers?
2. Would this be accepted as a novel contribution at a top venue?
3. Is the novelty in the method, application, or both?
4. Could a reviewer reasonably reject this as "incremental"?

Decision: NOVEL / NOT_NOVEL
Confidence: HIGH / MEDIUM / LOW
Justification: [detailed reasoning]

If NOVEL, position the idea:
- Most similar papers (for Related Work section)
- How this idea specifically differs from each
- The gap this idea fills in the literature
```

## Novelty vs. Contribution Distinction

```
Note: Novelty alone is not sufficient. Also assess:

1. Technical novelty: New method/algorithm/formulation?
2. Empirical contribution: New benchmarks/datasets/evaluations?
3. Theoretical contribution: New proofs/bounds/analysis?
4. Application novelty: First to apply X to domain Y?

A paper needs at least one strong contribution type.
A "novel" combination of existing techniques may still be
insufficient if the combination is obvious.
```
