# Chroma MCP Server

[The Model Context Protocol (MCP)](https://modelcontextprotocol.io/introduction) is an open protocol that enables seamless integration between LLM applications and external data sources and tools. Whether you’re building an AI-powered IDE, enhancing a chat interface, or creating custom AI workflows, MCP provides a standardized way to connect LLMs with the context they need.

This server provides vector database capabilities for Chroma, enabling AI models to interact with vector embeddings and perform semantic search operations through a standardized interface.

## Features

- **Flexible Client Types**
  - Ephemeral (in-memory) for testing and development
  - Persistent for local production deployments
  - HTTP client for Chroma Cloud integration

- **Collection Management**
  - Create, modify, and delete collections
  - List all collections with pagination support
  - Get collection information and statistics
  - Configure HNSW parameters for optimized vector search

- **Document Operations**
  - Add documents with optional metadata and custom IDs
  - Query documents using semantic search
  - Advanced filtering using metadata and document content
  - Retrieve documents by IDs or filters
  - Full text search capabilities

### Supported Tools

- `create_collection`
- `peek_collection`
- `list_collections`
- `get_collection_info`
- `get_collection_count`
- `modify_collection`
- `delete_collection`
- `add_documents`
- `query_documents`
- `get_documents`

## Usage with Claude Desktop

1. To add an ephemeral client, add the following to your `claude_desktop_config.json` file:

```json
"chroma": {
    "command": "uvx",
    "args": [
        "chroma-mcp"
    ]
}
```

2. To add a persistent client, add the following to your `claude_desktop_config.json` file:

```json
"chroma": {
    "command": "uvx",
    "args": [
        "chroma-mcp",
        "--client-type",
        "persistent",
        "--data-dir",
        "/full/path/to/your/data/directory"
    ]
}
```

This will create a persistent client that will use the data directory specified.

3. To add a HTTP client, add the following to your `claude_desktop_config.json` file:

```json
"chroma": {
    "command": "uvx",
    "args": [
        "chroma-mcp",
        "--client-type",
        "http",
        "--tenant",
        "your-tenant-id",
        "--database",
        "your-database-name",
        "--api-key",
        "your-api-key",
        "--ssl",
        "true"
    ]
}
```

This will create a HTTP client that will use the tenant, database, and API key specified.

### Using Environment Variables

You can also use environment variables to configure the client type, tenant, database, and API key.

```bash
export CHROMA_CLIENT_TYPE="http"
export CHROMA_DATA_DIR="/full/path/to/your/data/directory"
export CHROMA_TENANT="your-tenant-id"
export CHROMA_DATABASE="your-database-name"
export CHROMA_API_KEY="your-api-key"
export CHROMA_SSL="true"
```

