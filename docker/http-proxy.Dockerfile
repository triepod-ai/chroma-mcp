FROM python:3.10-slim

WORKDIR /app

# Install necessary dependencies
RUN pip install --no-cache-dir fastapi uvicorn httpx
RUN apt-get update && apt-get install -y docker.io && apt-get clean

# Copy all proxy script options
COPY src/proxies/websocket_http_proxy.py /app/websocket_http_proxy.py
COPY src/proxies/functional_http_proxy.py /app/functional_http_proxy.py
COPY src/proxies/direct_http_proxy.py /app/direct_http_proxy.py
COPY src/proxies/simple_http_proxy.py /app/simple_http_proxy.py

# Set environment variables
ENV HTTP_HOST=0.0.0.0
ENV HTTP_PORT=10550
ENV CHROMA_MCP_HOST=chroma-mcp
ENV PROXY_TYPE=direct

# Expose the HTTP port
EXPOSE 10550

# Create entrypoint script to select the appropriate proxy
RUN echo '#!/bin/bash\n\
case "$PROXY_TYPE" in\n\
  "websocket")\n\
    echo "Starting WebSocket proxy..."\n\
    python websocket_http_proxy.py\n\
    ;;\n\
  "functional")\n\
    echo "Starting Functional proxy..."\n\
    python functional_http_proxy.py\n\
    ;;\n\
  "direct")\n\
    echo "Starting Direct proxy..."\n\
    python direct_http_proxy.py\n\
    ;;\n\
  "simple")\n\
    echo "Starting Simple proxy..."\n\
    python simple_http_proxy.py\n\
    ;;\n\
  *)\n\
    echo "Unknown proxy type: $PROXY_TYPE, defaulting to direct proxy"\n\
    python direct_http_proxy.py\n\
    ;;\n\
esac' > /app/start_proxy.sh && chmod +x /app/start_proxy.sh

# Run the selected proxy server
CMD ["/app/start_proxy.sh"]