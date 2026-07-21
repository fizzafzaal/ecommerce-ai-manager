#!/bin/bash
# One-time environment setup for the E-Commerce AI Manager project.
# Run this once from the project root: bash setup_env.sh

set -e

echo "Creating virtual environment (venv)..."
python -m venv venv

echo "Activating venv..."
source venv/Scripts/activate

echo "Upgrading pip..."
pip install --upgrade pip

echo "Installing dependencies from requirements.txt..."
pip install -r requirements.txt

echo ""
echo "Done. Activate the venv in future terminal sessions with:"
echo "  source venv/Scripts/activate"
echo ""
echo "Next: install Ollama from https://ollama.com and run 'ollama pull phi-2'"
