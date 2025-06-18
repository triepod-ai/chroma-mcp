FROM node:20-alpine

# Install necessary system packages
RUN apk add --no-cache \
    nginx \
    certbot \
    certbot-nginx \
    bash \
    curl \
    docker-cli

# Install mcp-proxy globally
RUN npm install -g mcp-proxy

# Create application directory
WORKDIR /app

# Create nginx configuration template
COPY docker/nginx-sse.conf.template /etc/nginx/nginx.conf.template

# Create entrypoint script
COPY docker/sse-simple-entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Environment variables
ENV DOMAIN=""
ENV HTTP_PORT=3633
ENV HTTPS_PORT=443
ENV SSL_EMAIL=""
ENV MCP_WRAPPER="/home/bryan/run-chroma-mcp.sh"

# Expose ports
EXPOSE 80 443 3633

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${HTTP_PORT}/health || exit 1

# Use entrypoint script
ENTRYPOINT ["/entrypoint.sh"]