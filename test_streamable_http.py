#!/usr/bin/env python3
"""
Minimal test of MCP Streamable HTTP Server
"""

import uvicorn
from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI(title="Test MCP Streamable HTTP Server")

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "message": "Test MCP server running"}

@app.post("/")
async def handle_mcp_request():
    """Handle MCP requests."""
    return JSONResponse({
        "jsonrpc": "2.0",
        "result": {
            "name": "chroma-mcp-test",
            "version": "0.1.0"
        },
        "id": 1
    })

@app.get("/")
async def handle_sse():
    """Handle SSE requests."""
    return {"message": "SSE endpoint placeholder"}

if __name__ == "__main__":
    print("Starting minimal test MCP server...")
    uvicorn.run(app, host="127.0.0.1", port=3003, log_level="info")