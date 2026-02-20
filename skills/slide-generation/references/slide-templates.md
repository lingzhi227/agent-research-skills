# Slide Generation Templates

Beamer LaTeX templates and layout patterns for research presentations.

## Full Beamer Template

```latex
\documentclass[aspectratio=169]{beamer}
\usetheme{metropolis}
\usepackage{appendixnumberbeamer}
\usepackage{booktabs}
\usepackage{amsmath,amssymb}
\usepackage{graphicx}
\usepackage{xcolor}

% Custom colors
\definecolor{primaryblue}{HTML}{2C3E50}
\definecolor{accentorange}{HTML}{E67E22}
\setbeamercolor{frametitle}{bg=primaryblue}

\title{Paper Title Here}
\subtitle{Conference Name, Year}
\author{Author 1 \and Author 2}
\institute{University / Lab}
\date{\today}

\begin{document}

\maketitle

\begin{frame}{Outline}
\tableofcontents
\end{frame}

% --- MOTIVATION ---
\section{Motivation}

\begin{frame}{Problem Statement}
\begin{itemize}
    \item What is the problem?
    \item Why does it matter?
    \item What are the challenges?
\end{itemize}
\end{frame}

\begin{frame}{Existing Approaches Fall Short}
\begin{columns}[T]
\column{0.5\textwidth}
\textbf{Method A}
\begin{itemize}
    \item Pro: ...
    \item Con: ...
\end{itemize}

\column{0.5\textwidth}
\textbf{Method B}
\begin{itemize}
    \item Pro: ...
    \item Con: ...
\end{itemize}
\end{columns}

\vspace{1em}
\textcolor{accentorange}{\textbf{Gap:}} Neither handles ...
\end{frame}

% --- METHOD ---
\section{Our Approach}

\begin{frame}{Key Idea}
\begin{center}
\includegraphics[width=0.8\textwidth]{figures/method_overview.png}
\end{center}
\end{frame}

\begin{frame}{Formulation}
\begin{equation}
\mathcal{L} = \mathcal{L}_{\text{task}} + \lambda \mathcal{L}_{\text{reg}}
\end{equation}

where:
\begin{itemize}
    \item $\mathcal{L}_{\text{task}}$: task-specific loss
    \item $\mathcal{L}_{\text{reg}}$: regularization term
    \item $\lambda$: trade-off parameter
\end{itemize}
\end{frame}

% --- RESULTS ---
\section{Results}

\begin{frame}{Main Results}
\begin{table}
\centering
\begin{tabular}{lcc}
\toprule
Method & Dataset A & Dataset B \\
\midrule
Baseline 1 & 42.3 & 38.7 \\
Baseline 2 & 44.1 & 40.2 \\
\textbf{Ours} & \textbf{48.9} & \textbf{45.3} \\
\bottomrule
\end{tabular}
\end{table}
\end{frame}

\begin{frame}{Visualization}
\begin{center}
\includegraphics[width=0.7\textwidth]{figures/results_plot.png}
\end{center}
\end{frame}

\begin{frame}{Ablation Study}
\begin{table}
\centering
\begin{tabular}{lc}
\toprule
Variant & Accuracy \\
\midrule
Full model & \textbf{48.9} \\
w/o Component A & 45.2 \\
w/o Component B & 46.7 \\
w/o Component C & 44.8 \\
\bottomrule
\end{tabular}
\end{table}
\end{frame}

% --- CONCLUSION ---
\section{Conclusion}

\begin{frame}{Summary}
\begin{itemize}
    \item \textbf{Contribution 1}: ...
    \item \textbf{Contribution 2}: ...
    \item \textbf{Contribution 3}: ...
\end{itemize}

\vspace{1em}
\textbf{Limitations \& Future Work:}
\begin{itemize}
    \item Limitation 1 → Future direction
    \item Limitation 2 → Future direction
\end{itemize}
\end{frame}

\begin{frame}[standout]
Thank You!

\vspace{1em}
\small{Code: \url{https://github.com/...}}
\end{frame}

\end{document}
```

## Slide Layout Patterns

### Two-Column with Figure
```latex
\begin{frame}{Title}
\begin{columns}[T]
\column{0.45\textwidth}
\begin{itemize}
    \item Point 1
    \item Point 2
    \item Point 3
\end{itemize}

\column{0.55\textwidth}
\includegraphics[width=\textwidth]{figure.png}
\end{columns}
\end{frame}
```

### Full-Width Figure with Caption
```latex
\begin{frame}{Method Overview}
\begin{center}
\includegraphics[width=0.85\textwidth]{overview.png}
\end{center}
\vspace{-0.5em}
\small{Our method consists of three stages: encoding, processing, and decoding.}
\end{frame}
```

### Equation Highlight Box
```latex
\begin{frame}{Key Equation}
\begin{block}{Main Result}
\begin{equation}
f(x) = \sum_{i=1}^{N} \alpha_i K(x, x_i)
\end{equation}
\end{block}

\textbf{Intuition:} The output is a weighted combination of kernel evaluations.
\end{frame}
```

### Before/After Comparison
```latex
\begin{frame}{Improvement}
\begin{columns}[T]
\column{0.5\textwidth}
\centering
\textbf{Before}
\includegraphics[width=0.9\textwidth]{before.png}

\column{0.5\textwidth}
\centering
\textbf{After (Ours)}
\includegraphics[width=0.9\textwidth]{after.png}
\end{columns}
\end{frame}
```

## Poster Template (a0poster)

```latex
\documentclass[a0,portrait]{a0poster}
\usepackage{multicol}
\usepackage{graphicx}
\usepackage{booktabs}

\begin{document}

% Title
\begin{center}
{\VeryHuge \textbf{Paper Title}} \\[1cm]
{\Large Author 1, Author 2 — University}
\end{center}

\begin{multicols}{3}

% Column 1: Introduction
\section*{Introduction}
Problem description and motivation...

\section*{Related Work}
Key prior work...

% Column 2: Methods
\section*{Method}
\includegraphics[width=\columnwidth]{method.png}

Key equation:
$$\mathcal{L} = \mathcal{L}_{\text{task}} + \lambda \mathcal{L}_{\text{reg}}$$

% Column 3: Results
\section*{Results}
\includegraphics[width=\columnwidth]{results.png}

\begin{tabular}{lcc}
\toprule
Method & Acc & F1 \\
\midrule
Baseline & 42.3 & 40.1 \\
\textbf{Ours} & \textbf{48.9} & \textbf{46.5} \\
\bottomrule
\end{tabular}

\section*{Conclusion}
Summary of contributions...

\section*{References}
\small{[1] Author et al., Title, Venue, Year.}

\end{multicols}
\end{document}
```

## Content Extraction Rules

```
From the paper, extract for slides:
1. Title, authors, affiliations → Title slide
2. Abstract sentences 1-2 → Motivation
3. Contribution bullet points → Summary slide
4. Method figure (if exists) → Method overview slide
5. Key equations (numbered) → Formulation slide (simplify if needed)
6. Main results table → Results slide (reduce columns if > 5)
7. Best result figures → Visualization slides
8. Ablation table → Ablation slide
9. Limitations paragraph → Conclusion slide
10. Future work paragraph → Conclusion slide
```

## Presentation Tips

```
- 1 minute per slide (15 slides for 15-min talk)
- Max 6 bullet points per slide
- Max 30 words per slide (excluding equations/tables)
- Figures should fill at least 50% of the slide
- Use animations sparingly
- Include slide numbers
- Consistent color scheme
- Font size: title ≥ 24pt, body ≥ 18pt, caption ≥ 14pt
```
