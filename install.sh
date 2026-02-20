#!/usr/bin/env bash
set -euo pipefail

# claude-research-skills installer
# Installs slash commands, checks dependencies, and verifies skill installation.
#
# Usage:
#   ./install.sh              # Full install (interactive)
#   ./install.sh --check      # Check dependencies only
#   ./install.sh --commands    # Install commands only

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILLS_DIR="$HOME/.claude/skills"
COMMANDS_DIR="$HOME/.claude/commands"

MODE="${1:-full}"

echo "=== claude-research-skills installer ==="
echo ""

# --- 1. Verify skills are installed ---
SKILLS_FOUND=0
SKILLS_MISSING=0
SKILL_LIST=(
    algorithm-design atomic-decomposition backward-traceability
    citation-management code-debugging data-analysis deep-research
    excalidraw-skill experiment-code experiment-design figure-generation
    idea-generation latex-formatting literature-review literature-search
    math-reasoning novelty-assessment paper-assembly paper-compilation
    paper-revision paper-to-code paper-writing-section rebuttal-writing
    related-work-writing research-planning self-review slide-generation
    survey-generation symbolic-equation table-generation
)

echo "[1/4] Checking skill installation..."
for skill in "${SKILL_LIST[@]}"; do
    if [ -f "$SKILLS_DIR/$skill/SKILL.md" ]; then
        SKILLS_FOUND=$((SKILLS_FOUND + 1))
    else
        SKILLS_MISSING=$((SKILLS_MISSING + 1))
        if [ "$SKILLS_MISSING" -le 5 ]; then
            echo "  [!] Missing: $skill"
        fi
    fi
done

if [ "$SKILLS_MISSING" -gt 5 ]; then
    echo "  [!] ... and $((SKILLS_MISSING - 5)) more missing"
fi

if [ "$SKILLS_MISSING" -gt 0 ]; then
    echo ""
    echo "  $SKILLS_FOUND/30 skills installed, $SKILLS_MISSING missing."
    echo "  Install with: npx skills add lingzhi227/claude-research-skills -g -a claude-code"
    echo ""
else
    echo "  [+] All 30 skills installed."
fi

if [ "$MODE" = "--check" ]; then
    echo ""
    echo "=== Dependency check only ==="
fi

# --- 2. Install slash commands ---
if [ "$MODE" != "--check" ]; then
    echo ""
    echo "[2/4] Installing slash commands..."
    mkdir -p "$COMMANDS_DIR"

    install_command() {
        local src="$1" name="$2"
        if [ ! -f "$SCRIPT_DIR/commands/$src" ]; then
            return
        fi
        if [ -f "$COMMANDS_DIR/$src" ]; then
            if ! diff -q "$SCRIPT_DIR/commands/$src" "$COMMANDS_DIR/$src" &>/dev/null; then
                echo "  [~] /$name updated."
                cp "$SCRIPT_DIR/commands/$src" "$COMMANDS_DIR/$src"
            else
                echo "  [=] /$name already up to date."
            fi
        else
            cp "$SCRIPT_DIR/commands/$src" "$COMMANDS_DIR/$src"
            echo "  [+] /$name installed."
        fi
    }

    install_command "research.md" "research"
else
    echo ""
    echo "[2/4] Skipping command installation (--check mode)."
fi

# --- 3. Check Python 3 ---
echo ""
echo "[3/4] Checking Python dependencies..."

if command -v python3 &>/dev/null; then
    PY_VERSION=$(python3 --version 2>&1)
    echo "  [+] $PY_VERSION"
else
    echo "  [!] Python 3 not found. Many skills require Python 3."
    echo "      Install via: brew install python3  (macOS) or apt install python3 (Linux)"
fi

# Check PyMuPDF (for self-review/parse_pdf_sections.py, deep-research/extract_pdf.py)
if python3 -c "import fitz" 2>/dev/null; then
    echo "  [+] PyMuPDF installed (PDF extraction available)"
else
    echo "  [-] PyMuPDF not installed (optional, for PDF parsing)"
    if [ "$MODE" = "full" ] || [ "$MODE" = "" ]; then
        read -rp "      Install PyMuPDF now? [y/N] " yn
        if [[ "${yn:-}" =~ ^[Yy]$ ]]; then
            python3 -m pip install PyMuPDF && echo "  [+] PyMuPDF installed." || echo "  [!] Install failed."
        fi
    else
        echo "      Install with: pip install PyMuPDF"
    fi
fi

# Check numpy + scipy (for data-analysis/stat_summary.py)
if python3 -c "import numpy; import scipy" 2>/dev/null; then
    echo "  [+] numpy + scipy installed (statistical analysis available)"
else
    echo "  [-] numpy/scipy not installed (optional, for statistical analysis)"
    if [ "$MODE" = "full" ] || [ "$MODE" = "" ]; then
        read -rp "      Install numpy + scipy now? [y/N] " yn
        if [[ "${yn:-}" =~ ^[Yy]$ ]]; then
            python3 -m pip install numpy scipy && echo "  [+] numpy + scipy installed." || echo "  [!] Install failed."
        fi
    else
        echo "      Install with: pip install numpy scipy"
    fi
fi

# --- 4. Verify scripts ---
echo ""
echo "[4/4] Verifying scripts..."
SCRIPTS_OK=0
SCRIPTS_FAIL=0
for script in "$SKILLS_DIR"/*/scripts/*.py; do
    [ -f "$script" ] || continue
    if python3 -c "import py_compile; py_compile.compile('$script', doraise=True)" 2>/dev/null; then
        SCRIPTS_OK=$((SCRIPTS_OK + 1))
    else
        SCRIPTS_FAIL=$((SCRIPTS_FAIL + 1))
        echo "  [!] Syntax error: $(basename "$(dirname "$(dirname "$script")")")/scripts/$(basename "$script")"
    fi
done
echo "  [+] $SCRIPTS_OK scripts OK"
if [ "$SCRIPTS_FAIL" -gt 0 ]; then
    echo "  [!] $SCRIPTS_FAIL scripts have syntax errors"
fi

# --- Done ---
echo ""
echo "=== Setup reminders ==="
echo ""
echo "1. Semantic Scholar API key (optional, recommended for literature search):"
echo "   Get one at: https://www.semanticscholar.org/product/api#api-key"
echo "   Save in ~/keys.md:  S2_API_Key: your-key-here"
echo ""
echo "2. Output directory for deep-research: ~/deep-research-output/"
echo ""
echo "=== Installation complete ==="
echo ""
echo "Skills available: 30 (run ./install.sh --check to verify)"
echo "Slash commands:   /research <topic>"
echo ""
echo "Start with:"
echo "  /research transformer architectures for long-context reasoning"
echo "  \"Write the Methods section of my paper\""
echo "  \"Generate a comparison table from results.json\""
echo "  \"Review my paper draft before submission\""
