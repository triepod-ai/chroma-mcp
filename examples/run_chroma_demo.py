"""
Demo script to demonstrate Chroma MCP functionality using MCP tools.
This script shows how to use the Chroma MCP server for collection management,
document operations, and sequential thinking.
"""

import time
import json
from datetime import datetime
import uuid
import asyncio
import sys

# Wrapper functions for Chroma MCP tools using MCP protocol
def use_chroma_tool(tool_name, **kwargs):
    """Use the MCP Chroma tool with the given name and arguments."""
    import json
    from subprocess import run, PIPE
    
    # Format the command to call the MCP tool via Claude
    cmd = [
        "python", "-c",
        f"""
import json
from mcp.client import Client
from mcp.client.stdio import connect_to_stdio

async def main():
    client = await connect_to_stdio()
    
    try:
        result = await client.call_tool(
            "chroma-mcp",
            "{tool_name}",
            {json.dumps(kwargs)}
        )
        print(json.dumps(result))
    except Exception as e:
        print(json.dumps({{"error": str(e)}}))
    finally:
        await client.close()

import asyncio
asyncio.run(main())
        """
    ]
    
    # Run the command and capture the output
    result = run(cmd, stdout=PIPE, stderr=PIPE, text=True)
    
    # Parse the JSON output
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        print(f"Error: {result.stderr}")
        return {"error": "Failed to parse response", "stdout": result.stdout, "stderr": result.stderr}

def chroma_list_collections(limit=None, offset=None):
    """List all collection names in the Chroma database."""
    return use_chroma_tool("chroma_list_collections", limit=limit, offset=offset)

def chroma_create_collection(collection_name, **kwargs):
    """Create a new Chroma collection."""
    return use_chroma_tool("chroma_create_collection", collection_name=collection_name, **kwargs)

def chroma_peek_collection(collection_name, limit=5):
    """Peek at documents in a Chroma collection."""
    return use_chroma_tool("chroma_peek_collection", collection_name=collection_name, limit=limit)

def chroma_get_collection_info(collection_name):
    """Get information about a Chroma collection."""
    return use_chroma_tool("chroma_get_collection_info", collection_name=collection_name)

def chroma_get_collection_count(collection_name):
    """Get the number of documents in a Chroma collection."""
    return use_chroma_tool("chroma_get_collection_count", collection_name=collection_name)

def chroma_delete_collection(collection_name):
    """Delete a Chroma collection."""
    return use_chroma_tool("chroma_delete_collection", collection_name=collection_name)

def chroma_add_documents(collection_name, documents, metadatas=None, ids=None):
    """Add documents to a Chroma collection."""
    return use_chroma_tool("chroma_add_documents", collection_name=collection_name, 
                          documents=documents, metadatas=metadatas, ids=ids)

def chroma_query_documents(collection_name, query_texts, n_results=5, where=None, where_document=None, include=None):
    """Query documents from a Chroma collection with advanced filtering."""
    return use_chroma_tool("chroma_query_documents", collection_name=collection_name,
                          query_texts=query_texts, n_results=n_results, 
                          where=where, where_document=where_document, include=include)

def chroma_get_documents(collection_name, ids=None, where=None, where_document=None, include=None, limit=None, offset=None):
    """Get documents from a Chroma collection with optional filtering."""
    return use_chroma_tool("chroma_get_documents", collection_name=collection_name,
                          ids=ids, where=where, where_document=where_document,
                          include=include, limit=limit, offset=offset)

def chroma_sequential_thinking(thought, thoughtNumber, totalThoughts, nextThoughtNeeded,
                               sessionId=None, isRevision=None, revisesThought=None,
                               branchFromThought=None, branchId=None, needsMoreThoughts=None,
                               sessionSummary=None, keyThoughts=None, persist=True):
    """Use the sequential thinking tool for problem-solving."""
    return use_chroma_tool("chroma_sequential_thinking", 
                          thought=thought, thoughtNumber=thoughtNumber,
                          totalThoughts=totalThoughts, nextThoughtNeeded=nextThoughtNeeded,
                          sessionId=sessionId, isRevision=isRevision, revisesThought=revisesThought,
                          branchFromThought=branchFromThought, branchId=branchId,
                          needsMoreThoughts=needsMoreThoughts, sessionSummary=sessionSummary,
                          keyThoughts=keyThoughts, persist=persist)

def chroma_get_thought_history(sessionId):
    """Retrieve the thought history for a specific session."""
    return use_chroma_tool("chroma_get_thought_history", sessionId=sessionId)

def print_section(title):
    """Print a section header."""
    print("\n" + "=" * 80)
    print(f" {title} ".center(80, "="))
    print("=" * 80 + "\n")

def print_result(title, result):
    """Print a result with a title."""
    print(f"\n--- {title} ---")
    if isinstance(result, dict) or isinstance(result, list):
        print(json.dumps(result, indent=2))
    else:
        print(result)
    print()

