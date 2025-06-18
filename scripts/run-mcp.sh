#!/bin/bash

# Chroma MCP Docker Wrapper Script
# Usage: ./run-mcp.sh [additional arguments]

docker exec -i chroma-mcp chroma-mcp --client-type http --host 10.0.0.225 --port 8001 "$@"