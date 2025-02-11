from typing import Dict, List, Optional
import chromadb
from mcp.server.fastmcp import FastMCP
import os
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

# Initialize FastMCP server
mcp = FastMCP("chroma")

# Global client instance
_chroma_client = None

def get_chroma_client():
    """Get or create the global Chroma client instance."""
    global _chroma_client
    if _chroma_client is None:
        _chroma_client = chromadb.HttpClient(
            ssl=os.getenv('CHROMA_SSL', 'true').lower() == 'true',
            host=os.getenv('CHROMA_HOST', 'api.trychroma.com'),
            tenant=os.getenv('CHROMA_TENANT'),
            database=os.getenv('CHROMA_DATABASE'),
            headers={
                'x-chroma-token': os.getenv('CHROMA_API_KEY')
            }
        )
    return _chroma_client

@mcp.tool()
async def add_documents(
    collection_name: str,
    documents: List[str],
    metadatas: Optional[List[Dict]] = None,
    ids: Optional[List[str]] = None
) -> str:
    """Add documents to a Chroma collection.
    
    Args:
        collection_name: Name of the collection to add documents to
        documents: List of text documents to add
        metadatas: Optional list of metadata dictionaries for each document
        ids: Optional list of IDs for the documents
    """
    client = get_chroma_client()
    collection = client.get_or_create_collection(collection_name)
    
    # Generate sequential IDs if none provided
    if ids is None:
        ids = [str(i) for i in range(len(documents))]
    
    collection.add(
        documents=documents,
        metadatas=metadatas,
        ids=ids
    )
    
    return f"Successfully added {len(documents)} documents to collection {collection_name}"

@mcp.tool()
async def query_documents(
    collection_name: str,
    query_texts: List[str],
    n_results: int = 5,
    where: Optional[Dict] = None,
    where_document: Optional[Dict] = None,
    include: Optional[List[str]] = None
) -> Dict:
    """Query documents from a Chroma collection with advanced filtering.
    
    Args:
        collection_name: Name of the collection to query
        query_texts: List of query texts to search for
        n_results: Number of results to return per query
        where: Optional metadata filters using Chroma's query operators
               Examples:
               - Simple equality: {"metadata_field": "value"}
               - Comparison: {"metadata_field": {"$gt": 5}}
               - Logical AND: {"$and": [{"field1": {"$eq": "value1"}}, {"field2": {"$gt": 5}}]}
               - Logical OR: {"$or": [{"field1": {"$eq": "value1"}}, {"field1": {"$eq": "value2"}}]}
        where_document: Optional document content filters
        include: Optional list of what to include in response. Can contain any of:
                ["documents", "embeddings", "metadatas", "distances"]
    """
    client = get_chroma_client()
    collection = client.get_collection(collection_name)
    
    return collection.query(
        query_texts=query_texts,
        n_results=n_results,
        where=where,
        where_document=where_document,
        include=include
    )

@mcp.tool()
async def get_collection_info(collection_name: str) -> Dict:
    """Get information about a Chroma collection.
    
    Args:
        collection_name: Name of the collection to get info about
    """
    client = get_chroma_client()
    collection = client.get_collection(collection_name)
    
    # Get collection count
    count = collection.count()
    
    # Peek at a few documents
    peek_results = collection.peek(limit=3)
    
    return {
        "name": collection_name,
        "count": count,
        "sample_documents": peek_results
    }

@mcp.tool()
async def delete_collection(collection_name: str) -> str:
    """Delete a Chroma collection.
    
    Args:
        collection_name: Name of the collection to delete
    """
    client = get_chroma_client()
    client.delete_collection(collection_name)
    return f"Successfully deleted collection {collection_name}"

@mcp.tool()
async def peek_collection(
    collection_name: str,
    limit: int = 5
) -> Dict:
    """Peek at documents in a Chroma collection.
    
    Args:
        collection_name: Name of the collection to peek into
        limit: Number of documents to peek at
    """
    client = get_chroma_client()
    collection = client.get_collection(collection_name)
    results = collection.peek(limit=limit)
    return results

@mcp.tool()
async def get_collection_count(collection_name: str) -> int:
    """Get the number of documents in a Chroma collection.
    
    Args:
        collection_name: Name of the collection to count
    """
    client = get_chroma_client()
    collection = client.get_collection(collection_name)
    return collection.count()

@mcp.tool()
async def modify_collection(
    collection_name: str,
    new_name: Optional[str] = None,
    new_metadata: Optional[Dict] = None
) -> str:
    """Modify a Chroma collection's name or metadata.
    
    Args:
        collection_name: Name of the collection to modify
        new_name: Optional new name for the collection
        new_metadata: Optional new metadata for the collection
    """
    client = get_chroma_client()
    collection = client.get_collection(collection_name)
    
    if new_name:
        collection.modify(name=new_name)
    if new_metadata:
        collection.modify(metadata=new_metadata)
    
    modified_aspects = []
    if new_name:
        modified_aspects.append("name")
    if new_metadata:
        modified_aspects.append("metadata")
    
    return f"Successfully modified collection {collection_name}: updated {' and '.join(modified_aspects)}"

@mcp.tool()
async def list_collections(
    limit: Optional[int] = None,
    offset: Optional[int] = None
) -> List[str]:
    """List all collection names in the Chroma database with pagination support.
    
    Args:
        limit: Optional maximum number of collections to return
        offset: Optional number of collections to skip before returning results
    
    Returns:
        List of collection names
    """
    client = get_chroma_client()
    return client.list_collections(limit=limit, offset=offset)

@mcp.tool()
async def get_documents(
    collection_name: str,
    ids: Optional[List[str]] = None,
    where: Optional[Dict] = None,
    where_document: Optional[Dict] = None,
    include: Optional[List[str]] = None
) -> Dict:
    """Get documents from a Chroma collection with optional filtering.
    
    Args:
        collection_name: Name of the collection to get documents from
        ids: Optional list of document IDs to retrieve
        where: Optional metadata filters using Chroma's query operators
               Examples:
               - Simple equality: {"metadata_field": "value"}
               - Comparison: {"metadata_field": {"$gt": 5}}
               - Logical AND: {"$and": [{"field1": {"$eq": "value1"}}, {"field2": {"$gt": 5}}]}
               - Logical OR: {"$or": [{"field1": {"$eq": "value1"}}, {"field1": {"$eq": "value2"}}]}
        where_document: Optional document content filters
        include: Optional list of what to include in response. Can contain any of:
                ["documents", "embeddings", "metadatas"]
    
    Returns:
        Dictionary containing the matching documents, their IDs, and requested includes
    """
    client = get_chroma_client()
    collection = client.get_collection(collection_name)
    
    return collection.get(
        ids=ids,
        where=where,
        where_document=where_document,
        include=include
    )

if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio')
    