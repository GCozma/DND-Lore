#!/bin/bash

# Navigate to the script's directory
cd "$(dirname "$0")"

echo "=========================================="
echo "   Warhammer 40k Lore Oracle Startup      "
echo "=========================================="

# 1. Check if Ollama service is running
echo "Checking Ollama background service..."
if ! curl -s http://127.0.0.1:11434/api/tags > /dev/null; then
    echo "Ollama is not running. Attempting to start service..."
    sudo systemctl start ollama
    sleep 3
    if ! curl -s http://127.0.0.1:11434/api/tags > /dev/null; then
        echo "❌ Error: Could not connect to Ollama. Please run 'ollama serve' in another terminal."
        exit 1
    fi
fi
echo "✓ Ollama service is active."

# 2. Check if llama3.1 is installed
echo "Checking llama3.1 model availability..."
if ! curl -s http://127.0.0.1:11434/api/tags | grep -q "llama3.1"; then
    echo "llama3.1 model not found. Downloading now (this may take a few minutes)..."
    ollama pull llama3.1
else
    echo "✓ llama3.1 model is ready."
fi

# 3. Start Streamlit Server
echo "Launching Streamlit interface..."
uv run streamlit run app.py