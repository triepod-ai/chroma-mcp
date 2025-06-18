import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
from chroma_mcp import ChromaMCP

# Initialize ChromaMCP
chroma_mcp = ChromaMCP()

# Create a simple document collection
collection = {
    "collection_name": "test_collection",
    "documents": ["Hello, World!", "This is a test document.", "Testing Chroma MCP functionality."]
}

# Store documents
chroma_mcp.store(collection)

# Query for documents
result = chroma_mcp.find({"collection_name": "test_collection"})

# Print the results
print("Query Results:", result)
