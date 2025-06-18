#!/bin/bash

# Simple SSE Server on Host (not containerized)
# This uses your existing wrapper script and runs mcp-proxy directly on the host

set -e

DOMAIN="${1:-bot.triepod.ai}"
PORT="${2:-3633}"

echo "🚀 Starting Chroma MCP SSE Server (Host Mode)"
echo "============================================="
echo "Domain: $DOMAIN"
echo "Port: $PORT"
echo "Wrapper: /home/bryan/run-chroma-mcp.sh"
echo ""

# Check if wrapper script exists
if [ ! -f "/home/bryan/run-chroma-mcp.sh" ]; then
    echo "❌ Wrapper script not found: /home/bryan/run-chroma-mcp.sh"
    exit 1
fi

# Check if port is available
if netstat -tuln | grep -q ":$PORT "; then
    echo "❌ Port $PORT is already in use"
    echo "Run: sudo lsof -ti:$PORT | xargs kill to stop existing process"
    exit 1
fi

# Start mcp-proxy with the wrapper script
echo "🎯 Starting SSE proxy..."
echo "📍 Endpoints:"
echo "  SSE:    http://localhost:$PORT/sse"
echo "  Stream: http://localhost:$PORT/stream"
echo "  Health: http://localhost:$PORT/health"
echo ""

if [ -n "$DOMAIN" ] && [ "$DOMAIN" != "localhost" ]; then
    echo "🌐 Public endpoints (after DNS setup):"
    echo "  SSE:    https://$DOMAIN/sse"
    echo "  Stream: https://$DOMAIN/stream"
    echo "  Health: https://$DOMAIN/health"
    echo ""
fi

# Run mcp-proxy with your working wrapper script
exec mcp-proxy --port "$PORT" --debug /home/bryan/run-chroma-mcp.sh