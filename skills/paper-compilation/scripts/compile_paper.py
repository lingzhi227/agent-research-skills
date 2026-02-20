#!/usr/bin/env python3
"""Compile a LaTeX paper to PDF with error detection.

Runs the full pdflatex → bibtex → pdflatex → pdflatex pipeline,
reports errors, and optionally runs chktex for style checking.

Self-contained: uses only stdlib.

Adapted from AI-Scientist (compile_latex) and data-to-paper (save_latex_and_compile_to_pdf).

Usage:
    python compile_paper.py paper/main.tex
    python compile_paper.py paper/main.tex --check-style
    python compile_paper.py paper/main.tex --output paper/output.pdf
"""

import argparse
import os
import re
import shutil
import subprocess
import sys


def run_command(cmd: list[str], cwd: str, timeout: int = 60) -> tuple[int, str, str]:
    """Run a command and return (returncode, stdout, stderr)."""
    try:
        result = subprocess.run(
            cmd, cwd=cwd,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, timeout=timeout,
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", f"Command timed out after {timeout}s: {' '.join(cmd)}"
    except FileNotFoundError:
        return -2, "", f"Command not found: {cmd[0]}"


def check_bib_exists(tex_content: str) -> bool:
    """Check if the tex file references a bibliography."""
    return bool(re.search(r"\\bibliography\{", tex_content) or
                re.search(r"\\begin\{filecontents\}\{.*\.bib\}", tex_content) or
                re.search(r"\\addbibresource\{", tex_content))


def extract_errors(log_content: str) -> list[str]:
    """Extract LaTeX errors from log file."""
    errors = []
    lines = log_content.split("\n")
    for i, line in enumerate(lines):
        if line.startswith("! "):
            # Grab the error line and a few lines of context
            context = lines[i:i+5]
            errors.append("\n".join(context))
    return errors


def extract_warnings(log_content: str) -> list[str]:
    """Extract significant warnings from log file."""
    warnings = []
    for line in log_content.split("\n"):
        line = line.strip()
        if "Overfull \\hbox" in line:
            warnings.append(line)
        elif "Underfull \\vbox" in line:
            warnings.append(line)
        elif "Citation" in line and "undefined" in line:
            warnings.append(line)
        elif "Reference" in line and "undefined" in line:
            warnings.append(line)
        elif "LaTeX Warning: There were undefined references" in line:
            warnings.append(line)
    return warnings


def count_pages(pdf_path: str) -> int | None:
    """Try to count PDF pages using python."""
    try:
        with open(pdf_path, "rb") as f:
            content = f.read()
        # Simple heuristic: count /Type /Page entries
        count = len(re.findall(rb"/Type\s*/Page[^s]", content))
        return count if count > 0 else None
    except Exception:
        return None


def compile_latex(tex_file: str, output_pdf: str | None = None,
                  check_style: bool = False, timeout: int = 60) -> bool:
    """Compile LaTeX to PDF. Returns True on success."""
    tex_file = os.path.abspath(tex_file)
    if not os.path.exists(tex_file):
        print(f"Error: {tex_file} not found", file=sys.stderr)
        return False

    cwd = os.path.dirname(tex_file)
    basename = os.path.splitext(os.path.basename(tex_file))[0]

    with open(tex_file, encoding="utf-8", errors="replace") as f:
        tex_content = f.read()

    has_bib = check_bib_exists(tex_content)

    # Build compilation sequence
    commands = [
        ["pdflatex", "-interaction=nonstopmode", "-halt-on-error", os.path.basename(tex_file)],
    ]
    if has_bib:
        commands.append(["bibtex", basename])
        commands.append(["pdflatex", "-interaction=nonstopmode", os.path.basename(tex_file)])
    commands.append(["pdflatex", "-interaction=nonstopmode", os.path.basename(tex_file)])

    print(f"Compiling {tex_file}")
    print(f"  Working directory: {cwd}")
    print(f"  Bibliography: {'yes' if has_bib else 'no'}")
    print(f"  Passes: {len(commands)}")
    print()

    all_stdout = ""
    success = True

    for i, cmd in enumerate(commands):
        step_name = cmd[0] + (" (pass 1)" if i == 0 else f" (pass {i+1})" if cmd[0] == "pdflatex" else "")
        print(f"  [{i+1}/{len(commands)}] {step_name}...", end=" ")

        rc, stdout, stderr = run_command(cmd, cwd, timeout)
        all_stdout += stdout

        if rc == -2:
            print(f"FAILED - {cmd[0]} not installed")
            print(f"\n  Install LaTeX:")
            print(f"    macOS:  brew install --cask mactex-no-gui")
            print(f"    Ubuntu: sudo apt install texlive-full")
            return False
        elif rc == -1:
            print(f"TIMEOUT ({timeout}s)")
            success = False
        elif rc != 0 and cmd[0] == "pdflatex" and i == 0:
            # First pass failure is critical
            print("FAILED")
            errors = extract_errors(stdout)
            if errors:
                print("\n  Errors found:")
                for err in errors[:5]:
                    for line in err.split("\n"):
                        print(f"    {line}")
            success = False
            break
        else:
            print("OK")

    # Check for output PDF
    pdf_path = os.path.join(cwd, f"{basename}.pdf")
    if os.path.exists(pdf_path):
        if output_pdf:
            shutil.copy2(pdf_path, output_pdf)
            pdf_path = output_pdf
        pages = count_pages(pdf_path)
        size_kb = os.path.getsize(pdf_path) / 1024

        print(f"\n  Output: {pdf_path}")
        print(f"  Size: {size_kb:.0f} KB")
        if pages:
            print(f"  Pages: {pages}")
    else:
        print(f"\n  ERROR: No PDF produced")
        success = False

    # Warnings
    warnings = extract_warnings(all_stdout)
    if warnings:
        print(f"\n  Warnings ({len(warnings)}):")
        for w in warnings[:10]:
            print(f"    {w}")
        if len(warnings) > 10:
            print(f"    ... and {len(warnings) - 10} more")

    # Errors in final pass
    errors = extract_errors(all_stdout)
    if errors and success:
        print(f"\n  Non-fatal errors ({len(errors)}):")
        for err in errors[:3]:
            first_line = err.split("\n")[0]
            print(f"    {first_line}")

    # Style check with chktex
    if check_style:
        print(f"\n  Running chktex...")
        rc, stdout, stderr = run_command(
            ["chktex", "-q", "-n2", "-n24", "-n13", "-n1", os.path.basename(tex_file)],
            cwd, timeout=30
        )
        if rc == -2:
            print("    chktex not installed (optional)")
        elif stdout.strip():
            issues = [l for l in stdout.strip().split("\n") if l.strip()]
            print(f"    Style issues ({len(issues)}):")
            for issue in issues[:10]:
                print(f"      {issue}")
        else:
            print("    No style issues found")

    # Citation/reference stats
    cite_count = len(re.findall(r"\\cite[a-z]*\{", tex_content))
    ref_count = len(re.findall(r"\\ref\{", tex_content))
    fig_count = len(re.findall(r"\\includegraphics", tex_content))
    table_count = len(re.findall(r"\\begin\{table", tex_content))
    undef_cites = len([w for w in warnings if "Citation" in w and "undefined" in w])
    undef_refs = len([w for w in warnings if "Reference" in w and "undefined" in w])

    print(f"\n  Stats:")
    print(f"    Citations: {cite_count} used, {undef_cites} undefined")
    print(f"    References: {ref_count} used, {undef_refs} undefined")
    print(f"    Figures: {fig_count}")
    print(f"    Tables: {table_count}")

    status = "SUCCESS" if success else "FAILED"
    print(f"\n  Result: {status}")

    return success


def main():
    parser = argparse.ArgumentParser(description="Compile LaTeX paper to PDF")
    parser.add_argument("tex_file", help="Main .tex file")
    parser.add_argument("--output", "-o", help="Output PDF path")
    parser.add_argument("--check-style", action="store_true", help="Run chktex style check")
    parser.add_argument("--timeout", type=int, default=60, help="Timeout per command (seconds)")
    parser.add_argument("--auto-fix", action="store_true", help="Auto-fix errors and retry (up to 3 rounds)")
    args = parser.parse_args()

    success = compile_latex(
        args.tex_file,
        output_pdf=args.output,
        check_style=args.check_style,
        timeout=args.timeout,
    )

    if not success and args.auto_fix:
        fix_script = os.path.join(os.path.dirname(__file__), "fix_latex_errors.py")
        if os.path.exists(fix_script):
            for attempt in range(1, 4):
                print(f"\n--- Auto-fix attempt {attempt}/3 ---")
                fix_cmd = [sys.executable, fix_script, "--tex", args.tex_file, "--auto-detect",
                           "--output", args.tex_file]
                import subprocess as _subprocess
                result = _subprocess.run(fix_cmd, capture_output=True, text=True)
                if result.stdout:
                    print(result.stdout)
                if result.stderr:
                    print(result.stderr, file=sys.stderr)
                success = compile_latex(
                    args.tex_file,
                    output_pdf=args.output,
                    check_style=args.check_style,
                    timeout=args.timeout,
                )
                if success:
                    print(f"\nAuto-fix succeeded on attempt {attempt}!")
                    break

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
