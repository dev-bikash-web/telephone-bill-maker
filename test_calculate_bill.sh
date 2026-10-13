#!/bin/bash
# Telephone Bill Diagnostic & Calculation Tool Runner Script

set -e

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "=============================================="
    echo "Creating virtual environment (.venv)..."
    echo "=============================================="
    python3 -m venv .venv
    
    echo "Upgrading pip..."
    .venv/bin/pip install --upgrade pip
    
    echo "Installing required dependencies (pypdf, reportlab)..."
    .venv/bin/pip install pypdf reportlab
    echo "Dependencies installed successfully!"
fi

# Check for poppler pdftotext availability
if ! command -v pdftotext &> /dev/null; then
    echo "[WARNING] 'pdftotext' was not found on PATH."
    echo "If uncached PDF parsing fails, install poppler-utils:"
    echo "  sudo apt install poppler-utils"
    echo ""
fi

# Run the python parser script directly forwarding any CLI arguments
exec .venv/bin/python test_parser.py "$@"
