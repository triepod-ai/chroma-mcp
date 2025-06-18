"""HTTP Server implementation for Chroma MCP"""

import os
import json
import logging
import argparse
import asyncio
import sys
import threading
import traceback
from typing import Dict, List, Any, Optional, Callable, Union
import uvicorn
from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from pydantic import BaseModel
from starlette.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware

# Configure basic logging first
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure error handling for uncaught exceptions
def handle_exception(exc_type, exc_value, exc_traceback):
    """Handle uncaught exceptions."""
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    
    logger.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))

sys.excepthook = handle_exception

# Import all chroma tools from server
from .server import (
    chroma_list_collections,
    chroma_create_collection,
    chroma_peek_collection,
    chroma_get_collection_info,
    chroma_get_collection_count,
    chroma_modify_collection,
    chroma_delete_collection,
    chroma_add_documents,
    chroma_query_documents,
    chroma_get_documents,
    chroma_update_documents,
    chroma_delete_documents,
    chroma_sequential_thinking,
    chroma_get_similar_sessions,
    chroma_get_thought_history,
    chroma_get_thought_branches,
    chroma_continue_thought_chain,
    get_chroma_client  # Import function to get Chroma client
)

# Configure logging
logger = logging.getLogger("chroma-mcp-http")
log_dir = os.path.join(os.getcwd(), "logs")
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, "chroma-mcp-http.log")

handler = logging.FileHandler(log_file)
handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# Create FastAPI app
app = FastAPI(title="Chroma MCP HTTP Server")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# JSON-RPC request model
class JsonRpcRequest(BaseModel):
    jsonrpc: str = "2.0"
    method: str
    params: Optional[Dict[str, Any]] = {}
    id: Union[str, int, None] = None

# Tool method mapping
TOOL_METHODS = {
    "chroma_list_collections": chroma_list_collections,
    "chroma_create_collection": chroma_create_collection,
    "chroma_peek_collection": chroma_peek_collection,
    "chroma_get_collection_info": chroma_get_collection_info,
    "chroma_get_collection_count": chroma_get_collection_count,
    "chroma_modify_collection": chroma_modify_collection,
    "chroma_delete_collection": chroma_delete_collection,
    "chroma_add_documents": chroma_add_documents,
    "chroma_query_documents": chroma_query_documents,
    "chroma_get_documents": chroma_get_documents,
    "chroma_update_documents": chroma_update_documents,
    "chroma_delete_documents": chroma_delete_documents,
    "chroma_sequential_thinking": chroma_sequential_thinking,
    "chroma_get_similar_sessions": chroma_get_similar_sessions,
    "chroma_get_thought_history": chroma_get_thought_history,
    "chroma_get_thought_branches": chroma_get_thought_branches,
    "chroma_continue_thought_chain": chroma_continue_thought_chain,
}

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
        
        # Check if method exists
        if method not in TOOL_METHODS:
            logger.error(f"Method not found: {method}")
            return JSONResponse({
                "jsonrpc": "2.0",
                "error": {"code": -32601, "message": f"Method not found: {method}"},
                "id": req_id
            })
        
        # Get the tool function
        tool_fn = TOOL_METHODS[method]
        
        # Execute the tool function
        logger.info(f"Executing method: {method} with params: {params}")
        result = await tool_fn(**params)
        
        # Return the result
        return JSONResponse({
            "jsonrpc": "2.0",
            "result": result,
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

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        # Try to get Chroma client and list collections
        client = get_chroma_client()
        collections = client.list_collections()
        return {"status": "healthy", "collections_count": len(collections)}
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

def run_http_server(host: str = "0.0.0.0", port: int = 10550):
    """Run the HTTP server for Chroma MCP."""
    logger.info(f"Starting Chroma MCP HTTP server on {host}:{port}")
    uvicorn.run(app, host=host, port=port)

def run_in_thread(host: str = "0.0.0.0", port: int = 10550):
    """Run the HTTP server in a separate thread."""
    thread = threading.Thread(target=run_http_server, args=(host, port), daemon=True)
    thread.start()
    return thread

if __name__ == "__main__":
    # Initialize Chroma client
    get_chroma_client()
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Chroma MCP HTTP Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind server to")
    parser.add_argument("--port", type=int, default=10550, help="Port to bind server to")
    args = parser.parse_args()
    
    # Run the server
    run_http_server(args.host, args.port)