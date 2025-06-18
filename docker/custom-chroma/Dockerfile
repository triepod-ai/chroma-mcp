FROM chromadb/chroma:1.0.3

# Install curl for healthcheck and other necessary tools
USER root
RUN apt-get update && apt-get install -y curl && apt-get clean && rm -rf /var/lib/apt/lists/*

# Add custom entrypoint script to fix permissions
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Use the custom entrypoint
ENTRYPOINT ["/entrypoint.sh", "dumb-init", "--", "chroma"]
CMD ["run", "/config.yaml"]
