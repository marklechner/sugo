#!/bin/bash
# Súgó Transcriber — Double-click to launch
# This script installs dependencies on first run and starts the transcription server.

set -e

# Navigate to the script's directory (where the project lives)
cd "$(dirname "$0")"

echo ""
echo "  🐱 Súgó Transcriber"
echo "  ===================="
echo ""

# Check for uv, install if missing
if ! command -v uv &> /dev/null; then
    echo "  Installing uv (Python package manager)..."
    echo "  This is a one-time setup step."
    echo ""
    curl -LsSf https://astral.sh/uv/install.sh | sh
    # Source the updated PATH
    export PATH="$HOME/.local/bin:$PATH"
    echo ""
    echo "  uv installed successfully."
    echo ""
fi

echo "  Starting Súgó..."
echo "  (On first run, the AI model will download — this may take a few minutes)"
echo ""

# Run the app via uv (auto-creates venv and installs deps on first run)
uv run python -m transcriber.app
