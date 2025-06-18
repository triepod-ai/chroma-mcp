"""Simple HTTP Proxy Server for Chroma MCP"""

import os
import json
import logging
import uvicorn
from fastapi import FastAPI, Request
from starlette.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("chroma-mcp-simple-http")

# Create FastAPI app
app = FastAPI(title="Chroma MCP Simple HTTP Server")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "chroma-mcp-simple-http"}

@app.post("/")
async def json_rpc_endpoint(request: Request):
    """Simple JSON-RPC mock endpoint."""
    try:
        # Parse the request body
        try:
            body = await request.json()
            method = body.get("method", "unknown")
            req_id = body.get("id")
        except Exception as e:
            logger.error(f"Error parsing request: {str(e)}")
            return JSONResponse({
                "jsonrpc": "2.0",
                "error": {"code": -32700, "message": "Parse error: Invalid JSON"},
                "id": None
            })
        
        # Return a simple mock response
        return JSONResponse({
            "jsonrpc": "2.0",
            "result": {
                "message": f"Simple HTTP server received method: {method}",
                "status": "This is a mock response until full proxy implementation is ready"
            },
            "id": req_id
        })
    
    except Exception as e:
        # Log the error
        logger.error(f"Error in JSON-RPC request: {str(e)}")
        
        # Return error response
        return JSONResponse({
            "jsonrpc": "2.0",
            "error": {"code": -32603, "message": f"Internal error: {str(e)}"},
            "id": None
        })

if __name__ == "__main__":
    port = int(os.environ.get("HTTP_PORT", 10550))
    host = os.environ.get("HTTP_HOST", "0.0.0.0")
    
    logger.info(f"Starting simple HTTP server on {host}:{port}")
    uvicorn.run(app, host=host, port=port)