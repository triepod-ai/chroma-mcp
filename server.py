from typing import Dict, List, Optional
import chromadb
from mcp.server.fastmcp import FastMCP
import os
from dotenv import load_dotenv
import argparse

# Load environment variables from .env file if it exists
load_dotenv()

# Initialize argument parser
parser = argparse.ArgumentParser(description='FastMCP server for Chroma DB')
parser.add_argument('--client-type', 
                   choices=['http', 'persistent', 'ephemeral'],
                   default='ephemeral',
                   help='Type of Chroma client to use')
parser.add_argument('--data-dir',
                   default='/data',
                   help='Directory for persistent client data (only used with persistent client)')
parser.add_argument('--tenant', help='Chroma tenant (only used with http client)', 
                   default=os.getenv('CHROMA_TENANT'))
parser.add_argument('--database', help='Chroma database (only used with http client)', 
                   default=os.getenv('CHROMA_DATABASE'))
parser.add_argument('--api-key', help='Chroma API key (only used with http client)', 
                   default=os.getenv('CHROMA_API_KEY'))
parser.add_argument('--host', help='Chroma host (only used with http client)', 
                   default=os.getenv('CHROMA_HOST', 'api.trychroma.com'))
parser.add_argument('--ssl', help='Use SSL (only used with http client)', 
                   type=bool, 
                   default=os.getenv('CHROMA_SSL', 'true').lower() == 'true')

# Initialize FastMCP server
mcp = FastMCP("chroma")

# Global variables
_chroma_client = None
_args = None

def get_chroma_client():
    """Get or create the global Chroma client instance."""
    global _chroma_client, _args
    if _chroma_client is None:
        if _args is None:
            _args = parser.parse_args()
        
        if _args.client_type == 'http':
            if not _args.tenant:
                raise ValueError("Tenant must be provided via --tenant flag or CHROMA_TENANT environment variable when using HTTP client")
            if not _args.database:
                raise ValueError("Database must be provided via --database flag or CHROMA_DATABASE environment variable when using HTTP client")
            if not _args.api_key:
                raise ValueError("API key must be provided via --api-key flag or CHROMA_API_KEY environment variable when using HTTP client")
            _chroma_client = chromadb.HttpClient(
                ssl=_args.ssl,
                host=_args.host,
                tenant=_args.tenant,
                database=_args.database,
                headers={
                    'x-chroma-token': _args.api_key
                }
            )
        elif _args.client_type == 'persistent':
            data_dir = os.path.join(os.path.dirname(__file__), _args.data_dir)
            os.makedirs(data_dir, exist_ok=True)
            _chroma_client = chromadb.PersistentClient(path=data_dir)
        else:  # ephemeral
            _chroma_client = chromadb.EphemeralClient()
            
    return _chroma_client

##### Collection Tools #####
@mcp.tool()
async def create_collection(
    collection_name: str,
    hnsw_space: Optional[str] = None,
    hnsw_construction_ef: Optional[int] = None,
    hnsw_search_ef: Optional[int] = None,
    hnsw_M: Optional[int] = None,
    hnsw_num_threads: Optional[int] = None,
    hnsw_resize_factor: Optional[float] = None,
    hnsw_batch_size: Optional[int] = None,
    hnsw_sync_threshold: Optional[int] = None
) -> str:
    """Create a new Chroma collection with configurable HNSW parameters.
    
    Args:
        collection_name: Name of the collection to create
        hnsw_space: Distance function used in HNSW index. Options: 'l2', 'ip', 'cosine'
        hnsw_construction_ef: Size of the dynamic candidate list for constructing the HNSW graph
        hnsw_search_ef: Size of the dynamic candidate list for searching the HNSW graph
        hnsw_M: Number of bi-directional links created for every new element
        hnsw_num_threads: Number of threads to use during HNSW construction
        hnsw_resize_factor: Factor to resize the index by when it's full
        hnsw_batch_size: Number of elements to batch together during index construction
        hnsw_sync_threshold: Number of elements to process before syncing index to disk
    """
    client = get_chroma_client()
    
    # Build HNSW configuration directly in metadata, only including non-None values
    metadata = {
        k: v for k, v in {
            "hnsw:space": hnsw_space,
            "hnsw:construction_ef": hnsw_construction_ef,
            "hnsw:M": hnsw_M,
            "hnsw:search_ef": hnsw_search_ef,
            "hnsw:num_threads": hnsw_num_threads,
            "hnsw:resize_factor": hnsw_resize_factor,
            "hnsw:batch_size": hnsw_batch_size,
            "hnsw:sync_threshold": hnsw_sync_threshold
        }.items() if v is not None
    }
    
    client.create_collection(
        name=collection_name,
        metadata=metadata if metadata else None
    )
    
    config_msg = f" with HNSW configuration: {metadata}" if metadata else ""
    return f"Successfully created collection {collection_name}{config_msg}"

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
async def delete_collection(collection_name: str) -> str:
    """Delete a Chroma collection.
    
    Args:
        collection_name: Name of the collection to delete
    """
    client = get_chroma_client()
    client.delete_collection(collection_name)
    return f"Successfully deleted collection {collection_name}"

##### Document Tools #####
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
    # Parse arguments before running the server
    _args = parser.parse_args()
    
    # Validate required arguments for HTTP client
    if _args.client_type == 'http':
        if not _args.tenant:
            parser.error("Tenant must be provided via --tenant flag or CHROMA_TENANT environment variable when using HTTP client")
        if not _args.database:
            parser.error("Database must be provided via --database flag or CHROMA_DATABASE environment variable when using HTTP client")
        if not _args.api_key:
            parser.error("API key must be provided via --api-key flag or CHROMA_API_KEY environment variable when using HTTP client")
    
    # Initialize and run the server
    mcp.run(transport='stdio')
    