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

# Start the MCP SSE proxy using docker exec to the chroma-mcp container
echo "Starting MCP SSE proxy on port ${HTTP_PORT}..."

# Create a simple health endpoint for the proxy itself
cat > /app/health.js << 'EOF'
const http = require('http');

const server = http.createServer((req, res) => {
    if (req.url === '/health') {
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ status: 'healthy', service: 'mcp-sse-proxy' }));
    } else {
        res.writeHead(404);
        res.end('Not Found');
    }
});

server.listen(3402, () => {
    console.log('Health server running on port 3402');
});
EOF

# Start health server in background
node /app/health.js &

# Start mcp-proxy using docker exec approach
exec mcp-proxy \
    --port "${HTTP_PORT}" \
    --debug \
    docker exec -i chroma-mcp python3 -u -m chroma_mcp.server --client-type http --host chroma-chroma --port 8000 --ssl false