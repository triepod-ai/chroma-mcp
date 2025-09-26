#!/bin/bash

# Chroma MCP + Sequential Thinking Management Menu
# Enhanced by Triepod.ai

set -e

# Colors for better UX
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
DEFAULT_PORT=3633
DEFAULT_DOMAIN="bot.triepod.ai"
WRAPPER_SCRIPT="/home/bryan/run-chroma-mcp.sh"

# Helper functions
print_header() {
    clear
    echo -e "${PURPLE}╔══════════════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${PURPLE}║                    Chroma MCP + Sequential Thinking                          ║${NC}"
    echo -e "${PURPLE}║                           Enhanced by Triepod.ai                             ║${NC}"
    echo -e "${PURPLE}╚══════════════════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

check_status() {
    echo -e "${CYAN}📊 Current Status${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    # Check if port is in use
    if netstat -tuln 2>/dev/null | grep -q ":$DEFAULT_PORT "; then
        echo -e "🟢 SSE Server: ${GREEN}Running on port $DEFAULT_PORT${NC}"
        local pid=$(lsof -ti:$DEFAULT_PORT 2>/dev/null || echo "")
        if [ -n "$pid" ]; then
            echo -e "   PID: $pid"
        fi
    else
        echo -e "🔴 SSE Server: ${RED}Not running${NC}"
    fi
    
    # Check wrapper script
    if [ -f "$WRAPPER_SCRIPT" ]; then
        echo -e "✅ Wrapper Script: ${GREEN}Found${NC} ($WRAPPER_SCRIPT)"
    else
        echo -e "❌ Wrapper Script: ${RED}Missing${NC} ($WRAPPER_SCRIPT)"
    fi
    
    # Check Docker
    if command -v docker &> /dev/null; then
        echo -e "🐳 Docker: ${GREEN}Available${NC}"
        local running_containers=$(docker ps --format "table {{.Names}}\t{{.Status}}" | grep -E "(chroma|mcp)" | wc -l)
        echo -e "   MCP Containers: $running_containers running"
    else
        echo -e "🐳 Docker: ${YELLOW}Not available${NC}"
    fi
    
    # Check endpoints
    echo ""
    echo -e "${CYAN}🌐 Endpoints${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo -e "   SSE:    http://localhost:$DEFAULT_PORT/sse"
    echo -e "   Stream: http://localhost:$DEFAULT_PORT/stream"
    echo -e "   Health: http://localhost:$DEFAULT_PORT/health"
    echo -e "   Public: https://$DEFAULT_DOMAIN/sse"
    echo ""
}

start_sse_server() {
    echo -e "${GREEN}🚀 Starting SSE Server${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    # Check if already running
    if netstat -tuln 2>/dev/null | grep -q ":$DEFAULT_PORT "; then
        echo -e "${YELLOW}⚠️  Server already running on port $DEFAULT_PORT${NC}"
        echo ""
        read -p "Press Enter to continue..."
        return
    fi
    
    echo "Starting SSE server on port $DEFAULT_PORT..."
    echo ""
    
    # Start in background with output to log file
    local log_file="/tmp/chroma-mcp-sse.log"
    echo "Logging to: $log_file"
    echo ""
    
    # Start the server
    nohup ./start-sse-host.sh "$DEFAULT_DOMAIN" "$DEFAULT_PORT" > "$log_file" 2>&1 &
    local pid=$!
    
    echo "Started with PID: $pid"
    echo ""
    
    # Wait a moment and check if it's running
    sleep 2
    if kill -0 "$pid" 2>/dev/null; then
        echo -e "${GREEN}✅ SSE Server started successfully${NC}"
        echo "View logs: tail -f $log_file"
    else
        echo -e "${RED}❌ Failed to start SSE server${NC}"
        echo "Check logs: cat $log_file"
    fi
    
    echo ""
    read -p "Press Enter to continue..."
}

stop_sse_server() {
    echo -e "${RED}🛑 Stopping SSE Server${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    local pids=$(lsof -ti:$DEFAULT_PORT 2>/dev/null || echo "")
    
    if [ -z "$pids" ]; then
        echo -e "${YELLOW}⚠️  No processes found on port $DEFAULT_PORT${NC}"
    else
        echo "Stopping processes on port $DEFAULT_PORT..."
        echo "PIDs: $pids"
        echo ""
        
        # Kill the processes
        echo "$pids" | xargs kill -TERM 2>/dev/null || true
        
        # Wait a moment
        sleep 2
        
        # Force kill if still running
        local remaining_pids=$(lsof -ti:$DEFAULT_PORT 2>/dev/null || echo "")
        if [ -n "$remaining_pids" ]; then
            echo "Force killing remaining processes..."
            echo "$remaining_pids" | xargs kill -KILL 2>/dev/null || true
        fi
        
        echo -e "${GREEN}✅ SSE Server stopped${NC}"
    fi
    
    echo ""
    read -p "Press Enter to continue..."
}

test_sse_connection() {
    echo -e "${BLUE}🧪 Testing SSE Connection${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    # Test health endpoint
    echo "Testing health endpoint..."
    if curl -s -f "http://localhost:$DEFAULT_PORT/health" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Health endpoint responding${NC}"
    else
        echo -e "${RED}❌ Health endpoint not responding${NC}"
        echo ""
        read -p "Press Enter to continue..."
        return
    fi
    
    # Test with JavaScript client if available
    if [ -f "test-sse.js" ]; then
        echo ""
        echo "Running JavaScript SSE test..."
        echo "Press Ctrl+C to stop the test"
        echo ""
        sleep 2
        node test-sse.js || true
    else
        echo ""
        echo "Manual test - try this in another terminal:"
        echo "curl -N http://localhost:$DEFAULT_PORT/sse"
    fi
    
    echo ""
    read -p "Press Enter to continue..."
}

view_logs() {
    echo -e "${CYAN}📋 Viewing Logs${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    local log_file="/tmp/chroma-mcp-sse.log"
    
    if [ -f "$log_file" ]; then
        echo "Showing last 50 lines of $log_file"
        echo "Press 'q' to quit, 'f' to follow new lines"
        echo ""
        sleep 2
        tail -n 50 "$log_file"
        echo ""
        echo "To follow live logs, run: tail -f $log_file"
    else
        echo -e "${YELLOW}⚠️  Log file not found: $log_file${NC}"
    fi
    
    echo ""
    read -p "Press Enter to continue..."
}

docker_management() {
    echo -e "${BLUE}🐳 Docker Management${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}❌ Docker not available${NC}"
        echo ""
        read -p "Press Enter to continue..."
        return
    fi
    
    echo "Available Docker commands:"
    echo ""
    echo "1. Start Docker SSE (docker-compose.sse.yaml)"
    echo "2. Stop Docker SSE"
    echo "3. View Docker logs"
    echo "4. Rebuild containers"
    echo "5. Back to main menu"
    echo ""
    
    read -p "Choose option (1-5): " docker_choice
    
    case $docker_choice in
        1)
            echo "Starting Docker SSE..."
            docker-compose -f docker-compose.sse.yaml up -d
            ;;
        2)
            echo "Stopping Docker SSE..."
            docker-compose -f docker-compose.sse.yaml down
            ;;
        3)
            echo "Docker logs..."
            docker-compose -f docker-compose.sse.yaml logs -f --tail=50
            ;;
        4)
            echo "Rebuilding containers..."
            docker-compose -f docker-compose.sse.yaml down
            docker-compose -f docker-compose.sse.yaml build --no-cache
            docker-compose -f docker-compose.sse.yaml up -d
            ;;
        5)
            return
            ;;
        *)
            echo "Invalid option"
            ;;
    esac
    
    echo ""
    read -p "Press Enter to continue..."
}

