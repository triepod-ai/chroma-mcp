"""
Demo script to demonstrate Chroma MCP functionality.
This script shows how to use the Chroma MCP tools for collection management,
document operations, and sequential thinking.
"""

import time
import json
from datetime import datetime
import uuid

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

# Main demo function
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
        
        # Initialize a thinking session to solve a coding problem
        problem = "How to implement a function that finds the most frequent item in a list in Python?"
        
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

# This allows the script to be imported without running
if __name__ == "__main__":
    # When running this script directly, these functions will be available
    # from the MCP tools server. In a real environment, they would be
    # accessed through the MCP protocol.
    
    # Uncomment and run this script once the MCP Chroma server is running
    # and has properly registered these functions.
    
    # run_chroma_demo()
    
    print("""
This script demonstrates how to use Chroma MCP tools. To run it:

1. Start the Chroma MCP server
2. Use the MCP tools to interact with Chroma collections

The script shows:
- Collection management (create, list, delete)
- Document operations (add, query with filters)
- Sequential thinking (for complex problem solving)

To run this demo, you would need to either:
- Use the MCP protocol to access these functions
- Define these functions with the same signatures to call the MCP server
""")
