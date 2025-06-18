import chromadb
import sys

# Function to test data persistence by checking if a collection exists
def verify_persistence(collection_name):
    try:
        # Connect to ChromaDB
        client = chromadb.HttpClient(host='localhost', port=8001)
        print(f"Connected to ChromaDB successfully")
        
        # Get all collections and check if our test collection exists
        collections = client.list_collections()
        collection_names = [col.name for col in collections]
        
        if collection_name in collection_names:
            print(f"Collection '{collection_name}' found - data persistence verified!")
            
            # Get the collection and verify data is still there
            collection = client.get_collection(name=collection_name)
            results = collection.query(query_texts=["test document"], n_results=2)
            print(f"Query results after restart: {results}")
            
            return True
        else:
            print(f"Collection '{collection_name}' NOT found - data persistence failed!")
            print(f"Available collections: {collection_names}")
            return False
    
    except Exception as e:
        print(f"Error in verification: {str(e)}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python verify_persistence.py <collection_name>")
        sys.exit(1)
        
    collection_name = sys.argv[1]
    success = verify_persistence(collection_name)
    
    if success:
        print("Persistence test passed - ChromaDB is correctly storing data on the volume!")
    else:
        print("Persistence test failed - Data was not persisted!")
