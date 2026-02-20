# Two-Pass Refinement Prompts

> Extracted verbatim from AI-Scientist `perform_writeup.py`.

## Error Checklist

When refining any section, check for these specific errors:
- Unenclosed math symbols
- Only reference figures that exist in our directory
- LaTeX syntax errors
- Numerical results that do not come from explicit experiments and logs
- Repeatedly defined figure labels
- References to papers that are not in the .bib file, DO NOT ADD ANY NEW CITATIONS!
- Unnecessary verbosity or repetition, unclear text
- Results or insights in the `notes.txt` that have not yet been included
- Any relevant figures that have not yet been included in the text
- Closing any `\begin{figure}` with a `\end{figure}` and `\begin{table}` with a `\end{table}`, etc.
- Duplicate headers, e.g. duplicated `\section{Introduction}` or `\end{document}`
- Unescaped symbols, e.g. `shakespeare_char` should be `shakespeare\_char` in text
- Incorrect closing of environments, e.g. `</end{figure}>` instead of `\end{figure}`

## Pass 1: Error Correction

```
Great job! Now criticize and refine only the {section} that you just wrote.
Make this complete in this pass, do not leave any placeholders.

Pay particular attention to fixing any errors such as:
[error checklist above]
```

## Pass 2: Compression and Polish

```
Criticize and refine the {section} only. Recall the advice:
{tips for this section}
Make this complete in this pass, do not leave any placeholders.

Pay attention to how it fits in with the rest of the paper.
Identify any redundancies (e.g. repeated figures or repeated text), if there are any, decide where in the paper things should be cut.
Identify where we can save space, and be more concise without weakening the message of the text.
Fix any remaining errors as before:
[error checklist above]
```

## Section Generation Prompt Template

For each section, use this pattern:

```
Please fill in the {section} of the writeup. Some tips are provided below:
{per_section_tips[section]}

Be sure to use \cite or \citet where relevant, referring to the works provided in the file.
Do not cite anything that is not already in references.bib. Do not add any new entries to this.

Keep the experimental results (figures and tables) only in the Results section, and make sure that any captions are filled in.
In this pass, do not reference anything in later sections of the paper.

Before every paragraph, please include a brief description of what you plan to write in that paragraph in a comment.
```

## Related Work Sketch (before citation harvesting)

```
Please fill in the Related Work of the writeup. Some tips are provided below:

{per_section_tips["Related Work"]}

For this section, very briefly sketch out the structure of the section, and clearly indicate what papers you intend to include.
Do this all in LaTeX comments using %.
The related work should be concise, only plan to discuss the most relevant work.
Do not modify references.bib to add any new citations, this will be filled in at a later stage.
```
