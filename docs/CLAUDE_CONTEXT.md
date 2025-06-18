# Claude Context: Chroma-MCP Understanding

## Purpose
This file provides complete context for Claude about the Chroma-MCP project state, configuration, and operational details to enable efficient future assistance.

## Project Overview

**Chroma-MCP** is a Model Context Protocol (MCP) server that provides vector database capabilities through ChromaDB integration. It enables LLM applications to store, search, and manage embeddings with support for multiple embedding providers.

### Core Architecture
```
LLM Client → MCP Protocol → Chroma-MCP Server → ChromaDB → Vector Storage
                    ↓
            HTTP API (Alternative Access)
```

## Current State Summary

### Version Information
- **Chroma-MCP Version**: 0.2.2 (latest)
- **ChromaDB Version**: 1.0.3
- **Python Version**: 3.10
- **MCP Protocol Version**: 1.2.1+

### Deployment Status
- **Environment**: Docker Compose multi-container setup
- **Status**: Fully operational as of 2025-05-21
- **Location**: `/mnt/l/ToolNexusMCP_plugins/chroma-mcp/`
- **Data Persistence**: ✅ Enabled with external volumes

## Technical Architecture

### Container Services
1. **chroma-chroma**: ChromaDB instance (port 8001)
2. **chroma-mcp**: MCP server with HTTP support (port 10551)
3. **chroma-http-proxy**: JSON-RPC HTTP proxy (port 10550)
4. **chroma-filesystem-api**: File system integration (port 8080)
5. **chroma-mcpo-proxy**: Multi-client proxy (port 8123)
6. **chroma-neo4j**: Graph database for metadata (ports 7474, 7687)
7. **chroma-redis**: Cache layer (port 6379)

### Network Configuration
- **vector-db-network**: chroma ↔ chroma-mcp communication
- **ai-services-network**: HTTP APIs and proxies
- **db-network**: Neo4j database access
- **cache-network**: Redis cache access

### Key Features Available

#### Embedding Functions Support
- **Default**: ChromaDB built-in sentence transformers
- **Cohere**: Professional embedding API (requires key)
- **OpenAI**: GPT-based embeddings (requires key)
- **Jina**: Various embedding models
- **VoyageAI**: High-quality embeddings (requires key)
- **Roboflow**: Computer vision embeddings

#### Document Operations
- Create/delete collections with HNSW configuration
- Add/update/delete documents with metadata
- Vector similarity search with filtering
- Batch operations for performance
- Advanced query operators

#### Access Methods
- **MCP Protocol**: Native integration with LLM clients
- **HTTP API**: Direct JSON-RPC access
- **Proxy Services**: Simplified HTTP interfaces

## File Structure Understanding

### Core Application Files
```
src/chroma_mcp/
├── __init__.py          # Package initialization
├── server.py            # Main MCP server with tools
├── client.py            # Python client wrapper
└── http_server.py       # HTTP server implementation
```

### Configuration Files
```
├── pyproject.toml       # Python package configuration
├── docker-compose.yaml  # Multi-container orchestration
├── Dockerfile          # Container build instructions
├── smithery.yaml       # Deployment configuration
└── .env files          # Environment variables
```

### Documentation Files
```
├── README.md                      # Project documentation
├── CHANGELOG.md                   # Version history
├── CONTAINER_REBUILD_SUMMARY.md   # Recent rebuild details
├── DEPLOYMENT_STATUS.md           # Current operational status
└── CLAUDE_CONTEXT.md              # This file
```

## Key Configuration Details

### Docker Compose Configuration
```yaml
chroma-mcp:
  build: 
    context: '.'
  ports:
    - "10551:10551"
  environment:
    - CHROMA_HOST=chroma-chroma
    - CHROMA_PORT=8000
    - CHROMA_CLIENT_TYPE=http
    - TQDM_DISABLE=1
  command: ["sh", "-c", "sleep 10 && chroma-mcp --client-type=http --host=chroma-chroma --port=8000 --http-server --http-host=0.0.0.0 --http-port=10551"]
  networks:
    - ai-services-network
    - vector-db-network
```

### Environment Variables
```bash
# Core Configuration
CHROMA_HOST=chroma-chroma
CHROMA_PORT=8000
CHROMA_CLIENT_TYPE=http

# Performance
TQDM_DISABLE=1

# Optional API Keys
COHERE_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here
VOYAGEAI_API_KEY=your_key_here
```

