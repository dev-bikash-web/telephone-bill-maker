#!/bin/bash
# C-DOT Telephone Bill Printer Tool Runner Script

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
fi

# Ensure required printer packages (pypdf, selenium) are installed in the venv
echo "Checking dependencies..."
.venv/bin/pip install -q pypdf selenium

# Ensure print_config.cfg exists
if [ ! -f "print_config.cfg" ]; then
    echo "Warning: 'print_config.cfg' not found."
    if [ -f "print_config.cfg.template" ]; then
        echo "Creating 'print_config.cfg' from template..."
        cp print_config.cfg.template print_config.cfg
        echo "Please configure your credentials in 'print_config.cfg' and run the tool again."
        exit 1
    else
        echo "Error: Template 'print_config.cfg.template' not found in workspace."
        exit 1
    fi
fi

# Run the python script forwarding any CLI arguments
exec .venv/bin/python print_bills.py "$@"
