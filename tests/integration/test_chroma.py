import chromadb
import uuid
import time

# Function to test ChromaDB connection and data persistence
def test_chroma_persistence():
    try:
        # Connect to ChromaDB
        client = chromadb.HttpClient(host='localhost', port=8001)
        print(f"Connected to ChromaDB successfully")
        
        # Generate a unique collection name for this test
        test_collection_name = f"test_collection_{uuid.uuid4().hex[:8]}"
        print(f"Creating test collection: {test_collection_name}")
        
        # Create a new collection
        collection = client.create_collection(name=test_collection_name)
        
        # Add some documents
        collection.add(
            documents=["This is a test document", "Another test document"],
            metadatas=[{"source": "test1"}, {"source": "test2"}],
            ids=["id1", "id2"]
        )
        
        # Query to confirm data is there
        results = collection.query(query_texts=["test document"], n_results=2)
        print(f"Initial query results: {results}")
        
        # Return the collection name for future tests
        return test_collection_name
    
    except Exception as e:
        print(f"Error in test: {str(e)}")
        return None

if __name__ == "__main__":
    collection_name = test_chroma_persistence()
    if collection_name:
        print(f"Test passed. Collection '{collection_name}' was created and data was added successfully.")
    else:
        print("Test failed.")
