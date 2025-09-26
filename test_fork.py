#!/usr/bin/env python3
"""
Test the new chroma_fork_collection functionality
"""

import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def test_fork_functionality():
    print("Testing fork functionality...")

    # Connect to MCP server via container
    server_params = StdioServerParameters(
        command="/home/bryan/run-chroma-mcp.sh",
        args=[]
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize the connection
            await session.initialize()

            # List available tools
            tools = await session.list_tools()
            tool_names = [tool.name for tool in tools.tools]
            print(f"Available tools: {tool_names}")

            # Check if fork tool is available
            if "chroma_fork_collection" in tool_names:
                print("✅ chroma_fork_collection tool is available!")

                # Try to create a test collection first
                try:
                    result = await session.call_tool("chroma_list_collections")
                    print(f"Collections list: {result.content[0].text}")

                    # Create a test collection if none exist
                    result = await session.call_tool(
                        "chroma_create_collection",
                        {"collection_name": "test_collection"}
                    )
                    print(f"Create collection result: {result.content[0].text}")

                    # Test fork functionality
                    result = await session.call_tool(
                        "chroma_fork_collection",
                        {
                            "collection_name": "test_collection",
                            "new_collection_name": "test_collection_fork"
                        }
                    )
                    print(f"Fork result: {result.content[0].text}")

                    # Verify fork worked
                    result = await session.call_tool("chroma_list_collections")
                    print(f"Collections after fork: {result.content[0].text}")

                except Exception as e:
                    print(f"Error testing fork: {e}")

            else:
                print("❌ chroma_fork_collection tool not found!")

            # Check regex support in query documentation
            for tool in tools.tools:
                if tool.name == "chroma_query_documents":
                    if "$regex" in str(tool.description):
                        print("✅ Regex support documentation found in query tools!")
                    else:
                        print("❌ Regex documentation not found")

if __name__ == "__main__":
    asyncio.run(test_fork_functionality())