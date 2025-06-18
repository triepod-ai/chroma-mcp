"""ChromaMCP Client for simplified interaction with Chroma collections."""

import chromadb
from typing import Dict, List, Any, Optional

class ChromaMCP:
    """
    A simple client wrapper for Chroma DB functionality.
    
    Provides simplified methods to store and retrieve documents from Chroma collections.
    """
    
    def __init__(self, client_type: str = "persistent", path: Optional[str] = None):
        """
        Initialize a ChromaMCP instance.

        Args:
            client_type: Type of client to use ('persistent' or 'ephemeral')
            path: Path for persistent client (used if client_type is 'persistent')
        """
        if client_type == "persistent" and path:
            self.client = chromadb.PersistentClient(path=path)
        else:
            self.client = chromadb.EphemeralClient()
        self._client_type = client_type
        self._path = path
    
    def close(self):
        """
        Close the Chroma client and release resources.
        
        This should be called before the ChromaMCP instance is destroyed,
        especially for persistent clients to ensure all data is flushed
        and file handles are released.
        """
        # Chroma doesn't have an explicit close method, but we can help GC
        self.client = None
    
    def store(self, data: Dict) -> Dict:
        """
        Store documents in a Chroma collection.
        
        Args:
            data: Dictionary containing:
                - collection_name: Name of the collection
                - documents: List of text documents to add
                - metadatas: Optional list of metadata dictionaries (one per document)
                - ids: Optional list of document IDs
        
        Returns:
            Dictionary with status information
        """
        collection_name = data.get("collection_name")
        documents = data.get("documents", [])
        metadatas = data.get("metadatas")
        ids = data.get("ids")
        
        if not collection_name:
            raise ValueError("collection_name is required")
        if not documents:
            raise ValueError("documents must be a non-empty list")
        
        # Generate sequential IDs if none provided
        if ids is None:
            ids = [str(i) for i in range(len(documents))]
        
        # Get or create collection
        collection = self.client.get_or_create_collection(collection_name)
        
        # Add documents
        collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        
        return {
            "status": "success",
            "collection": collection_name,
            "documents_added": len(documents)
        }
    
    def find(self, query: Dict) -> Dict[str, Any]:
        """
        Find documents in a Chroma collection.
        
        Args:
            query: Dictionary containing:
                - collection_name: Name of the collection to query
                - query_texts: Optional list of query texts for similarity search
                - n_results: Optional number of results to return (default: 10)
                - where: Optional metadata filters
                - ids: Optional list of document IDs to retrieve
        
        Returns:
            Dictionary with query results
        """
        collection_name = query.get("collection_name")
        query_texts = query.get("query_texts", [])
        n_results = query.get("n_results", 10)
        where = query.get("where")
        ids = query.get("ids")
        
        if not collection_name:
            raise ValueError("collection_name is required")
        
        # Get collection
        collection = self.client.get_collection(collection_name)
        
        # Execute query if query_texts provided
        if query_texts:
            results = collection.query(
                query_texts=query_texts,
                n_results=n_results,
                where=where
            )
        # Otherwise get documents directly
        else:
            results = collection.get(
                ids=ids,
                where=where
            )
            
        return results
