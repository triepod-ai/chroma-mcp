# Chroma MCP HTTP Proxy Usage Guide

This document explains how to use the HTTP proxy for accessing Chroma MCP functionality over standard HTTP JSON-RPC instead of the default stdio transport.

## Overview

The Chroma MCP service is designed to work with the MCP (Machine Communication Protocol) system which uses stdio as its primary transport. This works well for direct client-server connections but can be limiting in networked environments. 

The HTTP proxy provides a bridge that allows standard HTTP clients to interact with the Chroma MCP service using JSON-RPC over HTTP, making it more accessible for various applications and development environments.

## Available Proxy Types

The Chroma MCP HTTP Proxy supports multiple implementation methods to accommodate different environments:

1. **Direct Proxy (default)** - Uses the `mcp` command directly via subprocess
2. **WebSocket Proxy** - Uses Docker commands to execute commands in the chroma-mcp container
3. **Functional Proxy** - Uses a custom approach to call the mcp command
4. **Simple Proxy** - Returns mock responses for testing and development

You can select the proxy type by setting the `PROXY_TYPE` environment variable in the `docker-compose.yaml` file.

## Setup and Configuration

The HTTP proxy is configured in the `docker-compose.yaml` file with the following settings:

```yaml
chroma-http-proxy:
  build:
    context: '.'
    dockerfile: docker/http-proxy.Dockerfile
  container_name: chroma-http-proxy
  ports:
    - "10550:10550"
  environment:
    - CHROMA_MCP_HOST=chroma-mcp
    - HTTP_HOST=0.0.0.0
    - HTTP_PORT=10550
    - PROXY_TYPE=direct  # Options: websocket, functional, direct, or simple
    - MCP_EXECUTABLE=mcp
  volumes:
    - /var/run/docker.sock:/var/run/docker.sock  # Required for websocket proxy
  networks:
    - ai-services-network
  depends_on:
    - chroma-mcp
  restart: unless-stopped
```

### Key Configuration Parameters

- `PROXY_TYPE` - Selects the proxy implementation method
- `HTTP_HOST` - Host interface to bind to (default: 0.0.0.0)
- `HTTP_PORT` - Port to listen on (default: 10550)
- `CHROMA_MCP_HOST` - Hostname of the chroma-mcp service
- `MCP_EXECUTABLE` - Path to the mcp executable (default: mcp)

## JSON-RPC API

### Endpoint

The JSON-RPC API is available at the root endpoint: `http://localhost:10550/`

### Health Check

A health check endpoint is available at: `http://localhost:10550/health`

Sample response:
```json
{
  "status": "healthy",
  "service": "chroma-mcp-http-proxy",
  "chroma_mcp_available": true
}
```

### Request Format

Requests should follow the JSON-RPC 2.0 specification:

```json
{
  "jsonrpc": "2.0",
  "method": "chroma_list_collections",
  "params": {},
  "id": 1
}
```

### Available Methods

All Chroma MCP methods are accessible through the HTTP proxy. The most common methods include:

- `chroma_list_collections` - List all collections in the database
- `chroma_create_collection` - Create a new collection
- `chroma_delete_collection` - Delete a collection
- `chroma_add_documents` - Add documents to a collection
- `chroma_query_documents` - Query documents in a collection
- `chroma_get_documents` - Get documents from a collection

### Method Aliases

For convenience, the proxy also supports method aliases that omit the `chroma_` prefix:

- `list_collections` → `chroma_list_collections`
- `create_collection` → `chroma_create_collection`
- `delete_collection` → `chroma_delete_collection`
- `add_documents` → `chroma_add_documents`
- `query_documents` → `chroma_query_documents`
- `get_documents` → `chroma_get_documents`

## Examples

### Testing the Health Endpoint

```bash
curl -v http://localhost:10550/health
```

### Listing Collections

```bash
curl -X POST -H "Content-Type: application/json" -d '{"jsonrpc": "2.0", "method": "chroma_list_collections", "params": {}, "id": 1}' http://localhost:10550/
```

### Creating a Collection

```bash
curl -X POST -H "Content-Type: application/json" -d '{
  "jsonrpc": "2.0", 
  "method": "chroma_create_collection", 
  "params": {
    "collection_name": "my_collection"
  }, 
  "id": 1
}' http://localhost:10550/
```

### Adding Documents

```bash
curl -X POST -H "Content-Type: application/json" -d '{
  "jsonrpc": "2.0", 
  "method": "chroma_add_documents", 
  "params": {
    "collection_name": "my_collection",
    "documents": ["Document 1 content", "Document 2 content"],
    "metadatas": [{"source": "doc1"}, {"source": "doc2"}],
    "ids": ["doc1", "doc2"]
  }, 
  "id": 1
}' http://localhost:10550/
```

### Querying Documents

```bash
curl -X POST -H "Content-Type: application/json" -d '{
  "jsonrpc": "2.0", 
  "method": "chroma_query_documents", 
  "params": {
    "collection_name": "my_collection",
    "query_texts": ["similar to this text"],
    "n_results": 2
  }, 
  "id": 1
}' http://localhost:10550/
```

## Python Client Example

```python
import requests
import json

def call_chroma_api(method, params=None):
    """Call the Chroma MCP HTTP API."""
    url = "http://localhost:10550/"
    
    # Create a JSON-RPC request
    request = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params or {},
        "id": 1
    }
    
    # Send the request
    response = requests.post(
        url, 
        json=request,
        headers={"Content-Type": "application/json"}
    )
    
    # Parse the response
    if response.status_code == 200:
        return response.json().get("result")
    else:
        raise Exception(f"API call failed: {response.text}")

# Example: List collections
collections = call_chroma_api("chroma_list_collections")
print(f"Collections: {collections}")

# Example: Create a collection
result = call_chroma_api("chroma_create_collection", {
    "collection_name": "test_collection"
})
print(f"Create result: {result}")
```

## Troubleshooting

### Proxy Not Responding

If the proxy is not responding, check:

1. Make sure the chroma-http-proxy container is running:
   ```bash
   docker ps | grep chroma-http-proxy
   ```

2. Check the logs for any errors:
   ```bash
   docker logs chroma-http-proxy
   ```

3. Verify the port mapping is correct:
   ```bash
   docker-compose ps chroma-http-proxy
   ```

### JSON-RPC Errors

Common JSON-RPC error codes:

- `-32700`: Parse error - Invalid JSON
- `-32600`: Invalid Request - The JSON sent is not a valid Request object
- `-32601`: Method not found - The method does not exist or is not available
- `-32602`: Invalid params - Invalid method parameter(s)
- `-32603`: Internal error - Internal JSON-RPC error

If you encounter JSON-RPC errors, ensure your request format follows the JSON-RPC 2.0 specification and that the method and parameters are correct.

### Incompatible Proxy Type

If you experience issues with one proxy type, try another by modifying the `PROXY_TYPE` environment variable in `docker-compose.yaml`:

```yaml
environment:
  - PROXY_TYPE=direct  # Try: websocket, functional, or simple
```

Then rebuild and restart the container:

```bash
docker-compose up -d --build chroma-http-proxy
```