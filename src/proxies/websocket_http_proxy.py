"""WebSocket-based HTTP Proxy Server for Chroma MCP"""

import os
import json
import logging
import asyncio
import httpx
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from starlette.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware
import uvicorn
import socket
import subprocess
import time

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

def parse_jsonrpc_message(message):
    """Parse a JSON-RPC message from string."""
    try:
        data = json.loads(message)
        
        # Check if this is a valid JSON-RPC 2.0 message
        if "jsonrpc" not in data or data.get("jsonrpc") != "2.0":
            return None
            
        return data
    except Exception:
        return None

def is_chroma_mcp_available():
    """Check if chroma-mcp is available."""
    try:
        # Try to ping the container
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex((CHROMA_MCP_HOST, 22))  # Try SSH port for connection check
        sock.close()
        
        if result == 0:
            logger.info("chroma-mcp container is reachable")
            return True
        else:
            logger.warning(f"chroma-mcp container is not reachable (code: {result})")
            return False
    except Exception as e:
        logger.error(f"Error checking chroma-mcp availability: {str(e)}")
        return False

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    chroma_available = is_chroma_mcp_available()
    
    return {
        "status": "healthy", 
        "service": "chroma-mcp-http-proxy",
        "chroma_mcp_available": chroma_available
    }

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
        
        # Ensure this is a valid chroma method
        if not method.startswith("chroma_"):
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
            method = method_mapping.get(method, method)
            
            if not method.startswith("chroma_"):
                return JSONResponse({
                    "jsonrpc": "2.0",
                    "error": {"code": -32601, "message": f"Method '{method}' not found or not supported"},
                    "id": req_id
                })
        
        # Create the JSON-RPC request to forward
        jsonrpc_request = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": req_id
        }
        
        # Execute the command through the chroma-mcp container using direct exec
        try:
            # Use Docker exec to send the JSON-RPC request to the container
            process = await asyncio.create_subprocess_exec(
                "docker", "exec", "chroma-mcp", "python", "-c",
                f'''
import json
import subprocess
import sys

request = {json.dumps(jsonrpc_request)}
cmd = ["mcp", "chroma", request["method"]]
input_data = json.dumps(request["params"]).encode() if request["params"] else None

process = subprocess.Popen(
    cmd,
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE
)

stdout, stderr = process.communicate(input=input_data)

if process.returncode != 0:
    result = {{"error": stderr.decode(), "status": "failed"}}
else:
    try:
        result = json.loads(stdout.decode())
    except json.JSONDecodeError:
        result = {{"error": "Failed to parse response", "raw": stdout.decode()}}

response = {{
    "jsonrpc": "2.0",
    "result": result,
    "id": request["id"]
}}

print(json.dumps(response))
                ''',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                error_message = stderr.decode() if stderr else "Unknown error"
                logger.error(f"Error executing command: {error_message}")
                return JSONResponse({
                    "jsonrpc": "2.0",
                    "error": {"code": -32603, "message": f"Internal error: {error_message}"},
                    "id": req_id
                })
            
            response = json.loads(stdout.decode())
            return JSONResponse(response)
            
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
    # Wait for chroma-mcp container to be available
    retries = 0
    max_retries = 10
    while not is_chroma_mcp_available() and retries < max_retries:
        logger.info(f"Waiting for chroma-mcp container to be available (attempt {retries+1}/{max_retries})...")
        time.sleep(3)
        retries += 1
    
    if retries >= max_retries:
        logger.warning("chroma-mcp container not available after multiple attempts, starting anyway")
    
    logger.info(f"Starting Chroma MCP HTTP Proxy server on {HTTP_HOST}:{HTTP_PORT}")
    uvicorn.run(app, host=HTTP_HOST, port=HTTP_PORT)