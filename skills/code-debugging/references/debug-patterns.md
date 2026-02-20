# Code Debugging Patterns

Extracted from data-to-paper (debugger.py, run_issues.py), AI-Scientist-v2, and AgentLaboratory.

## Error Severity Hierarchy (data-to-paper)

```python
class CodeProblem(IndexOrderedEnum):
    NoCode = 'No code'                                    # Most severe
    IncompleteBlock = 'Incomplete block'
    NotSingleBlock = 'Not single block'
    StaticCheck = 'Static check'
    TimeoutError = 'Timeout error'
    RuntimeError = 'Runtime error'
    SyntaxError = 'Syntax error'
    MissingOutputFiles = 'Missing output files'
    NonBreakingRuntimeIssue = 'Non-breaking runtime issue'
    OutputFileCallingSyntax = 'Output file calling syntax'
    OutputFileContentA = 'Output file content first check'
    OutputFileContinuity = 'Check dependency on previous output'
    OutputFileContentB = 'Output file content second check'
    OutputFileCompilation = 'Output file failed compilation'
    OutputFileAnnotation = 'Output file annotation'
    AllOK = 'All OK'                                      # Least severe
```

## RunIssue Structure (data-to-paper)

```python
@dataclass
class RunIssue:
    code_problem: CodeProblem  # Severity category
    category: str              # e.g., "Importing packages", "Timeout"
    item: str                  # Specific file/function name
    issue: str                 # Problem description
    instructions: str          # How to fix
    comment: str               # Internal note
    requesting_small_change: bool  # Minor fix vs major rewrite
    forgive_after: int         # Forgive after N occurrences (None = never)
```

## Fix Strategy State Machine (data-to-paper)

### Action Matrix
```
                    Stage 0      Stage 1              Stage 2
                    (initial)    (1st revision)       (2nd revision)
incomplete         regen0       regen1               regen1
not_single_block   leave        regen1               regen2
static_check       repost0      repost0/regen1       regen2
run_failed         repost0      repost0/leave        repost1
missing_files      repost0      repost0/leave        repost0/regen1
run_completed      repost0      repost0              repost0
```

### Action Definitions

- **repost[N]**: Rewind conversation to stage N, post code as fresh response
  - Stage 0: "Here is the code to perform the requested analysis:"
  - Stage 1: "Here is the revised code to perform the requested analysis:"

- **regen[N]**: Delete messages back to stage N, regenerate from scratch
  - Resets `requesting_small_change` flag

- **leave**: Keep current response, post issue feedback requesting small change

### Conditional Actions (A/B)
When action contains "/": `action1/action2`
- If current problem severity ≥ previous: use action1
- Else: use action2

## Common Error Patterns

### Device Mismatch (PyTorch)
```
RuntimeError: Expected all tensors to be on the same device
Fix: Add .to(device) or ensure consistent device placement
```

### Shape Mismatch
```
RuntimeError: mat1 and mat2 shapes cannot be multiplied
Fix: Check tensor dimensions, add .reshape() or .view()
```

### Missing Data Normalization
```
Symptom: Loss is NaN or Inf
Fix: Add input normalization, check for zero-division
```

### Off-by-One Indexing
```
IndexError: index X is out of bounds for axis Y with size Z
Fix: Check loop bounds, array indexing
```

### Incorrect Loss Function
```
Symptom: Training loss doesn't decrease
Fix: Match loss function to task type:
- Classification: CrossEntropyLoss (not MSE)
- Regression: MSELoss (not CrossEntropy)
- Multi-label: BCEWithLogitsLoss
```

## Automated Code Repair Prompt (AgentLaboratory)

```
You are a code repair specialist. Given:
1. The original code
2. The error message
3. The traceback

Identify the root cause and apply a MINIMAL fix:
- Do not rewrite working code
- Fix only the lines causing the error
- Preserve the original logic and structure
- Explain why the error occurred
```

## Truncation Rules

- Error output: Keep last 1500 characters of stderr
- Stack trace: Keep the last frame (most relevant)
- Code context: Show 5 lines before/after the error line

## Reflection After Fix

```
After fixing the error:
1. Why did this error occur?
2. Which specific lines caused it?
3. What was the fix (line-by-line)?
4. What pattern should be avoided in future?
```
