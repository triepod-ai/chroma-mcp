#!/bin/bash
set -e

# Create data directory if it doesn't exist
mkdir -p /data

# Fix permissions on data directory
chmod -R 777 /data

# Execute the original entrypoint command
exec "$@"
