FROM node:20-alpine

# Install necessary system packages
RUN apk add --no-cache \
    nginx \
    certbot \
    certbot-nginx \
    bash \
    curl \
    python3 \
    py3-pip \
    docker-cli

# Install mcp-proxy globally
RUN npm install -g mcp-proxy

# Create application directory
WORKDIR /app

# Copy the chroma-mcp source
COPY src/ /app/src/
COPY pyproject.toml /app/
COPY requirements-filesystem.txt /app/

# Install Python dependencies for chroma-mcp (break system packages for container)
RUN pip3 install --no-cache-dir --break-system-packages chromadb>=1.0.3 httpx>=0.28.1 mcp[cli]>=1.2.1

# Create nginx configuration template
COPY docker/nginx-sse.conf.template /etc/nginx/nginx.conf.template

# Create entrypoint script
COPY docker/sse-entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Copy SSE startup script
COPY chroma-mcp-sse.sh /app/chroma-mcp-sse.sh
RUN chmod +x /app/chroma-mcp-sse.sh

# Environment variables
ENV DOMAIN=""
ENV HTTP_PORT=3633
ENV HTTPS_PORT=443
ENV CHROMA_HOST=chroma-chroma
ENV CHROMA_PORT=8000
ENV SSL_EMAIL=""

# Expose ports
EXPOSE 80 443 3633

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${HTTP_PORT}/health || exit 1

# Use entrypoint script
ENTRYPOINT ["/entrypoint.sh"]