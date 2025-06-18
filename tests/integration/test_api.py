# Script to test ChromaDB via REST API
import requests
import json
import time

# Wait for the ChromaDB API to be available
def wait_for_api():
    retries = 10
    for i in range(retries):
        try:
            response = requests.get("http://localhost:8001/api/v1/heartbeat")
            if response.status_code == 200:
                print("ChromaDB API is available!")
                return True
        except requests.exceptions.ConnectionError:
            pass
        
        print(f"Waiting for ChromaDB API to be available... ({i+1}/{retries})")
        time.sleep(2)
    
    print("Failed to connect to ChromaDB API")
    return False

# Create a collection
def create_collection():
    try:
        response = requests.post(
            "http://localhost:8001/api/v1/collections",
            json={"name": f"test_collection_{int(time.time())}", "metadata": {"source": "test"}}
        )
        response.raise_for_status()
        print("Successfully created a test collection")
        return response.json()
    except Exception as e:
        print(f"Error creating collection: {e}")
        return None

# Add documents to the collection
def add_documents(collection_id):
    try:
        response = requests.post(
            f"http://localhost:8001/api/v1/collections/{collection_id}/add",
            json={
                "documents": ["This is a test document", "This is another test document"],
                "metadatas": [{"source": "test"}, {"source": "test"}],
                "ids": ["id1", "id2"]
            }
        )
        response.raise_for_status()
        print("Successfully added documents to the collection")
        return response.json()
    except Exception as e:
        print(f"Error adding documents: {e}")
        return None

# Main execution
if wait_for_api():
    collection_info = create_collection()
    if collection_info:
        add_documents(collection_info.get("id"))
        print("Test completed successfully. If you don't see any errors, ChromaDB is working properly.")
