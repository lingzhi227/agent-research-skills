# Atomic Decomposition Prompts

Extracted from AI-Researcher (survey_agent.py) — the core innovation of atomic concept decomposition.

## Decomposition System Prompt

```
You are an expert research analyst. Your task is to decompose a research
idea or method into atomic, self-contained concepts.

Each atomic concept must:
1. Be a single, well-defined concept
2. Have a clear mathematical formulation (extractable from papers)
3. Be implementable as a code module
4. Be traceable to specific reference papers

Do not combine multiple concepts into one atom.
If unsure about atomicity, break down further.
```

## Step 1: Initial Decomposition

```
Given the research idea:
"{idea_description}"

Break this down into atomic definitions. For each atom:
- Name: A concise, specific name
- Definition: One-sentence description
- Category: {mathematical_concept, algorithm, loss_function,
             architecture_component, training_technique, data_processing}
- Dependencies: Which other atoms this depends on

Example decomposition for "Graph Attention Network":
1. Message Passing → Graph convolution operation
2. Attention Coefficient → Learnable edge weights
3. Multi-Head Attention → Parallel attention mechanisms
4. Softmax Normalization → Attention weight normalization
```

## Step 2A: Paper Survey (Math Formula Extraction)

```
For the atomic concept: "{atom_name}"
Definition: "{atom_definition}"

Search academic papers to find:
1. The original paper that introduced this concept
2. The exact mathematical formulation (LaTeX)
3. Key assumptions and constraints
4. Any important variants or extensions

Output format:
{
  "math_formula": "Z = \\text{softmax}((\\log \\pi + g) / \\tau)",
  "formula_explanation": "Gumbel-Softmax reparameterization trick",
  "reference_papers": [
    {"title": "...", "year": 2017, "where_in_paper": "Equation 3"}
  ],
  "assumptions": ["Differentiable relaxation of discrete sampling"],
  "variants": ["Straight-through estimator variant"]
}
```

## Step 2B: Code Survey (Implementation Extraction)

```
For the atomic concept: "{atom_name}"
Math formula: "{math_formula}"

Search code repositories to find:
1. A clean, reference implementation
2. Key implementation details not in the paper
3. Common pitfalls and workarounds
4. Popular library implementations (PyTorch, TensorFlow, JAX)

Output format:
{
  "code_implementation": "def gumbel_softmax(logits, tau=1.0): ...",
  "language": "Python/PyTorch",
  "reference_codebases": ["github_user/repo_name"],
  "implementation_notes": ["Use log-sum-exp trick for numerical stability"],
  "common_pitfalls": ["Temperature must be > 0"]
}
```

## Step 2C: Knowledge Entry Template

```json
{
  "definition": "Kernelized Gumbel-Softmax Operator",
  "category": "mathematical_concept",
  "math_formula": "Z = \\text{softmax}((\\log \\pi + g) / \\tau), g \\sim \\text{Gumbel}(0,1)",
  "formula_source": "Equation 3 in Jang et al., 2017",
  "code_implementation": "def gumbel_softmax(logits, tau=1.0):\n    gumbels = -torch.log(-torch.log(torch.rand_like(logits)))\n    y = (logits + gumbels) / tau\n    return F.softmax(y, dim=-1)",
  "reference_papers": ["Categorical Reparameterization with Gumbel-Softmax"],
  "reference_codebases": ["jang-e/gumbel-softmax"],
  "assumptions": [
    "Differentiable relaxation of discrete sampling",
    "Temperature τ controls smoothness of approximation"
  ],
  "connections": ["Used in Component X of the proposed method"],
  "dependencies": ["softmax_function", "gumbel_distribution"]
}
```

## Step 3: Consistency Verification

```
Verify the knowledge base:

1. Math → Code completeness:
   For every math formula, verify there is a corresponding code implementation.
   Flag any formulas without code.

2. Code → Math completeness:
   For every code module, verify it traces to a formal mathematical definition.
   Flag any code without theory.

3. Cross-reference consistency:
   - Variable names in code match notation in formulas
   - Parameter counts match between formula and code
   - Input/output dimensions are consistent

4. Dependency graph:
   - No circular dependencies
   - All dependencies are satisfied
   - Topological order is well-defined
```

## Gap Analysis Template

```
After decomposition, identify gaps:

| Atom | Has Math? | Has Code? | Gap Type |
|------|-----------|-----------|----------|
| atom_1 | ✓ | ✓ | None |
| atom_2 | ✓ | ✗ | Needs implementation |
| atom_3 | ✗ | ✓ | Needs formalization |
| atom_4 | ✗ | ✗ | Needs both |

Priority: Address "Needs both" first, then "Needs formalization",
then "Needs implementation".
```
