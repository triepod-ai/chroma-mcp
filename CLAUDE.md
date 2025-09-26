# Chroma MCP Server Development Guide

## Project Status Documentation

### Current Project Status Reference

**Authoritative Source**: `PROJECT_STATUS.md` contains the definitive current state including:

- **Current Phase Status**: Migration progress, completion percentages, and active development focus
- **Priority Rankings**: Immediate next actions, current development tasks, and upcoming phases  
- **Legacy Integration Results**: Documentation consolidation outcomes and system integration status
- **Deployment Status**: Service health, environment configurations, and production readiness
- **Performance Metrics**: Memory system health, optimization achievements, and reliability statistics

### Status Management Commands

**Session Management:**
- `/brainpod-PROJECT-STATUS-LOAD` - Load current project status for session context
- `/brainpod-PROJECT-STATUS-UPDATE` - Update project status with recent progress
- `/brainpod-init-quick-status-to-claude-link` - Sync CLAUDE.md with PROJECT_STATUS.md references

**Development Workflow:**
1. **Session Start**: Use `/brainpod-PROJECT-STATUS-LOAD` to understand current priorities
2. **Development Work**: Follow immediate next actions from PROJECT_STATUS.md
3. **Progress Update**: Use `/brainpod-PROJECT-STATUS-UPDATE` to document completion
4. **Context Preservation**: Maintain living document synchronization

### Status Integration Benefits

- **Eliminates Duplication**: CLAUDE.md provides development guidance while PROJECT_STATUS.md tracks current state
- **Session Continuity**: Claude can immediately understand project context and priorities
- **Living Documentation**: Status files automatically track progress and maintain audit trails
- **Cross-Project Consistency**: Standardized status format across all projects

---

## Development Environment

### WSL Integration

This project runs in WSL2 with Docker containers. Key development files:

- **Wrapper Script**: `/home/bryan/run-chroma-mcp.sh` - Primary MCP server access
- **Container Access**: Uses `docker exec` for MCP protocol communication
- **Port Configuration**: See PROJECT_STATUS.md for current port allocations

### Architecture

- **ChromaDB**: Vector database with sequential thinking capabilities
- **MCP Server**: Model Context Protocol server for Claude integration
- **HTTP Proxy**: JSON-RPC endpoint (status: see PROJECT_STATUS.md)

---

## Development Workflows

### Testing and Validation

```bash
# Test MCP server functionality
./run-chroma-mcp.sh

# Check container health
docker compose ps

# Monitor logs
docker compose logs -f chroma-mcp
```

### Sequential Thinking Features

This is an enhanced version of the Chroma MCP server with additional sequential thinking capabilities:

- **Structured Reasoning**: Multi-step thought processes with branching
- **Session Management**: Persistent thinking sessions with context
- **Memory Integration**: Links with other memory systems (Neo4j, Qdrant)

### Development Standards

- **Python**: Use `python3` command (not `python`)
- **Package Management**: Use `uv` for virtual environments
- **Container Strategy**: Maintain Docker containers, use wrapper scripts
- **Port Management**: Follow allocations defined in PROJECT_STATUS.md

---

## MCP Tools and Capabilities

### Core Chroma Operations

- Collection management (create, list, modify, delete)
- Document operations (add, query, get, update, delete)
- Advanced filtering with metadata queries
- **Collection inspection**: `chroma_peek_collection` and `chroma_get_collection_info` ✅ **FIXED** (2025-07-23)

### Sequential Thinking Tools

- `chroma_sequential_thinking`: Store and process sequential thoughts
- `chroma_get_similar_sessions`: Find related thinking sessions
- `chroma_get_thought_history`: Retrieve complete thought chains
- `chroma_continue_thought_chain`: Analyze and continue reasoning

### Integration Features

- **Memory Orchestration**: Cross-system storage with Redis + Qdrant + Neo4j
- **Context Bridge**: Conversation-level caching and context preservation
- **Performance Optimization**: 90%+ token reduction through intelligent routing

### Recent Fixes

**Numpy Serialization Issue (2025-07-23)** ✅ **RESOLVED**
- **Issue**: `chroma_peek_collection` and `chroma_get_collection_info` failed with numpy array serialization errors
- **Root Cause**: ChromaDB's `.peek()` method returns embeddings as numpy arrays that cannot be JSON-serialized for MCP responses
- **Solution**: Modified both functions to remove embeddings before returning to client
- **Status**: Both functions now work correctly for collection inspection and debugging workflows

---

## Troubleshooting

### Common Issues

1. **Container Health**: Check PROJECT_STATUS.md for current service status
2. **Port Conflicts**: Refer to PROJECT_STATUS.md port allocation table
3. **Permission Issues**: WSL file permissions resolved (see migration notes)

### ✅ Resolved Issues

**Numpy Serialization Errors (Fixed 2025-07-23)**
- **Symptoms**: `chroma_peek_collection` and `chroma_get_collection_info` fail with "Unable to serialize unknown type: numpy.ndarray"
- **Root Cause**: ChromaDB's `.peek()` method returns embeddings as numpy arrays that cannot be JSON-serialized
- **Resolution**: Fixed in `src/chroma_mcp/server.py` by removing embeddings from responses
- **Status**: ✅ Both functions now work correctly

### Debugging Commands

```bash
# Check container status
docker compose ps

# View container logs
docker compose logs chroma-mcp

# Test MCP connection
echo '{"jsonrpc": "2.0", "id": 1, "method": "ping"}' | ./run-chroma-mcp.sh

# Test specific functions (if issues arise)
docker exec chroma-mcp python -c "
from chroma_mcp.server import get_chroma_client
client = get_chroma_client()
collection = client.get_collection('collection_name')
results = collection.peek(limit=3)
print('Peek keys:', list(results.keys()))
"
```

### Container Rebuild Process

If code changes aren't reflected (due to Docker COPY behavior):
```bash
# Stop container
docker-compose stop chroma-mcp

# Rebuild with updated code
docker-compose build chroma-mcp

# Start updated container
docker-compose up -d chroma-mcp
```

### Migration Context

Successfully migrated from Windows to WSL2. All development should now occur in the WSL environment using the wrapper script approach. See PROJECT_STATUS.md for detailed migration status and any remaining tasks.

---

## Next Steps

**Current priorities and action items are maintained in PROJECT_STATUS.md**

For session-specific development:
1. Check PROJECT_STATUS.md for immediate next actions
2. Follow the current phase priorities listed there
3. Update PROJECT_STATUS.md upon task completion
4. Use status management commands for session continuity

---

*This development guide defers to PROJECT_STATUS.md for current project state, priorities, and specific tasks. Always consult PROJECT_STATUS.md for the most up-to-date information about project status and next actions.*