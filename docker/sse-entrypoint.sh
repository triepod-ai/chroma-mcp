#!/bin/bash

set -e

echo "Starting Chroma MCP SSE Container..."
echo "Domain: ${DOMAIN:-localhost}"
echo "HTTP Port: ${HTTP_PORT:-3633}"
echo "HTTPS Port: ${HTTPS_PORT:-443}"

# Create necessary directories
mkdir -p /var/www/certbot
mkdir -p /var/log/nginx
mkdir -p /app/logs

# If domain is specified, set up SSL
if [ -n "$DOMAIN" ]; then
    echo "Setting up SSL for domain: $DOMAIN"
    
    # Substitute environment variables in nginx config
    envsubst '${DOMAIN} ${HTTP_PORT}' < /etc/nginx/nginx.conf.template > /etc/nginx/nginx.conf
    
    # Start nginx in background for Let's Encrypt challenge
    nginx -t && nginx -g "daemon on;"
    
    # Check if certificate already exists
    if [ ! -f "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" ]; then
        echo "Obtaining SSL certificate for $DOMAIN..."
        
        # Get SSL certificate
        certbot certonly \
            --webroot \
            --webroot-path=/var/www/certbot \
            --email "${SSL_EMAIL:-admin@$DOMAIN}" \
            --agree-tos \
            --no-eff-email \
            -d "$DOMAIN"
    else
        echo "SSL certificate already exists for $DOMAIN"
    fi
    
    # Reload nginx with SSL configuration
    nginx -s reload
    
    echo "SSL setup complete. HTTPS endpoint: https://$DOMAIN/sse"
else
    echo "No domain specified, running HTTP only"
    
    # Simple HTTP-only nginx config
    cat > /etc/nginx/nginx.conf << EOF
events {
    worker_connections 1024;
}

http {
    upstream mcp_backend {
        server localhost:${HTTP_PORT};
    }

    server {
        listen 80;
        
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        
        # SSE configuration
        proxy_buffering off;
        proxy_cache off;
        proxy_set_header Connection '';
        proxy_http_version 1.1;
        chunked_transfer_encoding off;
        proxy_read_timeout 86400s;
        
        location / {
            proxy_pass http://mcp_backend;
        }
    }
}
EOF
    
    nginx -t && nginx -g "daemon on;"
fi

# Create a simple wrapper script for the container environment
cat > /app/container-mcp-wrapper.sh << 'EOF'
#!/bin/bash

# Set environment variables for MCP
export PYTHONUNBUFFERED=1
export TQDM_DISABLE=1
export CHROMA_CLIENT_TYPE=http
export CHROMA_HOST=${CHROMA_HOST:-chroma-chroma}
export CHROMA_PORT=${CHROMA_PORT:-8000}
export CHROMA_SSL=false
export ANONYMIZED_TELEMETRY=false
export CHROMA_TELEMETRY_DISABLED=true

# Execute the chroma-mcp server
exec python3 -u -m chroma_mcp.server \
    --client-type http \
    --host "${CHROMA_HOST}" \
    --port "${CHROMA_PORT}" \
    --ssl false "$@"
EOF

chmod +x /app/container-mcp-wrapper.sh

# Start the MCP SSE proxy
echo "Starting MCP SSE proxy on port ${HTTP_PORT}..."

# Create logs directory
mkdir -p /app/logs

# Start mcp-proxy with our wrapper
exec mcp-proxy \
    --port "${HTTP_PORT}" \
    --debug \
    /app/container-mcp-wrapper.sh