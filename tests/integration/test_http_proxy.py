#!/usr/bin/env python3
"""Test script for the Chroma MCP HTTP proxy"""

import requests
import json
import argparse
import sys

def test_health_endpoint(host="localhost", port=10550):
    """Test the health endpoint of the HTTP proxy."""
    url = f"http://{host}:{port}/health"
    try:
        response = requests.get(url)
        print(f"Health endpoint status code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error testing health endpoint: {str(e)}")
        return False

def test_jsonrpc_endpoint(host="localhost", port=10550, method="chroma_list_collections"):
    """Test the JSON-RPC endpoint of the HTTP proxy."""
    url = f"http://{host}:{port}/"
    
    # Create a JSON-RPC request
    jsonrpc_request = {
        "jsonrpc": "2.0",
        "method": method,
        "params": {},
        "id": 1
    }
    
    try:
        response = requests.post(
            url, 
            json=jsonrpc_request,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"JSON-RPC endpoint status code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        return response.status_code == 200 and "result" in response.json()
    except Exception as e:
        print(f"Error testing JSON-RPC endpoint: {str(e)}")
        return False

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Test the Chroma MCP HTTP proxy")
    parser.add_argument("--host", default="localhost", help="Proxy host")
    parser.add_argument("--port", type=int, default=10550, help="Proxy port")
    parser.add_argument("--method", default="chroma_list_collections", help="JSON-RPC method to test")
    parser.add_argument("--health-only", action="store_true", help="Only test the health endpoint")
    
    args = parser.parse_args()
    
    # Test the health endpoint
    print("Testing health endpoint...")
    health_ok = test_health_endpoint(args.host, args.port)
    
    if not health_ok:
        print("Health endpoint test failed!")
        sys.exit(1)
    
    # Test the JSON-RPC endpoint if requested
    if not args.health_only:
        print("\nTesting JSON-RPC endpoint...")
        jsonrpc_ok = test_jsonrpc_endpoint(args.host, args.port, args.method)
        
        if not jsonrpc_ok:
            print("JSON-RPC endpoint test failed!")
            sys.exit(1)
    
    print("\nAll tests passed!")
    sys.exit(0)

if __name__ == "__main__":
    main()