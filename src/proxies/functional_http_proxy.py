"""Functional HTTP Proxy Server for Chroma MCP with JSON-RPC forwarding"""

import os
import json
import logging
import asyncio
import httpx
from fastapi import FastAPI, Request
from starlette.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("chroma-mcp-http-proxy")

# Get environment variables
CHROMA_MCP_HOST = os.environ.get("CHROMA_MCP_HOST", "chroma-mcp")
HTTP_HOST = os.environ.get("HTTP_HOST", "0.0.0.0")
HTTP_PORT = int(os.environ.get("HTTP_PORT", 10550))

# Create FastAPI app
app = FastAPI(title="Chroma MCP HTTP Proxy Server")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def execute_command(cmd, params=None):
    """Execute a command on the chroma-mcp service using subprocess."""
    try:
        process = await asyncio.create_subprocess_exec(
            "mcp", "chroma", cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        # If params are provided, send them as JSON
        if params:
            params_json = json.dumps(params).encode()
            stdout, stderr = await process.communicate(params_json)
        else:
            stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            logger.error(f"Command failed: {stderr.decode()}")
            return {"error": stderr.decode(), "status": "failed"}, 500
        
        try:
            return json.loads(stdout.decode()), 200
        except json.JSONDecodeError:
            return {"error": "Failed to parse response from chroma-mcp", "raw": stdout.decode()}, 500
            
    except Exception as e:
        logger.error(f"Error executing command: {str(e)}")
        return {"error": str(e), "status": "failed"}, 500

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "chroma-mcp-http-proxy"}

@app.post("/")
async def json_rpc_endpoint(request: Request):
    """JSON-RPC endpoint that forwards requests to the chroma-mcp service."""
    try:
        # Parse the request body
        try:
            body = await request.json()
            method = body.get("method", "unknown")
            params = body.get("params", {})
            req_id = body.get("id")
        except Exception as e:
            logger.error(f"Error parsing request: {str(e)}")
            return JSONResponse({
                "jsonrpc": "2.0",
                "error": {"code": -32700, "message": "Parse error: Invalid JSON"},
                "id": None
            })
        
        # Map the JSON-RPC method to a chroma-mcp command
        if method.startswith("chroma_"):
            # The method name matches chroma-mcp's command format
            cmd = method
        else:
            # Try to map the method name to a chroma-mcp command
            method_mapping = {
                "list_collections": "chroma_list_collections",
                "create_collection": "chroma_create_collection",
                "delete_collection": "chroma_delete_collection",
                "add_documents": "chroma_add_documents",
                "query_documents": "chroma_query_documents",
                "get_documents": "chroma_get_documents",
                # Add more mappings as needed
            }
            cmd = method_mapping.get(method)
            if cmd is None:
                return JSONResponse({
                    "jsonrpc": "2.0",
                    "error": {"code": -32601, "message": f"Method '{method}' not found"},
                    "id": req_id
                })
        
        # Forward the command to the chroma-mcp service
        try:
            result, status_code = await execute_command(cmd, params)
            
            if status_code != 200:
                return JSONResponse({
                    "jsonrpc": "2.0",
                    "error": {"code": -32603, "message": result.get("error", "Internal error")},
                    "id": req_id
                })
            
            return JSONResponse({
                "jsonrpc": "2.0",
                "result": result,
                "id": req_id
            })
            
        except Exception as e:
            logger.error(f"Error forwarding command: {str(e)}")
            return JSONResponse({
                "jsonrpc": "2.0",
                "error": {"code": -32603, "message": f"Internal error: {str(e)}"},
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
    logger.info(f"Starting Chroma MCP HTTP Proxy server on {HTTP_HOST}:{HTTP_PORT}")
    uvicorn.run(app, host=HTTP_HOST, port=HTTP_PORT)