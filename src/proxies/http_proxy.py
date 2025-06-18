"""HTTP Proxy Server for Chroma MCP"""

import os
import json
import logging
import sys
import traceback
import uvicorn
from fastapi import FastAPI, Request, HTTPException
from starlette.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("chroma-mcp-http-proxy")

# Configure error handling for uncaught exceptions
def handle_exception(exc_type, exc_value, exc_traceback):
    """Handle uncaught exceptions."""
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    
    logger.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))

sys.excepthook = handle_exception

# Create FastAPI app
app = FastAPI(title="Chroma MCP HTTP Proxy")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from fastmcp import Client

# Client for the MCP server
mcp_client = None

async def get_mcp_client():
    """Get or create MCP client."""
    global mcp_client
    if mcp_client is None:
        mcp_host = os.environ.get("CHROMA_MCP_HOST", "chroma-mcp")
        logger.info(f"Connecting to MCP server at {mcp_host}")
        mcp_client = Client(mcp_host)
    return mcp_client

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "chroma-mcp-http-proxy"}

@app.post("/")
async def json_rpc_endpoint(request: Request):
    """Handle JSON-RPC requests for Chroma MCP tools."""
    try:
        # Parse the request body
        try:
            body = await request.json()
            jsonrpc = body.get("jsonrpc")
            method = body.get("method")
            params = body.get("params", {})
            req_id = body.get("id")
        except Exception as e:
            logger.error(f"Error parsing request: {str(e)}")
            return JSONResponse({
                "jsonrpc": "2.0",
                "error": {"code": -32700, "message": "Parse error: Invalid JSON"},
                "id": None
            })
        
        # Validate JSON-RPC version
        if jsonrpc != "2.0":
            return JSONResponse({
                "jsonrpc": "2.0",
                "error": {"code": -32600, "message": "Invalid Request: Expected JSON-RPC 2.0"},
                "id": req_id
            })
        
        # Connect to MCP client
        client = await get_mcp_client()
        
        # Call the tool via MCP client
        try:
            async with client:
                tools = await client.list_tools()
                if method not in [t for t in tools]:
                    logger.error(f"Method not found: {method}")
                    return JSONResponse({
                        "jsonrpc": "2.0",
                        "error": {"code": -32601, "message": f"Method not found: {method}"},
                        "id": req_id
                    })
                
                logger.info(f"Calling tool: {method} with params: {params}")
                result = await client.call_tool(method, params)
                if result and len(result) > 0:
                    tool_result = result[0].text
                    try:
                        # Try to parse as JSON
                        json_result = json.loads(tool_result)
                        return JSONResponse({
                            "jsonrpc": "2.0",
                            "result": json_result,
                            "id": req_id
                        })
                    except:
                        # Return as text
                        return JSONResponse({
                            "jsonrpc": "2.0",
                            "result": tool_result,
                            "id": req_id
                        })
                else:
                    return JSONResponse({
                        "jsonrpc": "2.0",
                        "result": None,
                        "id": req_id
                    })
        except Exception as e:
            logger.error(f"Error calling tool {method}: {str(e)}")
            logger.error(traceback.format_exc())
            return JSONResponse({
                "jsonrpc": "2.0",
                "error": {"code": -32603, "message": f"MCP client error: {str(e)}"},
                "id": req_id
            })
    
    except Exception as e:
        # Log the error
        logger.error(f"Error in JSON-RPC request: {str(e)}")
        logger.error(traceback.format_exc())
        
        # Return error response
        return JSONResponse({
            "jsonrpc": "2.0",
            "error": {"code": -32603, "message": f"Internal error: {str(e)}"},
            "id": None
        })

@app.get("/tools")
async def list_tools():
    """List available tools."""
    try:
        client = await get_mcp_client()
        async with client:
            tools = await client.list_tools()
            return {"tools": tools}
    except Exception as e:
        logger.error(f"Error listing tools: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    port = int(os.environ.get("HTTP_PORT", 10550))
    host = os.environ.get("HTTP_HOST", "0.0.0.0")
    
    print(f"Starting HTTP proxy server on {host}:{port}")
    uvicorn.run(app, host=host, port=port)