#!/bin/bash
# Quick launcher for Thai ID Card Reader interface

echo "🪪 Starting Thai ID Card Reader Interface"
echo ""

# Check if we're in the right directory
if [ ! -f "app.py" ]; then
    echo "Error: Must run from debug/ directory"
    exit 1
fi

# Launch streamlit
STREAMLIT_EMAIL="" uv run streamlit run app.py --server.headless=true

echo ""
echo "Interface stopped"
