"""
MCP-compliant Streamable HTTP Server for Chroma MCP
Implements the Model Context Protocol Streamable HTTP transport specification

⚠️  DEPRECATED: This custom implementation is deprecated as of 2025-10-03
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

MIGRATION NOTICE:
This file is deprecated in favor of FastMCP's built-in streamable HTTP transport.

REASON FOR DEPRECATION:
- Custom implementation used placeholder tool schemas with empty properties
- MCP Inspector rejected tools without proper parameter definitions
- FastMCP automatically generates complete schemas from Pydantic annotations

NEW IMPLEMENTATION:
Use server.py with --transport flag:
    python3 -m chroma_mcp.server --transport streamable-http \
                                  --http-host 0.0.0.0 \
                                  --http-port 10550

See src/chroma_mcp/server.py:1196-1264 for the new implementation.

DOCKER USAGE:
The docker-compose.yaml has been updated to use the new implementation.
See docker-compose.yaml:80 for the updated command.

This file is retained for reference but should not be used in production.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import os
import json
import logging
import asyncio
import uuid
from typing import Dict, List, Any, Optional, Union, AsyncGenerator
from urllib.parse import urlparse

import uvicorn
from fastapi import FastAPI, Request, HTTPException, Header
from fastapi.responses import Response, StreamingResponse
from pydantic import BaseModel
import httpx

from chroma_mcp.server_original import (
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
    get_chroma_client
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Session storage for streamable HTTP
sessions: Dict[str, Dict] = {}

class JsonRpcRequest(BaseModel):
    jsonrpc: str = "2.0"
    method: str
    params: Optional[Dict[str, Any]] = None
    id: Union[str, int, None] = None

class JsonRpcResponse(BaseModel):
    jsonrpc: str = "2.0"
    result: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None
    id: Union[str, int, None] = None

# MCP tool method mapping
MCP_TOOLS = {
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

# MCP server capabilities
SERVER_INFO = {
    "name": "chroma-mcp",
    "version": "0.3.0",
    "capabilities": {
        "tools": {
            "listChanged": True
        },
        "resources": {
            "subscribe": True,
            "listChanged": True
        },
        "prompts": {
            "listChanged": True
        },
        "logging": {}
    },
    "protocolVersion": "2025-03-26"
}

def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Chroma MCP Streamable HTTP Server",
        description="MCP-compliant streamable HTTP server for ChromaDB operations",
        version="0.3.0"
    )

    def validate_origin(origin: Optional[str], host: str) -> bool:
        """Validate Origin header to prevent DNS rebinding attacks."""
        if not origin:
            return True  # Allow requests without Origin header for now

        try:
            origin_parsed = urlparse(origin)
            # Allow localhost and same host
            if origin_parsed.hostname in ['localhost', '127.0.0.1', host]:
                return True
            # For development, allow all origins (should be restricted in production)
            return True
        except Exception:
            return False

    @app.middleware("http")
    async def security_middleware(request: Request, call_next):
        """Security middleware for origin validation."""
        origin = request.headers.get("origin")
        host = request.headers.get("host", "localhost")

        if not validate_origin(origin, host.split(':')[0]):
            return Response(
                content="Origin not allowed",
                status_code=403,
                headers={"Content-Type": "text/plain"}
            )

        response = await call_next(request)

        # Add CORS headers for development
        if origin:
            response.headers["Access-Control-Allow-Origin"] = origin
        else:
            response.headers["Access-Control-Allow-Origin"] = "*"

        response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, Mcp-Session-Id, Accept"

        return response

    @app.options("/")
    async def handle_preflight():
        """Handle CORS preflight requests."""
        return Response(
            status_code=200,
            headers={
                "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, Authorization, Mcp-Session-Id, Accept",
            }
        )

    @app.post("/")
    async def handle_post_request(
        request: Request,
        mcp_session_id: Optional[str] = Header(None, alias="Mcp-Session-Id")
    ):
        """Handle POST requests (client-to-server) in MCP Streamable HTTP."""
        try:
            # Parse JSON-RPC request
            body = await request.json()
            logger.info(f"POST request body: {body}")

            # Handle single request or batch
            if isinstance(body, list):
                # Batch request
                responses = []
                for req in body:
                    response = await process_jsonrpc_request(req, mcp_session_id)
                    if response:  # Only add non-None responses
                        responses.append(response)
                return responses
            else:
                # Single request
                response = await process_jsonrpc_request(body, mcp_session_id)
                if response is None:
                    return Response(status_code=202)  # Notification, no response
                return response

        except json.JSONDecodeError:
            return JsonRpcResponse(
                error={"code": -32700, "message": "Parse error"},
                id=None
            ).dict(exclude_none=True)
        except Exception as e:
            logger.error(f"Error in POST request: {str(e)}")
            return JsonRpcResponse(
                error={"code": -32603, "message": f"Internal error: {str(e)}"},
                id=None
            ).dict(exclude_none=True)

    async def process_jsonrpc_request(
        body: Dict[str, Any],
        session_id: Optional[str]
    ) -> Optional[Dict[str, Any]]:
        """Process a single JSON-RPC request."""
        # Extract request fields
        jsonrpc = body.get("jsonrpc")
        method = body.get("method")
        params = body.get("params", {})
        req_id = body.get("id")

        # Log the request for debugging
        logger.info(f"MCP Request: method={method}, id={req_id}, session={session_id}")

        # Validate JSON-RPC version
        if jsonrpc != "2.0":
            return JsonRpcResponse(
                error={"code": -32600, "message": "Invalid Request"},
                id=req_id
            ).dict(exclude_none=True)

        # Handle MCP protocol methods
        if method == "initialize":
            return await handle_initialize(params, req_id, session_id)
        elif method == "tools/list":
            return await handle_tools_list(req_id)
        elif method == "tools/call":
            return await handle_tool_call(params, req_id)
        elif method == "notifications/initialized":
            # Notification - no response needed
            return None
        else:
            return JsonRpcResponse(
                error={"code": -32601, "message": f"Method not found: {method}"},
                id=req_id
            ).dict(exclude_none=True)

    async def handle_initialize(
        params: Dict[str, Any],
        req_id: Union[str, int, None],
        session_id: Optional[str]
    ) -> Dict[str, Any]:
        """Handle MCP initialize request."""
        # Create or use existing session
        if not session_id:
            session_id = str(uuid.uuid4())

        sessions[session_id] = {
            "client_info": params,
            "initialized": True,
            "created_at": asyncio.get_event_loop().time()
        }

        return JsonRpcResponse(
            result=SERVER_INFO,
            id=req_id
        ).dict(exclude_none=True)

    async def handle_tools_list(req_id: Union[str, int, None]) -> Dict[str, Any]:
        """Handle tools/list request."""
        tools = []
        for tool_name in MCP_TOOLS:
            # Create tool schema based on the tool name
            tools.append({
                "name": tool_name,
                "description": f"ChromaDB {tool_name.replace('chroma_', '').replace('_', ' ')} operation",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "additionalProperties": True
                }
            })

        return JsonRpcResponse(
            result={"tools": tools},
            id=req_id
        ).dict(exclude_none=True)

    async def handle_tool_call(
        params: Dict[str, Any],
        req_id: Union[str, int, None]
    ) -> Dict[str, Any]:
        """Handle tools/call request."""
        tool_name = params.get("name")
        arguments = params.get("arguments", {})

        if tool_name not in MCP_TOOLS:
            return JsonRpcResponse(
                error={"code": -32601, "message": f"Tool not found: {tool_name}"},
                id=req_id
            ).dict(exclude_none=True)

        try:
            # Execute the tool
            tool_fn = MCP_TOOLS[tool_name]
            result = await tool_fn(**arguments)

            return JsonRpcResponse(
                result={
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(result, indent=2) if isinstance(result, (dict, list)) else str(result)
                        }
                    ]
                },
                id=req_id
            ).dict(exclude_none=True)

        except Exception as e:
            logger.error(f"Tool execution error for {tool_name}: {str(e)}")
            return JsonRpcResponse(
                error={"code": -32603, "message": f"Tool execution failed: {str(e)}"},
                id=req_id
            ).dict(exclude_none=True)

    @app.get("/")
    async def handle_get_request(
        mcp_session_id: Optional[str] = Header(None, alias="Mcp-Session-Id")
    ):
        """Handle GET requests (server-to-client SSE stream) in MCP Streamable HTTP."""
        logger.info(f"GET/SSE request - session_id: {mcp_session_id}")
        async def event_stream():
            """Generate Server-Sent Events stream."""
            try:
                # Send initial connection event
                yield f"data: {json.dumps({'type': 'connected', 'session_id': mcp_session_id})}\n\n"

                # Keep connection alive with periodic heartbeat
                while True:
                    await asyncio.sleep(30)  # 30-second heartbeat
                    yield f"data: {json.dumps({'type': 'heartbeat', 'timestamp': asyncio.get_event_loop().time()})}\n\n"

            except asyncio.CancelledError:
                logger.info("SSE stream cancelled")
                raise
            except Exception as e:
                logger.error(f"Error in SSE stream: {str(e)}")
                yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

        return StreamingResponse(
            event_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type, Authorization, Mcp-Session-Id",
            }
        )

    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        try:
            client = get_chroma_client()
            collections = client.list_collections()
            return {
                "status": "healthy",
                "collections_count": len(collections),
                "sessions_count": len(sessions),
                "server_info": SERVER_INFO
            }
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

    return app

def run_server(host: str = "127.0.0.1", port: int = 3000):
    """
    Run the MCP Streamable HTTP server.

    ⚠️  DEPRECATED: Use server.py with --transport streamable-http instead.

    This function is deprecated. Please use:
        python3 -m chroma_mcp.server --transport streamable-http --http-host <host> --http-port <port>

    See file docstring for full deprecation details.
    """
    logger.warning("=" * 80)
    logger.warning("⚠️  DEPRECATION WARNING")
    logger.warning("This custom streamable HTTP server is deprecated.")
    logger.warning("Please use: python3 -m chroma_mcp.server --transport streamable-http")
    logger.warning("See file docstring for migration details.")
    logger.warning("=" * 80)

    # Initialize Chroma client
    get_chroma_client()

    app = create_app()

    logger.info(f"Starting Chroma MCP Streamable HTTP server on {host}:{port}")
    logger.info("Server implements MCP Streamable HTTP transport specification")
    logger.info(f"Health check available at: http://{host}:{port}/health")

    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info",
        access_log=True
    )

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Chroma MCP Streamable HTTP Server")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=3000, help="Port to bind to")
    args = parser.parse_args()

    run_server(args.host, args.port)