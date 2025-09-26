#!/usr/bin/env python3
"""
Test sequential thinking functionality after merge
"""

import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def test_sequential_thinking():
    print("Testing sequential thinking functionality...")

    server_params = StdioServerParameters(
        command="/home/bryan/run-chroma-mcp.sh",
        args=[]
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            try:
                # Test sequential thinking
                result = await session.call_tool(
                    "chroma_sequential_thinking",
                    {
                        "thought": "Testing that sequential thinking still works after fork feature merge",
                        "thought_number": 1,
                        "total_thoughts": 2,
                        "next_thought_needed": True
                    }
                )
                print("✅ Sequential thinking test 1 passed")
                print(f"Result: {result.content[0].text[:100]}...")

                # Test another thought
                result = await session.call_tool(
                    "chroma_sequential_thinking",
                    {
                        "thought": "Second thought to complete the sequence",
                        "thought_number": 2,
                        "total_thoughts": 2,
                        "next_thought_needed": False
                    }
                )
                print("✅ Sequential thinking test 2 passed")

                # Test get similar sessions
                result = await session.call_tool(
                    "chroma_get_similar_sessions",
                    {
                        "query_text": "testing",
                        "n_results": 1
                    }
                )
                print("✅ Get similar sessions test passed")

            except Exception as e:
                print(f"❌ Sequential thinking test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_sequential_thinking())