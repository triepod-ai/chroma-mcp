# Chroma MCP Streamable HTTP Server

## Overview

This is a **clean, MCP-compliant Streamable HTTP server** that replaces the bloated proxy implementation. It follows the [Model Context Protocol Streamable HTTP specification (2025-03-26)](https://modelcontextprotocol.io/specification/2025-03-26/basic/transports).

## Key Improvements

✅ **MCP Compliant**: Follows official MCP Streamable HTTP transport specification
✅ **Single Endpoint**: Both POST (client→server) and GET (server→client SSE) on same endpoint
✅ **No Dependencies**: Eliminates the need for `mcp-proxy` wrapper
✅ **Lightweight**: Clean FastAPI implementation without bloated containers
✅ **Session Management**: Proper session handling with `Mcp-Session-Id` headers
✅ **Security**: Origin validation and CORS protection

## Quick Start

### 1. Basic Usage

```bash
# Start the server (binds to localhost:3000 by default)
./run-streamable-http.sh

# Or specify custom host/port
./run-streamable-http.sh 127.0.0.1 3001
```

### 2. Using Python Module Directly

```bash
# Activate virtual environment first
source .venv/bin/activate

# Start server programmatically
python3 -c "from src.chroma_mcp.streamable_http_server import run_server; run_server('127.0.0.1', 3000)"
```

### 3. Health Check

```bash
curl http://localhost:3000/health
```

Expected response:
```json
{
  "status": "healthy",
  "collections_count": 0,
  "sessions_count": 0,
  "server_info": {
    "name": "chroma-mcp",
    "version": "0.3.0",
    "protocolVersion": "2025-03-26"
  }
}
```

## MCP Client Integration

### Initialize Connection

```bash
curl -X POST http://localhost:3000/ \
  -H "Content-Type: application/json" \
  -H "Mcp-Session-Id: $(uuidgen)" \
  -d '{
    "jsonrpc": "2.0",
    "method": "initialize",
    "params": {
      "protocolVersion": "2025-03-26",
      "capabilities": {},
      "clientInfo": {"name": "my-client", "version": "1.0.0"}
    },
    "id": 1
  }'
```

### List Available Tools

```bash
curl -X POST http://localhost:3000/ \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/list",
    "id": 2
  }'
```

### Call a Tool

```bash
curl -X POST http://localhost:3000/ \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "chroma_list_collections",
      "arguments": {}
    },
    "id": 3
  }'
```

### Server-to-Client Events (SSE)

```bash
# Listen for server events
curl -N http://localhost:3000/ \
  -H "Accept: text/event-stream" \
  -H "Mcp-Session-Id: your-session-id"
```

## Architecture

### File Structure

```
src/chroma_mcp/
├── streamable_http_server.py    # Main MCP server implementation
├── server.py                    # Existing Chroma tool functions
└── __init__.py                  # Module initialization

run-streamable-http.sh           # Launcher script
```

### Technical Details

- **Framework**: FastAPI with uvicorn
- **Transport**: MCP Streamable HTTP (spec 2025-03-26)
- **Port**: 3000 (default), configurable
- **Binding**: 127.0.0.1 (localhost only for security)
- **Session Management**: UUID-based sessions with optional `Mcp-Session-Id` header
- **CORS**: Enabled for development, configurable for production

### Available Tools

All existing Chroma MCP tools are available:

- `chroma_list_collections`
- `chroma_create_collection`
- `chroma_peek_collection`
- `chroma_get_collection_info`
- `chroma_get_collection_count`
- `chroma_modify_collection`
- `chroma_delete_collection`
- `chroma_add_documents`
- `chroma_query_documents`
- `chroma_get_documents`
- `chroma_update_documents`
- `chroma_delete_documents`
- `chroma_sequential_thinking`
- `chroma_get_similar_sessions`
- `chroma_get_thought_history`
- `chroma_get_thought_branches`
- `chroma_continue_thought_chain`

## Differences from Old Implementation

| Aspect | Old (Bloated) | New (Streamable HTTP) |
|--------|---------------|----------------------|
| **Compliance** | Non-standard JSON-RPC over HTTP | Official MCP Streamable HTTP |
| **Dependencies** | Requires `mcp-proxy` wrapper | Native FastAPI implementation |
| **Endpoints** | Multiple endpoints | Single endpoint (POST + GET) |
| **Sessions** | No session management | Proper session handling |
| **Security** | Basic CORS | Origin validation + CORS |
| **Deployment** | Complex Docker setup | Simple script launcher |
| **Debugging** | Hard to troubleshoot | Clear logs and health checks |

## Configuration

### Environment Variables

The launcher script automatically sets:

```bash
export CHROMA_CLIENT_TYPE=http
export CHROMA_HOST=chroma-chroma
export CHROMA_PORT=8000
export CHROMA_SSL=false
export ANONYMIZED_TELEMETRY=false
export CHROMA_TELEMETRY_DISABLED=true
export PYTHONPATH="$PWD/src:$PYTHONPATH"
```

### Security Settings

For production deployment, consider:

- Restrict `allow_origins` in CORS middleware
- Use HTTPS with proper certificates
- Implement authentication/authorization
- Bind to specific interfaces instead of `0.0.0.0`

## Troubleshooting

### Server Won't Start

1. **Check virtual environment**:
   ```bash
   source .venv/bin/activate
   python3 -c "import chromadb; print('ChromaDB available')"
   ```

2. **Check ChromaDB container**:
   ```bash
   docker-compose ps
   curl http://localhost:8001/api/v2/heartbeat
   ```

3. **Check port availability**:
   ```bash
   lsof -i :3000
   ```

### Connection Issues

1. **CORS errors**: Check `Origin` header in requests
2. **SSL errors**: Ensure using HTTP (not HTTPS) for local testing
3. **Timeout errors**: Verify ChromaDB container is healthy

### Logs

- Server logs: `logs/chroma-mcp-streamable-http-YYYYMMDD-HHMMSS.log`
- Health check: `curl http://localhost:3000/health`

## Testing

Use the provided test files:

```bash
# Test minimal server functionality
source .venv/bin/activate
python3 test_streamable_http.py

# Test with real Chroma integration
./run-streamable-http.sh 127.0.0.1 3001
```

## Production Deployment

For production use, consider:

1. **Reverse Proxy**: Use nginx/Apache for SSL termination
2. **Process Management**: Use systemd, supervisor, or Docker
3. **Monitoring**: Add metrics and health checks
4. **Security**: Implement proper authentication

Example nginx config:
```nginx
location /mcp/ {
    proxy_pass http://localhost:3000/;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Host $host;
    proxy_cache_bypass $http_upgrade;
}
```

This streamable HTTP implementation provides a clean, standards-compliant way to access your Chroma MCP server over HTTP without the complexity of the previous proxy-based approach.