def run_chroma_demo():
    """Run a demonstration of Chroma MCP functionality."""
    # Generate unique IDs for this run to avoid collisions
    current_time = int(time.time())
    collection_name = f"demo_collection_{current_time}"
    session_id = f"demo_session_{str(uuid.uuid4())[:8]}"
    
    print_section("CHROMA MCP DEMO")
    print(f"Demo running at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Using collection: {collection_name}")
    print(f"Using session ID: {session_id}")
    
    try:
        # PART 1: Collection Management
        print_section("COLLECTION MANAGEMENT")
        
        # Create a new collection
        print("Creating a new collection...")
        result = chroma_create_collection(
            collection_name=collection_name,
            hnsw_space="cosine",  # Use cosine similarity for vector search
            hnsw_construction_ef=100  # Increase construction quality
        )
        print_result("Collection Creation Result", result)
        
        # List all collections
        print("Listing all collections...")
        collections = chroma_list_collections()
        print_result("All Collections", collections)
        
        # PART 2: Document Operations
        print_section("DOCUMENT OPERATIONS")
        
        # Sample documents about different programming languages
        documents = [
            "Python is a high-level, interpreted programming language known for its readability and versatility.",
            "JavaScript is a scripting language that enables interactive web pages and is an essential part of web applications.",
            "Rust is a systems programming language focused on safety, especially safe concurrency, and performance.",
            "Go (or Golang) is a statically typed, compiled language designed at Google, known for simplicity and efficiency.",
            "TypeScript is a superset of JavaScript that adds static typing to the language."
        ]
        
        # Add documents to the collection
        print("Adding documents to the collection...")
        add_result = chroma_add_documents(
            collection_name=collection_name,
            documents=documents,
            metadatas=[
                {"language": "Python", "paradigm": "multi-paradigm"},
                {"language": "JavaScript", "paradigm": "multi-paradigm"},
                {"language": "Rust", "paradigm": "multi-paradigm"},
                {"language": "Go", "paradigm": "concurrent"},
                {"language": "TypeScript", "paradigm": "static-typed"}
            ]
        )
        print_result("Add Documents Result", add_result)
        
        # Get collection info
        print("Getting collection info...")
        info_result = chroma_get_collection_info(collection_name=collection_name)
        print_result("Collection Info", info_result)
        
        # Query documents by similarity
        print("Querying documents by similarity...")
        query_result = chroma_query_documents(
            collection_name=collection_name,
            query_texts=["statically typed programming languages"],
            n_results=2
        )
        print_result("Query Result (statically typed languages)", query_result)
        
        # Query with metadata filter
        print("Querying with metadata filter...")
        query_with_filter = chroma_query_documents(
            collection_name=collection_name,
            query_texts=["programming language"],
            n_results=3,
            where={"paradigm": "multi-paradigm"}
        )
        print_result("Query Result (multi-paradigm languages)", query_with_filter)
        
        # PART 3: Sequential Thinking
        print_section("SEQUENTIAL THINKING DEMO")
        
        # First thought
        print("Starting sequential thinking process...")
        thought1 = """
        I need to implement a function that finds the most frequent item in a list in Python.
        First, I'll think about the approaches we could use:
        
        1. Using a dictionary/Counter to track frequencies
        2. Using list methods like count() for each unique item
        3. Using specialized libraries like numpy or pandas
        
        The first approach seems most straightforward and efficient for general use.
        """
        
        thought1_result = chroma_sequential_thinking(
            thought=thought1,
            thoughtNumber=1,
            totalThoughts=3,
            nextThoughtNeeded=True,
            sessionId=session_id
        )
        print_result("Thought 1 Result", thought1_result)
        
        # Second thought
        thought2 = """
        Using a dictionary to track frequencies is the way to go. Here's how the algorithm would work:
        
        1. Create an empty dictionary
        2. Iterate through each item in the list
           a. If the item is already in the dictionary, increment its count
           b. If not, add it with a count of 1
        3. Find the key with the maximum value in the dictionary
        
        Actually, Python's collections module has a Counter class which is perfect for this task.
        It's specifically designed for counting hashable objects.
        """
        
        thought2_result = chroma_sequential_thinking(
            thought=thought2,
            thoughtNumber=2,
            totalThoughts=3,
            nextThoughtNeeded=True,
            sessionId=session_id
        )
        print_result("Thought 2 Result", thought2_result)
        
        # Final thought with solution
        thought3 = """
        The most elegant solution would use Python's Counter class from the collections module.
        
        Here's the implementation:
        
        ```python
        from collections import Counter
        
        def most_frequent(items):
            # Edge case: empty list
            if not items:
                return None
            
            # Use Counter to count occurrences of each item
            counter = Counter(items)
            
            # Get the most common item
            most_common_item, count = counter.most_common(1)[0]
            
            return most_common_item
        ```
        
        This solution is:
        - Concise: Just a few lines of code
        - Efficient: Counter is optimized for this exact purpose
        - Robust: Handles edge cases like empty lists
        - Readable: The intent is clear
        
        The time complexity is O(n) where n is the length of the input list.
        """
        
        thought3_result = chroma_sequential_thinking(
            thought=thought3,
            thoughtNumber=3,
            totalThoughts=3,
            nextThoughtNeeded=False,
            sessionId=session_id,
            sessionSummary="Developed a solution to find the most frequent item in a list using Python's Counter class from the collections module for optimal performance and readability.",
            keyThoughts=[1, 3]
        )
        print_result("Thought 3 Result (Final)", thought3_result)
        
        # Retrieve thought history
        print("Retrieving thought history...")
        history_result = chroma_get_thought_history(sessionId=session_id)
        print_result("Thought History", history_result)
        
        # PART 4: Cleanup
        print_section("CLEANUP")
        
        # Delete the collection
        print("Deleting the collection...")
        delete_result = chroma_delete_collection(collection_name=collection_name)
        print_result("Delete Result", delete_result)
        
        print("\nDemo completed successfully!")
        
    except Exception as e:
        print(f"\nERROR: {str(e)}")
        print("\nDemo did not complete successfully.")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--run":
        run_chroma_demo()
    else:
        print("""
This script demonstrates using the Chroma MCP tools through the MCP protocol.

To run the demo:
    python run_chroma_demo.py --run

The script shows:
- Collection management (create, list, delete)
- Document operations (add, query with filters)
- Sequential thinking (for complex problem solving)

Note: Make sure the Chroma MCP server is running before executing this demo.
""")
