#!/bin/bash

# Chroma MCP SSE Server
# Usage: ./chroma-mcp-sse.sh [port] [domain]
#
# This creates an SSE endpoint for the Chroma MCP server
# Default: http://localhost:3633/sse
# With domain: https://triepod.ai/chroma-mcp/sse

set -e

# Configuration
MCP_NAME="chroma-mcp"
DEFAULT_PORT=3633
PORT="${1:-$DEFAULT_PORT}"
DOMAIN="${2:-}"
LOG_DIR="$HOME/.${MCP_NAME}/logs"

# Create log directory
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/${MCP_NAME}-sse-$(date +%Y%m%d-%H%M%S).log"

# Function to handle cleanup on exit
cleanup() {
    echo "$(date): Cleaning up ${MCP_NAME} SSE proxy..." >> "$LOG_FILE"
    
    # Stop any running proxy processes on this port
    PROXY_PID=$(lsof -ti:${PORT} 2>/dev/null || true)
    if [ ! -z "$PROXY_PID" ]; then
        echo "$(date): Stopping proxy process $PROXY_PID on port $PORT" >> "$LOG_FILE"
        kill $PROXY_PID 2>/dev/null || true
        sleep 2
        kill -9 $PROXY_PID 2>/dev/null || true
    fi
    
    # Stop mcp-proxy processes for this MCP
    pkill -f "mcp-proxy.*${MCP_NAME}" 2>/dev/null || true
    
    echo "$(date): Cleanup complete" >> "$LOG_FILE"
}

# Set up signal handlers for graceful shutdown
trap cleanup EXIT SIGINT SIGTERM

# Check if port is already in use
if lsof -Pi :${PORT} -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "Error: Port ${PORT} is already in use"
    echo "Use: lsof -ti:${PORT} | xargs kill to stop existing process"
    exit 1
fi

# Determine the MCP command to use
# Use the wrapper script approach since it's proven to work
MCP_COMMAND="/home/bryan/run-chroma-mcp.sh"

# Check if wrapper script exists
if [ ! -f "$MCP_COMMAND" ]; then
    echo "Error: Chroma MCP wrapper script not found at $MCP_COMMAND"
    echo "Make sure /home/bryan/run-chroma-mcp.sh exists and is executable"
    exit 1
fi

# Display startup information
echo "Starting ${MCP_NAME} MCP-to-SSE proxy..." | tee -a "$LOG_FILE"
echo "Command: ${MCP_COMMAND}" | tee -a "$LOG_FILE"
echo "Port: ${PORT}" | tee -a "$LOG_FILE"

if [ -n "$DOMAIN" ]; then
    echo "Domain: ${DOMAIN}" | tee -a "$LOG_FILE"
    echo "SSE Endpoint: https://${DOMAIN}/sse" | tee -a "$LOG_FILE"
    echo "Stream Endpoint: https://${DOMAIN}/stream" | tee -a "$LOG_FILE"
else
    echo "SSE Endpoint: http://localhost:${PORT}/sse" | tee -a "$LOG_FILE"
    echo "Stream Endpoint: http://localhost:${PORT}/stream" | tee -a "$LOG_FILE"
fi

echo "Logs: $LOG_FILE" | tee -a "$LOG_FILE"
echo ""

# Set environment variables for the MCP command
export PYTHONUNBUFFERED=1
export TQDM_DISABLE=1
export CHROMA_CLIENT_TYPE=http
export CHROMA_HOST=chroma-chroma
export CHROMA_PORT=8000
export CHROMA_SSL=false
export ANONYMIZED_TELEMETRY=false
export CHROMA_TELEMETRY_DISABLED=true

# Start mcp-proxy with the wrapper script
echo "Starting SSE proxy..." | tee -a "$LOG_FILE"
exec mcp-proxy --port "$PORT" --debug "$MCP_COMMAND"