show_documentation() {
    echo -e "${CYAN}📚 Documentation${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo -e "${YELLOW}🔧 Claude Code Configuration${NC}"
    echo "Add this to your Claude Desktop config to use the SSE server:"
    echo ""
    echo '{
  "mcpServers": {
    "chroma-sse": {
      "command": "curl",
      "args": ["-N", "http://localhost:'$DEFAULT_PORT'/sse"],
      "env": {}
    }
  }
}'
    echo ""
    echo -e "${YELLOW}🌐 Endpoints${NC}"
    echo "  SSE Stream: http://localhost:$DEFAULT_PORT/sse"
    echo "  WebSocket:  http://localhost:$DEFAULT_PORT/stream"
    echo "  Health:     http://localhost:$DEFAULT_PORT/health"
    echo ""
    echo -e "${YELLOW}🧪 Testing Commands${NC}"
    echo "  curl -N http://localhost:$DEFAULT_PORT/sse"
    echo "  node test-sse.js"
    echo ""
    echo -e "${YELLOW}📋 Log Files${NC}"
    echo "  SSE Server: /tmp/chroma-mcp-sse.log"
    echo "  MCP Server: /tmp/chroma-mcp.log"
    echo ""
    echo -e "${YELLOW}🔧 Sequential Thinking Tools${NC}"
    echo "  chroma_sequential_thinking - Store structured thought chains"
    echo "  chroma_get_similar_sessions - Find similar thinking sessions"
    echo "  chroma_get_thought_history - Retrieve complete thought history"
    echo "  chroma_get_thought_branches - Get thought branches"
    echo "  chroma_continue_thought_chain - Continue reasoning chains"
    echo ""
    read -p "Press Enter to continue..."
}

# Main menu
main_menu() {
    while true; do
        print_header
        check_status
        
        echo -e "${CYAN}🎯 Main Menu${NC}"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo ""
        echo "1. 🚀 Start SSE Server"
        echo "2. 🛑 Stop SSE Server"
        echo "3. 🧪 Test SSE Connection"
        echo "4. 📋 View Logs"
        echo "5. 🐳 Docker Management"
        echo "6. 📚 Documentation"
        echo "7. 🔄 Refresh Status"
        echo "8. ❌ Exit"
        echo ""
        
        read -p "Choose option (1-8): " choice
        
        case $choice in
            1) start_sse_server ;;
            2) stop_sse_server ;;
            3) test_sse_connection ;;
            4) view_logs ;;
            5) docker_management ;;
            6) show_documentation ;;
            7) continue ;;
            8) 
                echo ""
                echo -e "${GREEN}👋 Goodbye!${NC}"
                exit 0
                ;;
            *)
                echo ""
                echo -e "${RED}❌ Invalid option. Please choose 1-8.${NC}"
                echo ""
                read -p "Press Enter to continue..."
                ;;
        esac
    done
}

# Run the menu
main_menu