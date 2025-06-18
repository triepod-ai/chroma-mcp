"""Test ChromaMCP functionality to ensure nothing was lost."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
from chroma_mcp import ChromaMCP
import time
import tempfile
import shutil
import os

def test_chroma_mcp_basic_functionality():
    """Test basic functionality of the ChromaMCP class."""
    print("Testing ChromaMCP basic functionality...")
    
    # Create a temporary directory for persistent storage
    temp_dir = tempfile.mkdtemp()
    try:
        # Create a ChromaMCP instance with persistent storage
        chroma_mcp = ChromaMCP(client_type="persistent", path=temp_dir)
        
        # Test data
        collection_name = f"test_collection_{int(time.time())}"
        documents = [
            "This is the first test document.",
            "Here is the second test document.",
            "And this is the third test document with different content."
        ]
        
        # Store documents
        store_result = chroma_mcp.store({
            "collection_name": collection_name,
            "documents": documents
        })
        
        print("Store result:", store_result)
        assert store_result["status"] == "success"
        assert store_result["documents_added"] == 3
        
        # Query using exact match
        find_result = chroma_mcp.find({
            "collection_name": collection_name
        })
        
        print("Find result (all documents):", find_result)
        assert len(find_result["documents"]) == 3
        assert all(doc in documents for doc in find_result["documents"])
        
        # Query using similarity search
        query_result = chroma_mcp.find({
            "collection_name": collection_name,
            "query_texts": ["test document with different"],
            "n_results": 1
        })
        
        print("Query result (similarity search):", query_result)
        assert len(query_result["documents"][0]) == 1
        assert "third test document" in query_result["documents"][0][0]
        
        print("All tests passed!")
        return True
    
    finally:
        # Properly close the client to release file handles
        if 'chroma_mcp' in locals():
            chroma_mcp.close()
            # Give the system a moment to release file handles
            time.sleep(0.5)
        
        # Clean up the temporary directory
        try:
            shutil.rmtree(temp_dir)
        except PermissionError as e:
            print(f"Warning: Could not fully clean up temporary directory: {e}")
            print("This is not a test failure, just a cleanup issue.")

if __name__ == "__main__":
    test_chroma_mcp_basic_functionality()
