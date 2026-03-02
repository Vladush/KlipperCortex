#!/bin/bash
set -e

echo "==================================================="
echo "   KlipperCortex: Automated Installer"
echo "==================================================="

# 1. Check for Python 3
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed."
    exit 1
fi

# 2. Setup Virtual Environment (Recommended)
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

echo "Activating virtual environment..."
source .venv/bin/activate

# 3. Install Dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# 4. Model Setup
echo ""
echo "---------------------------------------------------"
echo "Model Setup"
echo "---------------------------------------------------"
if [ ! -f "models/spaghetti_v2.vmfb" ] && [ ! -f "models/spaghetti_v2.tflite" ]; then
    echo "Model files not found."
    read -p "Do you want to run the model download script? (y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        python3 scripts/download_models.py
    else
        echo "Skipping model download. You will need to provide a model manually."
    fi
else
    echo "Model files detected."
fi

# 5. Configuration
echo ""
echo "---------------------------------------------------"
echo "Configuration"
echo "---------------------------------------------------"
if [ ! -f "mcp_config.json" ]; then
    echo "Creating mcp_config.json from example..."
    cp mcp_config.example.json mcp_config.json
    echo "Created mcp_config.json. Please edit it with your specific settings."
fi

if [ ! -f "connections.json" ]; then
    if [ -f "connections.json.example" ]; then
        echo "Creating connections.json from example..."
        cp connections.json.example connections.json
        echo "Created connections.json. Please edit it with your printer details."
    fi
fi

echo ""
echo "==================================================="
echo "   Installation Complete!"
echo "==================================================="
echo "To start the detector:"
echo "  source .venv/bin/activate"
echo "  python3 src/inference_loop.py"
echo ""
