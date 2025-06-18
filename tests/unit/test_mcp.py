import json
import requests

def test_mcp_server():
    """Test the Chroma MCP server's JSON-RPC endpoint."""
    url = "http://localhost:10550"
    
    # Prepare a simple request to list collections
    payload = {
        "jsonrpc": "2.0",
        "method": "chroma_list_collections",
        "params": {},
        "id": 1
    }
    
    try:
        response = requests.post(url, json=payload)
        print(f"Status code: {response.status_code}")
        print(f"Response: {response.text}")
        return response.json()
    except Exception as e:
        print(f"Error connecting to MCP server: {e}")
        return None

if __name__ == "__main__":
    result = test_mcp_server()
    print(f"Result: {result}")