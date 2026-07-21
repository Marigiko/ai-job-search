#!/usr/bin/env bash
set -e

echo "=== Job Submission Automation Setup ==="
echo ""

# Install Node.js dependencies
echo "[1/3] Installing dependencies..."
npm install

# Install Playwright Chromium browser
echo "[2/3] Installing Playwright Chromium browser..."
npx playwright install chromium

# Create .env from example if not exists
if [ ! -f .env ]; then
    echo "[3/3] Creating .env from .env.example..."
    cp .env.example .env
    echo ""
    echo "  ⚠ IMPORTANT: Edit .env and fill in your portal credentials!"
    echo "  nano .env"
else
    echo "[3/3] .env already exists"
fi

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Next steps:"
echo "  1. Edit .env with your credentials"
echo "  2. Preview with: npm run submit:dry"
echo "  3. Submit with:   npm run submit"
echo ""
