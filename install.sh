#!/usr/bin/env bash
set -euo pipefail

# deep-research skill installer
# Installs the /research command and checks dependencies.
# The skill itself (SKILL.md + scripts) should be installed via:
#   npx skills add <user>/claude-skills

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMMANDS_DIR="$HOME/.claude/commands"

echo "=== deep-research skill installer ==="
echo ""

# --- 1. Install /research command ---
mkdir -p "$COMMANDS_DIR"
if [ -f "$COMMANDS_DIR/research.md" ]; then
    echo "[!] ~/.claude/commands/research.md already exists."
    read -rp "    Overwrite? [y/N] " overwrite
    if [[ "$overwrite" =~ ^[Yy]$ ]]; then
        cp "$SCRIPT_DIR/commands/research.md" "$COMMANDS_DIR/research.md"
        echo "[+] Installed /research command (overwritten)."
    else
        echo "[-] Skipped /research command."
    fi
else
    cp "$SCRIPT_DIR/commands/research.md" "$COMMANDS_DIR/research.md"
    echo "[+] Installed /research command to ~/.claude/commands/research.md"
fi

# --- 2. Check Python 3 ---
echo ""
if command -v python3 &>/dev/null; then
    PY_VERSION=$(python3 --version 2>&1)
    echo "[+] Python 3 found: $PY_VERSION"
else
    echo "[!] Python 3 not found. The deep-research scripts require Python 3."
    echo "    Install via: brew install python3  (macOS) or apt install python3 (Linux)"
fi

# --- 3. Check/install PyMuPDF (optional, for PDF extraction) ---
echo ""
if python3 -c "import fitz" 2>/dev/null; then
    echo "[+] PyMuPDF is installed (PDF extraction available)."
else
    echo "[?] PyMuPDF is not installed (optional, needed for extract_pdf.py)."
    read -rp "    Install PyMuPDF now? [y/N] " install_pymupdf
    if [[ "$install_pymupdf" =~ ^[Yy]$ ]]; then
        python3 -m pip install PyMuPDF
        echo "[+] PyMuPDF installed."
    else
        echo "[-] Skipped. Install later with: pip install PyMuPDF"
    fi
fi

# --- 4. Remind about configuration ---
echo ""
echo "=== Setup reminders ==="
echo ""
echo "1. Output directory (default: ~/deep-research-output/)"
echo "   Papers and reports will be saved here."
echo ""
echo "2. Semantic Scholar API key (optional but recommended)"
echo "   Get one at: https://www.semanticscholar.org/product/api#api-key"
echo "   Save it in ~/keys.md with a line: S2_API_Key: <your-key>"
echo ""
echo "3. paper_finder tool (optional)"
echo "   For searching conference paper databases."
echo "   See SKILL.md for setup instructions."
echo ""
echo "=== Installation complete ==="
echo "Use /research <topic> in Claude Code to start a literature review."
