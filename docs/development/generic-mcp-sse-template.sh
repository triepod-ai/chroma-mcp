#!/bin/bash

# Generic MCP-to-SSE Proxy Template
# Usage: ./generic-mcp-sse-template.sh <mcp_name> <command> [port] [env_vars...]
#
# Examples:
# ./generic-mcp-sse-template.sh vercel-mcp "docker run -i --rm -e VERCEL_API_TOKEN=xyz vercel-mcp" 3399
# ./generic-mcp-sse-template.sh supabase-mcp "node /path/to/mcp/index.js" 3400
# ./generic-mcp-sse-template.sh chroma-mcp "python -m chroma_mcp" 3401

set -e

# Check arguments
if [ $# -lt 2 ]; then
    echo "Usage: $0 <mcp_name> <command> [port] [env_vars...]"
    echo ""
    echo "Examples:"
    echo "  $0 vercel-mcp 'docker run -i --rm -e VERCEL_API_TOKEN=xyz vercel-mcp' 3399"
    echo "  $0 supabase-mcp 'node /path/to/mcp/index.js' 3400" 
    echo "  $0 chroma-mcp 'python -m chroma_mcp' 3401"
    exit 1
fi

# Configuration
MCP_NAME="$1"
MCP_COMMAND="$2"
DEFAULT_PORT=8080
PORT="${3:-$DEFAULT_PORT}"
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

echo "Starting ${MCP_NAME} MCP-to-SSE proxy..." | tee -a "$LOG_FILE"
echo "Command: ${MCP_COMMAND}" | tee -a "$LOG_FILE"
echo "Port: ${PORT}" | tee -a "$LOG_FILE"
echo "SSE Endpoint: http://localhost:${PORT}/sse" | tee -a "$LOG_FILE"
echo "Stream Endpoint: http://localhost:${PORT}/stream" | tee -a "$LOG_FILE"
echo "Logs: $LOG_FILE" | tee -a "$LOG_FILE"
echo ""

# Start mcp-proxy 
echo "Starting proxy..." | tee -a "$LOG_FILE"
exec mcp-proxy --port "$PORT" $MCP_COMMAND