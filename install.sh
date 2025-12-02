#!/bin/bash

# WordLift Gemini CLI Extension - Installation Script
# This script sets up the Python virtual environment and dependencies

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🚀 Installing WordLift Gemini CLI Extension..."

# Check Python version
PYTHON_CMD=""
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

    if [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -ge 10 ]; then
        PYTHON_CMD="python3"
    fi
fi

if [ -z "$PYTHON_CMD" ]; then
    echo "❌ Error: Python 3.10 or higher is required"
    echo "Please install Python 3.10+ and try again"
    exit 1
fi

echo "✓ Found Python $PYTHON_VERSION"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    $PYTHON_CMD -m venv venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi

# Activate virtual environment and install dependencies
echo "📥 Installing dependencies..."
source venv/bin/activate
pip install --upgrade pip > /dev/null 2>&1
pip install -r requirements.txt

echo "✓ Dependencies installed"

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo ""
    echo "⚠️  Configuration Required"
    echo "You need to create a .env file with your WordLift credentials:"
    echo ""
    echo "  WORDLIFT_API_KEY=your_api_key_here"
    echo "  WORDLIFT_BASE_URI=https://data.wordlift.io/your_dataset_id"
    echo "  WORDLIFT_API_ENDPOINT=https://api.wordlift.io"
    echo ""
    echo "Create this file before using the extension."
else
    echo "✓ Configuration file (.env) found"
fi

echo ""
echo "✅ Installation complete!"
echo ""
echo "Next steps:"
echo "  1. Configure your .env file (if not already done)"
echo "  2. The extension is ready to use with Gemini CLI"
