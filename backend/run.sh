#!/bin/bash

# Quick start script for FIEK Chatbot

echo "FIEK AI Chatbot - Quick Start"
echo "=============================="
echo ""

# Check if data exists
if [ ! -f "knowledge_base/collected_data.json" ]; then
    echo "Knowledge base not found. Running setup..."
    python setup.py
    echo ""
fi

echo "Starting Flask server..."
echo "Server will be available at http://localhost:5001"
echo "Open frontend/index.html in your browser"
echo ""
python app.py

