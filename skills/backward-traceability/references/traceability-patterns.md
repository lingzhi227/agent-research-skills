# Backward Traceability Patterns

Extracted from data-to-paper (ref_numeric_values.py, referencable_text.py, latex_to_pdf.py).

## Core LaTeX Commands

### \hypertarget — Mark a Value in Code Output
```latex
% In code-generated output:
\hypertarget{R1a}{45.3}
% R1a = reference label, 45.3 = the value
```

### \hyperlink — Reference a Value in Paper Text
```latex
% In paper body:
Our method achieves \hyperlink{R1a}{45.3}\% accuracy.
% Clicking 45.3 in PDF jumps to the code output
```

### \num — Compile-Time Evaluated Formula
```latex
% Compute derived values at compile time:
\num{45.3 - 38.7, "accuracy improvement over baseline"}
% Evaluates to 6.6 and stores explanation
```

## Label Format Convention (data-to-paper)

```
Label = {prefix}{line_number}{letter}

prefix:     identifies the code block (e.g., "code", "R")
line_number: line in the code that produces the value
letter:      a, b, c... for multiple values on same line

Examples:
  code1a  → code block, line 1, 1st value
  code1b  → code block, line 1, 2nd value
  code12a → code block, line 12, 1st value
  R3c     → results block, line 3, 3rd value
```

Letter conversion (data-to-paper referencable_text.py):
```python
def _num_to_letters(num):
    """1→a, 2→b, ... 26→z, 27→aa, 28→ab, ..."""
    letters = ''
    while num > 0:
        num -= 1
        letters = chr(ord('a') + num % 26) + letters
        num //= 26
    return letters
```

## HypertargetPosition Modes (data-to-paper)

```python
class HypertargetPosition(Enum):
    WRAP = "wrap"          # \hypertarget{label}{value}
    ADJACENT = "adjacent"  # \hypertarget{label}{}value
    HEADER = "header"      # \hypertarget{label}{} (value elsewhere)
    NONE = "none"          # No hypertargets
```

## \num Implementation (data-to-paper latex_to_pdf.py)

```python
def evaluate_latex_num_command(latex_str, ref_prefix='',
                               enforce_explanation=True):
    r"""
    Evaluates \num{formula} or \num{formula, "explanation"} in latex.

    If ref_prefix provided, adds \hyperlink{ref_prefix?}{result}
    where ? is the index.

    Returns:
      - new_latex_str: with \num{} replaced by computed values
      - labels_to_notes: dict mapping labels to "formula = result"
    """
    # Available math functions for eval():
    namespace = {
        'exp': np.exp, 'log': np.log,
        'sin': np.sin, 'cos': np.cos, 'tan': np.tan,
        'pi': np.pi, 'e': np.e,
        'sqrt': np.sqrt, 'log2': np.log2, 'log10': np.log10,
        'abs': np.abs,
    }

    result = eval(formula_without_hyperlinks, namespace)

    # Create hyperlink:
    label = f'{ref_prefix}{index}'
    replace_with = f'\\hyperlink{{{label}}}{{{result}}}'

    # Store note:
    labels_to_notes[label] = f"{formula} = {result}"
    if explanation:
        labels_to_notes[label] += f" ({explanation})"
```

## Code Output Tagging Pattern

### Python Code (Experiment Script)
```python
# Tag every numeric output with hypertarget
def save_results_with_targets(results, prefix="R"):
    """Save results with LaTeX hypertarget tags."""
    lines = []
    line_no = 1
    for key, value in results.items():
        letter = 'a'
        if isinstance(value, dict):
            for subkey, subval in value.items():
                label = f"{prefix}{line_no}{letter}"
                lines.append(f"\\hypertarget{{{label}}}{{{subval:.4f}}}")
                letter = chr(ord(letter) + 1)
        else:
            label = f"{prefix}{line_no}a"
            lines.append(f"\\hypertarget{{{label}}}{{{value:.4f}}}")
        line_no += 1
    return lines
```

### Usage in Experiment
```python
results = {
    "accuracy": 0.453,
    "precision": 0.421,
    "recall": 0.487,
    "f1": 0.452,
}
tagged = save_results_with_targets(results)
# Output:
# \hypertarget{R1a}{0.4530}
# \hypertarget{R2a}{0.4210}
# \hypertarget{R3a}{0.4870}
# \hypertarget{R4a}{0.4520}
```

## Appendix Code Listing Template

```latex
\section*{Appendix A: Experiment Code}

\begin{lstlisting}[
  language=Python,
  basicstyle=\ttfamily\scriptsize,
  numbers=left,
  numberstyle=\tiny,
  escapechar=@,
  caption={Main experiment code with traceability anchors}
]
@\hypertarget{code1}{}@import torch
@\hypertarget{code2}{}@from model import MyModel

@\hypertarget{code5}{}@model = MyModel(hidden_dim=256)
@\hypertarget{code6}{}@optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)

@\hypertarget{code10}{}@for epoch in range(100):
@\hypertarget{code11}{}@    loss = train_epoch(model, train_loader)
@\hypertarget{code12}{}@    acc = evaluate(model, test_loader)

@\hypertarget{code15}{}@final_accuracy = evaluate(model, test_loader)
@\hypertarget{code16}{}@print(f"Final: {final_accuracy:.4f}")
\end{lstlisting}
```

## Calculation Notes Section

```latex
\section*{Appendix B: Calculation Notes}

The following values in this paper are computed from experimental results:

\begin{itemize}
\item \hyperlink{N1}{6.6}: $45.3 - 38.7 = 6.6$ (accuracy improvement)
\item \hyperlink{N2}{1.17}: $45.3 / 38.7 = 1.17$ (relative improvement)
\item \hyperlink{N3}{14.6}: $(45.3 - 38.7) / 45.3 \times 100 = 14.6$ (\% relative gain)
\end{itemize}
```

## Required LaTeX Packages

```latex
\usepackage{hyperref}    % For \hypertarget, \hyperlink
\usepackage{listings}    % For code listings with escapechar
\usepackage{xcolor}      % For colored hyperlinks (optional)

% Optional: make hyperlinks colored
\hypersetup{
    colorlinks=true,
    linkcolor=blue,
    citecolor=blue,
}
```

## Verification Checklist

```
For every number in the paper text:
[ ] Has a corresponding \hypertarget in code output
[ ] \hyperlink label matches the \hypertarget label
[ ] Value in text matches value in code output
[ ] Click-test: hyperlink in PDF jumps to correct location

For every \num{} command:
[ ] Formula evaluates correctly
[ ] Explanation is provided
[ ] Result matches expected value
[ ] Hyperlink (if ref_prefix) resolves correctly
```
