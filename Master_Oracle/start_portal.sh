#!/bin/bash
#Input here your own gemini api key
#export GEMINI_API_KEY=" "

# Navigate to the script's directory
cd "$(dirname "$0")"

echo "=========================================="
echo "    Master Oracle Portal Startup          "
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

# 3. Check and start Cloudflare Tunnel (geotools.me)
echo "Checking Cloudflare Tunnel status..."
if ! pgrep -x "cloudflared" > /dev/null; then
    echo "Cloudflare Tunnel is not active. Starting tunnel in background..."
    if command -v cloudflared &> /dev/null; then
        nohup cloudflared tunnel run > cloudflare_tunnel.log 2>&1 &
        sleep 2
        if pgrep -x "cloudflared" > /dev/null; then
            echo "✓ Cloudflare Tunnel successfully launched."
        else
            echo "⚠️ Warning: Failed to start cloudflared tunnel. Check 'cloudflare_tunnel.log'."
        fi
    else
        echo "⚠️ Warning: 'cloudflared' command not found. Cannot start tunnel."
    fi
else
    echo "✓ Cloudflare Tunnel is already running."
fi

# 4. Clean up any process occupying port 8501
if lsof -t -i:8501 > /dev/null 2>&1; then
    echo "Port 8501 is occupied. Cleaning up old server instance..."
    kill -9 $(lsof -t -i:8501)
    sleep 1
fi

# 5. Start Master Streamlit Server
echo "Launching Master Oracle Portal..."
/home/george/PycharmProjects/Warhammer_oracle/.venv/bin/streamlit run homepage.py --server.port 8501