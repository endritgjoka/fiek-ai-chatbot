#!/bin/bash
# Setup script for FIEK AI Chatbot
# This script creates a virtual environment and installs all dependencies

set -e  # Exit on error

echo "=========================================="
echo "FIEK AI Chatbot - Environment Setup"
echo "=========================================="
echo ""

# Check Python version
echo "Checking Python version..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "✅ Found Python $PYTHON_VERSION"

# Create virtual environment
echo ""
echo "Creating virtual environment..."
if [ -d "venv" ]; then
    echo "⚠️  Virtual environment already exists. Removing old one..."
    rm -rf venv
fi

python3 -m venv venv
echo "✅ Virtual environment created"

# Activate virtual environment
echo ""
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo ""
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo ""
echo "Installing Python dependencies..."
echo "This may take several minutes..."
pip install -r requirements.txt

# Check for .env file
echo ""
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found. Creating from .env.example..."
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "✅ Created .env file. Please edit it and add your OPENAI_API_KEY"
    else
        echo "⚠️  .env.example not found. Please create .env file manually with OPENAI_API_KEY"
    fi
else
    echo "✅ .env file already exists"
fi

echo ""
echo "=========================================="
echo "Setup completed successfully!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Edit backend/.env and add your OPENAI_API_KEY"
echo "2. (Optional) Install Tesseract OCR for scanned PDF support:"
echo "   - macOS: brew install tesseract"
echo "   - Ubuntu/Debian: sudo apt-get install tesseract-ocr"
echo "   - Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki"
echo "3. Run data ingestion: python models/ingest.py"
echo "4. Start the app:"
echo "   - Flask: python app.py"
echo "   - Streamlit: streamlit run appV2.py"
echo ""
echo "To activate the virtual environment in the future, run:"
echo "  source venv/bin/activate"
echo ""

