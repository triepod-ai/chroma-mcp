<p align="center">
  <a href="https://trychroma.com"><img src="https://user-images.githubusercontent.com/891664/227103090-6624bf7d-9524-4e05-9d2c-c28d5d451481.png" alt="Chroma logo"></a>
</p>

<p align="center">
    <b>Chroma - the open-source embedding database</b>. <br />
    The fastest way to build Python or JavaScript LLM apps with memory!
</p>

<p align="center">
  <a href="https://discord.gg/MMeYNTmh3x" target="_blank">
      <img src="https://img.shields.io/discord/1073293645303795742?cacheSeconds=3600" alt="Discord">
  </a> |
  <a href="https://github.com/chroma-core/chroma/blob/master/LICENSE" target="_blank">
      <img src="https://img.shields.io/static/v1?label=license&message=Apache 2.0&color=white" alt="License">
  </a> |
  <a href="https://docs.trychroma.com/" target="_blank">
      Docs
  </a> |
  <a href="https://www.trychroma.com/" target="_blank">
      Homepage
  </a>
</p>

# Chroma MCP Server

> **Note**: This is an enhanced fork of the original [chroma-core/chroma-mcp](https://github.com/chroma-core/chroma-mcp) project, featuring FastMCP architecture, streamable HTTP transport, and additional enhancements for production use.

[![smithery badge](https://smithery.ai/badge/@chroma-core/chroma-mcp)](https://smithery.ai/server/@chroma-core/chroma-mcp)

## MCP SDK Version

**Current Version**: Python MCP SDK 1.15.0 (upgraded October 1, 2025)

This server uses the latest Model Context Protocol SDK with enhanced capabilities:

### New Features:
- **Paginated List Decorators**: Support for paginated prompts, resources, and tools
- **Protected Resource Metadata**: Improved metadata handling for resources
- **Enhanced Security**: HTTP 403 responses for invalid Origin headers
- **Default Values**: Elicitation schema support for default values
- **Extended Metadata**: Additional metadata and icon support in SDK

**Previous Version**: 1.2.1 → **Upgrade Jump**: 13+ major versions (significant protocol enhancements)

**Compatibility**: The upgrade maintains full backward compatibility while enabling new optional features when MCP clients support them. All existing tool definitions and workflows continue to work unchanged.

### Installation Notes:
All 123 packages installed successfully in a fresh `uv` virtual environment. Server tested and operational with the `chroma-mcp` entry point.

For complete MCP protocol documentation, see [Model Context Protocol](https://modelcontextprotocol.io/).

[The Model Context Protocol (MCP)](https://modelcontextprotocol.io/introduction) is an open protocol designed for effortless integration between LLM applications and external data sources or tools, offering a standardized framework to seamlessly provide LLMs with the context they require.

This server provides data retrieval capabilities powered by Chroma, enabling AI models to create collections over generated data and user inputs, and retrieve that data using vector search, full text search, metadata filtering, and more.

## Enhancements in This Fork

- **FastMCP Architecture**: Modernized codebase following FastMCP template patterns
- **Streamable HTTP Transport**: MCP-compliant HTTP server implementation (port 10550)
- **Improved Type Safety**: Full Pydantic validation and structured error handling
- **Docker-First Deployment**: Production-ready containerized setup
- **Enhanced Documentation**: Comprehensive guides for development and deployment

## Features

- **Flexible Client Types**
  - Ephemeral (in-memory) for testing and development
  - Persistent for file-based storage
  - HTTP client for self-hosted Chroma instances
  - Cloud client for Chroma Cloud integration (automatically connects to api.trychroma.com)

- **Collection Management**
  - Create, modify, and delete collections
  - List all collections with pagination support
  - Get collection information and statistics
  - Configure HNSW parameters for optimized vector search
  - Select embedding functions when creating collections

- **Document Operations**
  - Add documents with optional metadata and custom IDs
  - Query documents using semantic search
  - Advanced filtering using metadata and document content
  - Retrieve documents by IDs or filters
  - Full text search capabilities

### Supported Tools

- `chroma_list_collections` - List all collections with pagination support
- `chroma_create_collection` - Create a new collection with optional HNSW configuration
- `chroma_peek_collection` - View a sample of documents in a collection
- `chroma_get_collection_info` - Get detailed information about a collection
- `chroma_get_collection_count` - Get the number of documents in a collection
- `chroma_modify_collection` - Update a collection's name or metadata
- `chroma_delete_collection` - Delete a collection
- `chroma_add_documents` - Add documents with optional metadata and custom IDs
- `chroma_query_documents` - Query documents using semantic search with advanced filtering
- `chroma_get_documents` - Retrieve documents by IDs or filters with pagination
- `chroma_update_documents` - Update existing documents' content, metadata, or embeddings
- `chroma_delete_documents` - Delete specific documents from a collection

### Embedding Functions
Chroma MCP supports several embedding functions: `default`, `cohere`, `openai`, `jina`, `voyageai`, and `roboflow`.

The embedding functions utilize Chroma's collection configuration, which persists the selected embedding function of a collection for retrieval. Once a collection is created using the collection configuration, on retrieval for future queries and inserts, the same embedding function will be used, without needing to specify the embedding function again. Embedding function persistance was added in v1.0.0 of Chroma, so if you created a collection using version <=0.6.3, this feature is not supported.

When accessing embedding functions that utilize external APIs, please be sure to add the environment variable for the API key with the correct format, found in [Embedding Function Environment Variables](#embedding-function-environment-variables)

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

3. To connect to Chroma Cloud, add the following to your `claude_desktop_config.json` file:

```json
"chroma": {
    "command": "uvx",
    "args": [
        "chroma-mcp",
        "--client-type",
        "cloud",
        "--tenant",
        "your-tenant-id",
        "--database",
        "your-database-name",
        "--api-key",
        "your-api-key"
    ]
}
```

This will create a cloud client that automatically connects to api.trychroma.com using SSL.

**Note:** Adding API keys in arguments is fine on local devices, but for safety, you can also specify a custom path for your environment configuration file using the `--dotenv-path` argument within the `args` list, for example: `"args": ["chroma-mcp", "--dotenv-path", "/custom/path/.env"]`.

4. To connect to a [self-hosted Chroma instance on your own cloud provider](https://docs.trychroma.com/
production/deployment), add the following to your `claude_desktop_config.json` file:

```json
"chroma": {
    "command": "uvx",
    "args": [
      "chroma-mcp", 
      "--client-type", 
      "http", 
      "--host", 
      "your-host", 
      "--port", 
      "your-port", 
      "--custom-auth-credentials",
      "your-custom-auth-credentials",
      "--ssl",
      "true"
    ]
}
```

This will create an HTTP client that connects to your self-hosted Chroma instance.

### Demos

Find reference usages, such as shared knowledge bases & adding memory to context windows in the [Chroma MCP Docs](https://docs.trychroma.com/integrations/frameworks/anthropic-mcp#using-chroma-with-claude)

### Using Environment Variables

You can also use environment variables to configure the client. The server will automatically load variables from a `.env` file located at the path specified by `--dotenv-path` (defaults to `.chroma_env` in the working directory) or from system environment variables. Command-line arguments take precedence over environment variables.

```bash
# Common variables
export CHROMA_CLIENT_TYPE="http"  # or "cloud", "persistent", "ephemeral"

# For persistent client
export CHROMA_DATA_DIR="/full/path/to/your/data/directory"

# For cloud client (Chroma Cloud)
export CHROMA_TENANT="your-tenant-id"
export CHROMA_DATABASE="your-database-name"
export CHROMA_API_KEY="your-api-key"

# For HTTP client (self-hosted)
export CHROMA_HOST="your-host"
export CHROMA_PORT="your-port"
export CHROMA_CUSTOM_AUTH_CREDENTIALS="your-custom-auth-credentials"
export CHROMA_SSL="true"

# Optional: Specify path to .env file (defaults to .chroma_env)
export CHROMA_DOTENV_PATH="/path/to/your/.env" 
```

#### Embedding Function Environment Variables
When using external embedding functions that access an API key, follow the naming convention
`CHROMA_<>_API_KEY="<key>"`.
So to set a Cohere API key, set the environment variable `CHROMA_COHERE_API_KEY=""`. We recommend adding this to a .env file somewhere and using the `CHROMA_DOTENV_PATH` environment variable or `--dotenv-path` flag to set that location for safekeeping.
