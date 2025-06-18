# OpenAPI Filesystem Server Integration

This guide explains how to integrate the OpenAPI Filesystem Server with the existing Chroma MCP stack.

## What is the OpenAPI Filesystem Server?

The OpenAPI Filesystem Server provides a secure REST API for file system operations, including:

- Reading and writing files
- Creating and listing directories
- Searching for files and content
- Getting file metadata
- Moving and deleting files

## Setup Instructions

The Filesystem API has been added to the existing Chroma MCP stack and can be started with the standard docker compose command:

```bash
# From the chroma-mcp directory
docker-compose up -d
```

This will:
- Build the Dockerfile for the filesystem server
- Start the server with access to configured directories
- Make the API available on `http://localhost:8080`

### Directory Access Configuration

By default, the filesystem server is configured to access the Windows C:/Users directory. You can customize this by editing the `docker-compose.yaml` file:

```yaml
filesystem-api:
  # ...
  volumes:
    - /C:/Users:/app/users  # Change this to mount different directories
  environment:
    - ALLOWED_DIRECTORIES=/app/users  # Change this to match your volume mounts
```

You can mount multiple directories by separating them with colons in the environment variable:

```yaml
environment:
  - ALLOWED_DIRECTORIES=/app/users:/app/other_dir
```

## Using the Filesystem API

You can access the API directly at http://localhost:8080 once the stack is running. The API documentation is available at http://localhost:8080/docs.

### API Endpoints

- `/read_file` - Read a file's contents
- `/write_file` - Write content to a file
- `/edit_file` - Edit specific parts of a file
- `/list_directory` - List a directory's contents
- `/directory_tree` - Get a recursive tree of a directory
- `/search_files` - Search for files by name
- `/search_content` - Search for content within files
- `/get_metadata` - Get file metadata
- `/move_path` - Move or rename a file or directory
- `/delete_path` - Delete a file or directory
- `/create_directory` - Create a new directory

### Configuring Open WebUI to Use the Filesystem API

1. Open the Open WebUI interface
2. Navigate to ⚙️ Settings
3. Click on ➕ Tools to add a new tool server
4. Enter the URL: `http://localhost:8080`
5. Click "Save"

## Security Considerations

The filesystem server provides access to the host filesystem based on the configured allowed directories. Ensure that you only mount directories that you want to expose through the API.

## Troubleshooting

1. If you can't connect to the filesystem API:
   - Ensure the container is running (`docker-compose ps`)
   - Check the logs for errors (`docker-compose logs filesystem-api`)

2. If files are inaccessible:
   - Check that the path is within the allowed directories
   - Verify the volume mounts in the Docker Compose file
   - Check file permissions on the host

3. To restart just the filesystem service:
   ```bash
   docker-compose restart filesystem-api
