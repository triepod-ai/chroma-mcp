"""Test script for the Chroma MCP HTTP server."""

import uvicorn
from fastapi import FastAPI, Request
from starlette.responses import JSONResponse

# Create FastAPI app
app = FastAPI(title="Chroma MCP Test Server")

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

@app.post("/")
async def json_rpc_endpoint(request: Request):
    """Handle JSON-RPC requests."""
    try:
        # Parse the request body
        body = await request.json()
        return JSONResponse({
            "jsonrpc": "2.0",
            "result": {
                "echo": body,
                "message": "Test server is working"
            },
            "id": body.get("id")
        })
    except Exception as e:
        return JSONResponse({
            "jsonrpc": "2.0",
            "error": {"code": -32603, "message": f"Internal error: {str(e)}"},
            "id": None
        })

if __name__ == "__main__":
    print("Starting test HTTP server on 0.0.0.0:8080")
    uvicorn.run(app, host="0.0.0.0", port=8080)