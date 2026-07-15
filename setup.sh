#!/usr/bin/env bash
# One-command setup for the AI Job Search framework.
# Usage: bash setup.sh
set -e

echo "=== AI Job Search — Setup ==="

# --- Python dependencies ---
echo "[1/4] Installing Python dependencies..."
pip install -r requirements.txt

# --- Bun / Node dependencies (for portal CLI tools) ---
echo "[2/4] Installing Bun dependencies..."
if ! command -v bun &>/dev/null; then
    echo "Bun not found. Installing..."
    curl -fsSL https://bun.sh/install | bash
    export PATH="$HOME/.local/bin:$HOME/.bun/bin:$PATH"
fi
for tool in $(ls -d .agents/skills/*/cli 2>/dev/null); do
    echo "  → Installing $tool"
    (cd "$tool" && bun install)
done

# --- Playwright browsers ---
echo "[3/4] Installing Playwright browsers..."
npx playwright install chromium

# --- Tesseract OCR (system-level) ---
echo "[4/4] Checking Tesseract OCR..."
if ! command -v tesseract &>/dev/null; then
    echo "  ⚠ Tesseract not found. Install via:"
    echo "    Ubuntu/Debian: sudo apt install tesseract-ocr"
    echo "    macOS:         brew install tesseract"
    echo "    Windows:       choco install tesseract"
fi

echo ""
echo "=== Setup complete! ==="
echo "Next steps:"
echo "  1. Copy .env.example to .env and fill in your Gmail App Password"
echo "  2. Run /setup inside your AI assistant to configure your profile"