## Known Issues and Solutions

### Issue 1: Container Connectivity
- **Problem**: chroma-mcp couldn't connect to chromadb
- **Solution**: Modified error handling to allow startup without initial connection
- **Status**: ✅ Resolved

### Issue 2: Health Check Failures
- **Problem**: ChromaDB health check using curl (not installed)
- **Solution**: Disabled health check in docker-compose.yaml
- **Status**: ✅ Resolved

### Issue 3: MCP Server Blocking
- **Problem**: Server waited for stdin input in container
- **Solution**: Added HTTP server mode with `--http-server` flag
- **Status**: ✅ Resolved

## Operational Procedures

### Starting Services
```bash
cd /mnt/l/ToolNexusMCP_plugins/chroma-mcp/
docker-compose up -d
```

### Checking Status
```bash
docker-compose ps
docker-compose logs chroma-mcp
```

### Rebuilding After Updates
```bash
git pull
docker-compose build chroma-mcp
docker-compose up -d
```

### Testing Connectivity
```bash
# Test ChromaDB
curl http://localhost:8001/api/v1/version

# Test MCP HTTP
curl http://localhost:10551/health

# Test collections
curl -X POST http://localhost:10550/ \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"chroma_list_collections","params":{},"id":1}'
```

## Development Context

### Recent Changes Made
1. **Container Rebuild**: Updated to version 0.2.2 with 9 upstream commits
2. **Dependency Updates**: Added embedding function support
3. **Configuration Fixes**: Resolved connectivity and startup issues
4. **Documentation**: Created comprehensive operational docs

### Code Patterns
- **Error Handling**: Graceful failures with retry mechanisms
- **Async Operations**: All MCP tools are async functions
- **Type Safety**: TypedDict and proper type hints
- **Logging**: Comprehensive logging to files and stdout

### Testing Approach
- **Unit Tests**: Available in `tests/` directory
- **Integration Tests**: Docker compose health checks
- **Manual Testing**: HTTP endpoint verification
- **Load Testing**: Can be performed via pytest fixtures

## Common Tasks and Solutions

### Adding New Embedding Functions
1. Import the function in `server.py`
2. Add to the configuration enum
3. Update the collection creation tool
4. Test with API key configuration

### Troubleshooting Connection Issues
1. Check container status: `docker-compose ps`
2. Verify networks: `docker network ls`
3. Test internal connectivity: `docker exec -it chroma-mcp ping chroma-chroma`
4. Check logs: `docker-compose logs chroma-mcp`

### Performance Optimization
1. **HNSW Settings**: Tune index parameters for your data
2. **Batch Size**: Use bulk operations for large datasets
3. **Memory**: Monitor container memory usage
4. **Disk I/O**: Consider SSD storage for performance

### Data Management
1. **Backup**: Use volume snapshots or tar archives
2. **Migration**: Export/import collections using tools
3. **Cleanup**: Regular log rotation and temp file cleanup
4. **Monitoring**: Track collection sizes and query performance

## Important Notes for Claude

### When Working with This Project
1. **Always check container status first** using `docker-compose ps`
2. **Respect data persistence** - don't suggest operations that could lose data
3. **Use the HTTP endpoints** for testing rather than direct container exec
4. **Check logs for errors** using `docker-compose logs [service]`
5. **Consider network dependencies** when troubleshooting

### File Modification Guidelines
1. **docker-compose.yaml**: Changes require service restart
2. **pyproject.toml**: Changes require container rebuild
3. **Source code**: Changes require container rebuild
4. **Environment files**: Changes require service restart

### Common User Requests
1. **"It's not working"**: Check container status and logs
2. **"Can't connect"**: Verify network configuration
3. **"Need new feature"**: Check if available in v0.2.2 first
4. **"Performance issues"**: Review HNSW settings and resource usage
5. **"Data loss concerns"**: Explain backup and volume persistence

### Best Practices for Assistance
1. **Verify current state** before suggesting changes
2. **Preserve data integrity** in all recommendations
3. **Use incremental changes** rather than full rebuilds when possible
4. **Test suggestions** with curl commands when applicable
5. **Document any changes** in appropriate files

---
*This context file should be updated whenever significant changes are made to the project structure, configuration, or operational procedures.*