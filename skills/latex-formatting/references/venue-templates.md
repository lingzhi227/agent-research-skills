# Conference Venue Templates Reference

## Venue Specifications

| Venue | Pages | Columns | Style | Anonymous | Refs Extra |
|-------|-------|---------|-------|-----------|------------|
| NeurIPS | 9 | 1 | neurips_2025.sty | Yes | Yes |
| ICML | 8 | 2 | icml2025.sty | Yes | Yes |
| ICLR | 9 | 1 | iclr2025_conference.sty | Yes | Yes |
| AAAI | 7+1 | 2 | aaai25.sty | Yes | 1 extra |
| ACL/EMNLP | 8 | 2 | acl.sty | Yes | Yes |
| CVPR/ICCV | 8 | 2 | cvpr.sty | Yes | Yes |
| ICBINB | 4 | 2 | icbinb.sty | Yes | Yes |
| arXiv | ∞ | 1 | article.cls | No | N/A |

## Standard Project Structure

```
paper/
├── main.tex
├── references.bib
├── sections/
│   ├── abstract.tex
│   ├── introduction.tex
│   ├── related_work.tex
│   ├── background.tex
│   ├── methods.tex
│   ├── experiments.tex
│   ├── results.tex
│   └── conclusion.tex
├── figures/
├── tables/
└── appendix/
    └── appendix.tex
```

## Essential Packages (always include)

```latex
\usepackage{amsmath,amssymb,amsthm}  % Math
\usepackage{graphicx}                 % Figures
\usepackage{booktabs}                 % Professional tables
\usepackage{hyperref}                 % Clickable references
\usepackage{algorithm,algpseudocode}  % Algorithms
\usepackage{subcaption}               % Subfigures
\usepackage{xcolor}                   % Colors
\usepackage{enumitem}                 % List customization
\usepackage{multirow}                 % Table multi-row
\usepackage{cleveref}                 % Smart references
\usepackage{microtype}                % Better typography
```

## Common Custom Commands

```latex
\DeclareMathOperator*{\argmin}{arg\,min}
\DeclareMathOperator*{\argmax}{arg\,max}
\newcommand{\norm}[1]{\left\| #1 \right\|}
\newcommand{\abs}[1]{\left| #1 \right|}
\newcommand{\ie}{\textit{i.e.}}
\newcommand{\eg}{\textit{e.g.}}
\newcommand{\etal}{\textit{et al.}}

% Remove before submission:
\newcommand{\todo}[1]{\textcolor{red}{[TODO: #1]}}
```

## Anonymization Checklist

- [ ] No author names in `\author{}`
- [ ] No "our previous work [X]" or "we previously showed"
- [ ] No GitHub/institutional URLs
- [ ] No acknowledgments section
- [ ] No grant numbers or funding info
- [ ] Supplementary material is anonymous too
