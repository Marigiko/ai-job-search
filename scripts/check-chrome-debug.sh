#!/bin/bash
# Verify Chrome remote debugging is reachable from WSL on port 9222.
# If Chrome is running on Windows with --remote-debugging-port=9222,
# this script confirms the MCP tools can connect to it.

echo "=== Checking Chrome remote debugging (port 9222) ==="

if ! command -v curl >/dev/null 2>&1; then
    echo "ERROR: curl not found"
    exit 1
fi

RESPONSE=$(curl -s --max-time 5 http://localhost:9222/json/version 2>&1)
if [ $? -ne 0 ]; then
    echo "FAIL: Cannot reach Chrome on port 9222."
    echo ""
    echo "To fix:"
    echo "  1. On Windows, run: scripts\\start-chrome-debug.bat"
    echo "  2. Log into LinkedIn and Upwork in the Chrome window that opens"
    echo "  3. Keep Chrome running, then retry this check"
    exit 1
fi

BROWSER=$(echo "$RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin).get('Browser','?'))" 2>/dev/null)
echo "OK: Chrome remote debugging reachable"
echo "  Browser: $BROWSER"
echo ""
echo "Next: log into linkedin.com and upwork.com in that Chrome window."
