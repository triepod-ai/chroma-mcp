"""
Direct Chroma MCP Tools Example

This script shows how to use the Chroma MCP tools directly through the MCP interface.
It demonstrates basic operations without any additional abstractions.
"""

import asyncio
import json
import random
import time
import uuid
from datetime import datetime

def use_chroma_tool(tool_name, **kwargs):
    """
    Use a Chroma MCP tool directly.
    
    This is a simulated version for the demonstration. In a real application,
    this would make an actual call to the MCP server.
    """
    print(f"\n[Using Chroma MCP Tool: {tool_name}]")
    print(f"Arguments: {json.dumps(kwargs, indent=2)}")
    
    # In a real implementation, this would be:
    # result = client.call_tool("chroma-mcp", tool_name, kwargs)
    # return result
    
    # For demonstration, we'll simulate responses
    if tool_name == "chroma_create_collection":
        return {"status": "success", "message": f"Collection '{kwargs['collection_name']}' created"}
    
    elif tool_name == "chroma_add_documents":
        doc_count = len(kwargs.get("documents", []))
        return {"status": "success", "documents_added": doc_count}
    
    elif tool_name == "chroma_query_documents":
        # Simulate query results
        n_results = kwargs.get("n_results", 3)
        sample_results = {
            "ids": [["doc1", "doc2", "doc3"]],
            "documents": [[f"Sample document for query '{kwargs['query_texts'][0]}' - result {i}" 
                          for i in range(n_results)]],
            "distances": [[random.random() * 0.3 for _ in range(n_results)]]
        }
        return sample_results
    
    elif tool_name == "chroma_sequential_thinking":
        # Simulate sequential thinking result
        thought = kwargs.get("thought", "")
        number = kwargs.get("thoughtNumber", 0)
        session_id = kwargs.get("sessionId", str(uuid.uuid4())[:8])
        
        return {
            "sessionId": session_id,
            "thoughtNumber": number,
            "totalThoughts": kwargs.get("totalThoughts", 1),
            "nextThoughtNeeded": kwargs.get("nextThoughtNeeded", False),
            "persistedId": f"{session_id}_{number}"
        }
        
    return {"status": "success", "message": f"Tool {tool_name} executed"}

