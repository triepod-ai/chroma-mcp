#!/bin/bash

# Chroma MCP SSE Deployment Script
# Usage: ./deploy-sse.sh [domain] [email]

set -e

# Configuration
DOMAIN="${1:-bot.triepod.ai}"
EMAIL="${2:-admin@triepod.ai}"
COMPOSE_FILE="docker-compose.sse.yaml"

echo "🚀 Deploying Chroma MCP SSE Server"
echo "=================================="
echo "Domain: $DOMAIN"
echo "Email: $EMAIL"
echo "Compose: $COMPOSE_FILE"
echo ""

# Check prerequisites
echo "🔍 Checking prerequisites..."

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose not found. Please install Docker Compose."
    exit 1
fi

# Check if the compose file exists
if [ ! -f "$COMPOSE_FILE" ]; then
    echo "❌ $COMPOSE_FILE not found."
    exit 1
fi

# Stop existing containers
echo "🛑 Stopping existing containers..."
docker-compose -f "$COMPOSE_FILE" down || true

# Build the SSE server image
echo "🔨 Building SSE server image..."
docker-compose -f "$COMPOSE_FILE" build chroma-sse

# Start the services
echo "🚀 Starting services..."
DOMAIN="$DOMAIN" SSL_EMAIL="$EMAIL" docker-compose -f "$COMPOSE_FILE" up -d

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 10

# Check service health
echo "🏥 Checking service health..."
docker-compose -f "$COMPOSE_FILE" ps

# Test HTTP endpoint (before SSL)
echo "🧪 Testing HTTP endpoint..."
if curl -f "http://localhost:3633/health" > /dev/null 2>&1; then
    echo "✅ HTTP health check passed"
else
    echo "❌ HTTP health check failed"
fi

echo ""
echo "🎉 Deployment complete!"
echo ""
echo "📍 Endpoints:"
echo "  Local HTTP:  http://localhost:3633/sse"
echo "  Local HTTPS: https://localhost/sse (after SSL setup)"
echo "  Public:      https://$DOMAIN/sse (after DNS propagation)"
echo ""
echo "📋 Next steps:"
echo "1. Set DNS A record: $DOMAIN → YOUR_PUBLIC_IP"
echo "2. Wait for DNS propagation (5-30 minutes)"
echo "3. SSL certificate will be automatically obtained"
echo "4. Test with: curl https://$DOMAIN/sse"
echo ""
echo "📱 Monitor with:"
echo "  docker-compose -f $COMPOSE_FILE logs -f chroma-sse"