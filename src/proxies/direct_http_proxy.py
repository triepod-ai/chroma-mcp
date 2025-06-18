"""Direct HTTP Proxy Server for Chroma MCP (no Docker dependency)"""

import os
import json
import logging
import asyncio
import uvicorn
from fastapi import FastAPI, Request
from starlette.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("chroma-mcp-direct-http-proxy")

# Get environment variables
HTTP_HOST = os.environ.get("HTTP_HOST", "0.0.0.0")
HTTP_PORT = int(os.environ.get("HTTP_PORT", 10550))
MCP_EXECUTABLE = os.environ.get("MCP_EXECUTABLE", "mcp")

# Create FastAPI app
app = FastAPI(title="Chroma MCP Direct HTTP Proxy")

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
    return {"status": "healthy", "service": "chroma-mcp-direct-http-proxy"}

@app.post("/")
async def json_rpc_endpoint(request: Request):
    """JSON-RPC endpoint that directly calls the mcp executable."""
    try:
        # Parse the request body
        try:
            body = await request.json()
            method = body.get("method", "unknown")
            params = body.get("params", {})
            req_id = body.get("id")
            
            if not method.startswith("chroma_"):
                # Try to map the method name
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
        except Exception as e:
            logger.error(f"Error parsing request: {str(e)}")
            return JSONResponse({
                "jsonrpc": "2.0",
                "error": {"code": -32700, "message": "Parse error: Invalid JSON"},
                "id": None
            })
        
        # Execute the command using the MCP executable
        try:
            # Call mcp with the method
            process = await asyncio.create_subprocess_exec(
                MCP_EXECUTABLE, "chroma", method,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # Prepare and send input params if any
            if params:
                input_data = json.dumps(params).encode()
                stdout, stderr = await process.communicate(input_data)
            else:
                stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                error_message = stderr.decode() if stderr else "Unknown error"
                logger.error(f"Error executing command: {error_message}")
                return JSONResponse({
                    "jsonrpc": "2.0",
                    "error": {"code": -32603, "message": f"Internal error: {error_message}"},
                    "id": req_id
                })
            
            # Parse the response as JSON
            try:
                result = json.loads(stdout.decode())
                return JSONResponse({
                    "jsonrpc": "2.0",
                    "result": result,
                    "id": req_id
                })
            except json.JSONDecodeError:
                logger.error(f"Error parsing response: {stdout.decode()}")
                return JSONResponse({
                    "jsonrpc": "2.0",
                    "error": {"code": -32603, "message": "Internal error: Invalid JSON in response"},
                    "id": req_id
                })
                
        except Exception as e:
            logger.error(f"Error executing command: {str(e)}")
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
    logger.info(f"Starting Chroma MCP Direct HTTP Proxy on {HTTP_HOST}:{HTTP_PORT}")
    uvicorn.run(app, host=HTTP_HOST, port=HTTP_PORT)