async def run_example():
    """Run the direct Chroma MCP tools example."""
    print("\n" + "=" * 80)
    print(" DIRECT CHROMA MCP TOOLS EXAMPLE ".center(80, "="))
    print("=" * 80 + "\n")
    
    timestamp = int(time.time())
    collection_name = f"example_collection_{timestamp}"
    session_id = f"example_session_{str(uuid.uuid4())[:8]}"
    
    print(f"Starting example at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Using collection: {collection_name}")
    print(f"Using session ID: {session_id}")
    
    # Example 1: Create a collection
    print("\n--- Creating a Collection ---")
    create_result = use_chroma_tool(
        "chroma_create_collection",
        collection_name=collection_name,
        hnsw_space="cosine"
    )
    print(f"Result: {json.dumps(create_result, indent=2)}")
    
    # Example 2: Add documents
    print("\n--- Adding Documents ---")
    programming_languages = [
        {
            "document": "Python is a high-level, interpreted programming language known for its readability and versatility. It emphasizes code readability with its notable use of significant whitespace.",
            "metadata": {"name": "Python", "paradigm": "multi-paradigm", "year": 1991}
        },
        {
            "document": "JavaScript is a high-level programming language that is one of the core technologies of the World Wide Web. It enables interactive web pages and is an essential part of web applications.",
            "metadata": {"name": "JavaScript", "paradigm": "multi-paradigm", "year": 1995}
        },
        {
            "document": "Rust is a multi-paradigm programming language designed for performance and safety, especially safe concurrency. Rust is syntactically similar to C++, but can guarantee memory safety.",
            "metadata": {"name": "Rust", "paradigm": "multi-paradigm", "year": 2010}
        },
        {
            "document": "Swift is a general-purpose, multi-paradigm, compiled programming language developed by Apple Inc. for iOS, iPadOS, macOS, watchOS, tvOS, and Linux.",
            "metadata": {"name": "Swift", "paradigm": "multi-paradigm", "year": 2014}
        },
        {
            "document": "Java is a high-level, class-based, object-oriented programming language that is designed to have as few implementation dependencies as possible.",
            "metadata": {"name": "Java", "paradigm": "object-oriented", "year": 1995}
        }
    ]
    
    documents = [lang["document"] for lang in programming_languages]
    metadatas = [lang["metadata"] for lang in programming_languages]
    
    add_result = use_chroma_tool(
        "chroma_add_documents",
        collection_name=collection_name,
        documents=documents,
        metadatas=metadatas
    )
    print(f"Result: {json.dumps(add_result, indent=2)}")
    
    # Example 3: Query documents
    print("\n--- Querying Documents ---")
    print("Query 1: Programming languages focused on safety")
    query_result = use_chroma_tool(
        "chroma_query_documents",
        collection_name=collection_name,
        query_texts=["programming language safety concurrency"],
        n_results=2
    )
    print(f"Result: {json.dumps(query_result, indent=2)}")
    
    print("\nQuery 2: Modern web programming languages")
    query_result2 = use_chroma_tool(
        "chroma_query_documents",
        collection_name=collection_name,
        query_texts=["web development modern"],
        n_results=2
    )
    print(f"Result: {json.dumps(query_result2, indent=2)}")
    
    # Example 4: Filtered query
    print("\n--- Filtered Query ---")
    filtered_query_result = use_chroma_tool(
        "chroma_query_documents",
        collection_name=collection_name,
        query_texts=["programming language"],
        where={"year": {"$gte": 2010}},  # Languages from 2010 or later
        n_results=2
    )
    print(f"Result (languages from 2010 or later): {json.dumps(filtered_query_result, indent=2)}")
    
    # Example 5: Sequential thinking for analysis
    print("\n--- Sequential Thinking for Analysis ---")
    
    # First thought
    thought1 = """
    I'm analyzing a collection of programming language descriptions to identify key trends and characteristics.
    
    Initial observations:
    1. The collection includes both older (Java, JavaScript, Python) and newer languages (Rust, Swift)
    2. Most are multi-paradigm languages, suggesting flexibility is valued
    3. There's a mix of interpreted and compiled languages
    
    I'll analyze further to identify key differentiating features and use cases.
    """
    
    thought1_result = use_chroma_tool(
        "chroma_sequential_thinking",
        thought=thought1,
        thoughtNumber=1,
        totalThoughts=3,
        nextThoughtNeeded=True,
        sessionId=session_id
    )
    print(f"Thought 1 Result: {json.dumps(thought1_result, indent=2)}")
    
    # Second thought
    thought2 = """
    Looking deeper at the language characteristics:
    
    Safety vs. Performance trade-offs:
    - Rust emphasizes memory safety without sacrificing performance
    - Swift offers safety features while maintaining good performance
    - Python prioritizes readability and development speed over raw performance
    
    Evolution of programming paradigms:
    - Trend toward multi-paradigm approaches (mixing OOP, functional, procedural)
    - Strong typing making a comeback in newer languages (TypeScript, Swift)
    - Concurrency as a first-class concern in modern languages (Rust, Swift)
    
    Let me continue analyzing application domains and ecosystem factors.
    """
    
    thought2_result = use_chroma_tool(
        "chroma_sequential_thinking",
        thought=thought2,
        thoughtNumber=2,
        totalThoughts=3,
        nextThoughtNeeded=True,
        sessionId=session_id
    )
    print(f"Thought 2 Result: {json.dumps(thought2_result, indent=2)}")
    
    # Final thought
    thought3 = """
    Final analysis of programming language trends from the collection:
    
    1. Language Design Evolution:
       - Modern languages (post-2010) emphasize both safety and performance
       - Older languages focus more on specific domains or paradigms
       - Multi-paradigm approach dominates recent language design
    
    2. Key Differentiators:
       - Memory management approach (manual, GC, ownership models)
       - Type system (dynamic, static, inference capabilities)
       - Concurrency model (threads, async/await, actors)
    
    3. Industry Applications:
       - System programming: Rust excels due to safety without GC
       - Web development: JavaScript dominates, with TypeScript adding safety
       - Mobile: Swift for Apple ecosystem, Java for Android
       - Data science: Python's ecosystem makes it the leader
    
    This analysis shows how programming languages are evolving to balance 
    developer productivity, performance needs, and safety considerations.
    """
    
    thought3_result = use_chroma_tool(
        "chroma_sequential_thinking",
        thought=thought3,
        thoughtNumber=3,
        totalThoughts=3,
        nextThoughtNeeded=False,
        sessionId=session_id,
        sessionSummary="Analysis of programming language evolution trends, focusing on the balance between safety, performance, and developer productivity across different application domains.",
        keyThoughts=[1, 3]
    )
    print(f"Thought 3 Result: {json.dumps(thought3_result, indent=2)}")
    
    print("\n" + "=" * 80)
    print(" EXAMPLE COMPLETED ".center(80, "="))
    print("=" * 80 + "\n")

if __name__ == "__main__":
    asyncio.run(run_example())
