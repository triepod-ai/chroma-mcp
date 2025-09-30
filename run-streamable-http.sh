#!/bin/bash

# Chroma MCP Streamable HTTP Server Launcher
# Implements MCP-compliant streamable HTTP transport

set -e

# Configuration
DEFAULT_HOST="127.0.0.1"
DEFAULT_PORT="10550"
HOST="${1:-$DEFAULT_HOST}"
PORT="${2:-$DEFAULT_PORT}"

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$SCRIPT_DIR/logs"
mkdir -p "$LOG_DIR"

# Logging
LOG_FILE="$LOG_DIR/chroma-mcp-streamable-http-$(date +%Y%m%d-%H%M%S).log"

echo "===============================================" | tee -a "$LOG_FILE"
echo "Chroma MCP Streamable HTTP Server" | tee -a "$LOG_FILE"
echo "MCP Specification: 2025-03-26" | tee -a "$LOG_FILE"
echo "===============================================" | tee -a "$LOG_FILE"
echo "Host: $HOST" | tee -a "$LOG_FILE"
echo "Port: $PORT" | tee -a "$LOG_FILE"
echo "Log file: $LOG_FILE" | tee -a "$LOG_FILE"
echo "Health check: http://$HOST:$PORT/health" | tee -a "$LOG_FILE"
echo ""

# Function to handle cleanup on exit
cleanup() {
    echo "$(date): Shutting down Chroma MCP Streamable HTTP server..." | tee -a "$LOG_FILE"

    # Kill any processes using our port
    PROC_PID=$(lsof -ti:${PORT} 2>/dev/null || true)
    if [ ! -z "$PROC_PID" ]; then
        echo "$(date): Stopping process $PROC_PID on port $PORT" | tee -a "$LOG_FILE"
        kill $PROC_PID 2>/dev/null || true
        sleep 2
        kill -9 $PROC_PID 2>/dev/null || true
    fi

    echo "$(date): Cleanup complete" | tee -a "$LOG_FILE"
}

# Set up signal handlers for graceful shutdown
trap cleanup EXIT SIGINT SIGTERM

# Check if port is already in use
if lsof -Pi :${PORT} -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "Error: Port ${PORT} is already in use" | tee -a "$LOG_FILE"
    echo "Use: lsof -ti:${PORT} | xargs kill to stop existing process" | tee -a "$LOG_FILE"
    exit 1
fi

# Set environment variables for ChromaDB
export PYTHONUNBUFFERED=1
export TQDM_DISABLE=1
export CHROMA_CLIENT_TYPE=http
export CHROMA_HOST=chroma-chroma
export CHROMA_PORT=8000
export CHROMA_SSL=false
export ANONYMIZED_TELEMETRY=false
export CHROMA_TELEMETRY_DISABLED=true
export PYTHONPATH="$SCRIPT_DIR/src:$PYTHONPATH"

# Check if ChromaDB container is running
if ! docker ps --format "table {{.Names}}" | grep -q "chroma-chroma"; then
    echo "Warning: ChromaDB container 'chroma-chroma' not found" | tee -a "$LOG_FILE"
    echo "Starting ChromaDB container..." | tee -a "$LOG_FILE"

    cd "$SCRIPT_DIR"
    docker-compose up -d chroma

    # Wait for ChromaDB to be ready
    echo "Waiting for ChromaDB to be ready..." | tee -a "$LOG_FILE"
    sleep 5

    # Health check for ChromaDB
    for i in {1..30}; do
        if curl -s http://localhost:8001/api/v1/heartbeat > /dev/null 2>&1; then
            echo "ChromaDB is ready!" | tee -a "$LOG_FILE"
            break
        fi
        echo "Waiting for ChromaDB... ($i/30)" | tee -a "$LOG_FILE"
        sleep 2

        if [ $i -eq 30 ]; then
            echo "Error: ChromaDB failed to start within 60 seconds" | tee -a "$LOG_FILE"
            exit 1
        fi
    done
fi

# Start the streamable HTTP server
echo "$(date): Starting Chroma MCP Streamable HTTP server..." | tee -a "$LOG_FILE"

cd "$SCRIPT_DIR"

# Activate virtual environment
if [ -d ".venv" ]; then
    echo "$(date): Activating virtual environment..." | tee -a "$LOG_FILE"
    source .venv/bin/activate
else
    echo "$(date): Warning - no .venv directory found" | tee -a "$LOG_FILE"
fi

python3 -m src.chroma_mcp.streamable_http_server --host "$HOST" --port "$PORT" 2>&1 | tee -a "$LOG_FILE"