#!/bin/bash
# Quick launcher for compact Thai ID Card Reader interface

echo "🪪 Starting Thai ID Card Reader - Compact Interface"
echo ""

# Check if we're in the right directory
if [ ! -f "app_compact.py" ]; then
    echo "Error: Must run from debug/ directory"
    exit 1
fi

# Launch streamlit
STREAMLIT_EMAIL="" uv run streamlit run app_compact.py --server.headless=true

echo ""
echo "Interface stopped"
