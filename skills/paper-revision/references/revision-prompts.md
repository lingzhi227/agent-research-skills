# Paper Revision Prompts

Extracted from AI-Scientist (perform_improvement) and AgentLaboratory (report_refinement).

## Concern Classification

```
For each reviewer comment, classify as:

| Type | Description | Priority |
|------|-------------|----------|
| Major Revision | Fundamental flaw, missing experiment, wrong methodology | P0 |
| Minor Revision | Clarity issues, missing details, presentation | P1 |
| Question | Reviewer seeks clarification | P2 |
| Suggestion | Nice-to-have improvement | P3 |
```

## Revision Planning Template

```
For each concern:

Concern: [Extracted reviewer concern]
Type: [Major/Minor/Question/Suggestion]
Affected Section(s): [Section name(s)]
Required Action: [Clarification/Experiment/Analysis/Structural/Citation]
Plan:
  - Step 1: ...
  - Step 2: ...
New Content Needed: [Yes/No - describe if yes]
```

## Revision Execution (AgentLaboratory)

### Full Pipeline Re-run
When a major revision requires new experiments:
```
1. Save current state:
   prev_code = current_code
   prev_results = current_results
   prev_paper = current_paper

2. Inject reviewer feedback as notes:
   notes += "Reviewer requested: {concern}"

3. Re-run affected phases:
   - If new experiment needed: re-run experiment phase
   - If new analysis needed: re-run analysis phase
   - Always re-run writing phase for affected sections

4. Compare new vs previous:
   - Score improvement: new_score - prev_score
   - Verify concern addressed
```

## Targeted Edit Prompts

### For Clarification Concerns
```
The reviewer found this passage unclear:
"{original_text}"

Their comment: "{reviewer_comment}"

Rewrite the passage to address the reviewer's concern.
Keep the same meaning but improve clarity.
Mark revised text with \textcolor{blue}{...}.
```

### For Missing Experiment Concerns
```
The reviewer requests: "{reviewer_comment}"

Current experimental setup: {current_setup}
Available resources: {resources}

Design a new experiment to address this concern:
1. What to test
2. Expected outcome
3. How to present results (table/figure)
```

### For Citation Concerns
```
The reviewer suggests citing: "{suggested_area}"

Search for relevant papers and add citations.
Integrate citations naturally into the text.
Do not just add a parenthetical — explain the connection.
```

## Change Marking

```latex
% Use blue text for all revisions
\usepackage{xcolor}
\newcommand{\revision}[1]{\textcolor{blue}{#1}}

% Example usage:
\revision{We additionally evaluate on the CIFAR-100 dataset
to address the reviewer's concern about generalization.}
```

## Revision Verification Checklist

```
After all revisions:
[ ] Every reviewer concern has been addressed
[ ] All revised text is marked in blue
[ ] New results are from actual experiments (not fabricated)
[ ] Page count still fits venue requirements
[ ] No new LaTeX errors introduced
[ ] All new citations are in .bib file
[ ] Self-review score improved or maintained
[ ] Revision summary cross-references every concern
```

## Revision Summary Template

```
# Revision Summary

## Changes Overview
- N sections modified
- M new experiments added
- K new figures/tables added

## Detailed Changes

### Reviewer 1, Concern 1 (Major)
**Concern**: [what they said]
**Action**: [what we did]
**Location**: Section X, paragraph Y
**New content**: [brief description]

### Reviewer 1, Concern 2 (Minor)
...

## Score Comparison
| Metric | Before | After |
|--------|--------|-------|
| Overall | 5 | 7 |
| Clarity | 6 | 8 |
| ...    | ... | ... |
```
