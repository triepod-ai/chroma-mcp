from typing import Dict, List, Optional, TypedDict
from enum import Enum
import chromadb
from mcp.server.fastmcp import FastMCP
import os
from dotenv import load_dotenv
import argparse
from chromadb.config import Settings
import ssl
import uuid
import time
import json
import logging
from pathlib import Path
from typing_extensions import TypedDict


from chromadb.api.collection_configuration import (
    CreateCollectionConfiguration, CreateHNSWConfiguration, UpdateHNSWConfiguration, UpdateCollectionConfiguration
    )
from chromadb.api import EmbeddingFunction
from chromadb.utils.embedding_functions import (
    DefaultEmbeddingFunction,
    CohereEmbeddingFunction,
    OpenAIEmbeddingFunction,
    JinaEmbeddingFunction,
    VoyageAIEmbeddingFunction,
    RoboflowEmbeddingFunction,
)

# Set up dual logging for MCP protocol compliance
# File logging for debugging, but keep stdout/stderr available for MCP protocol
log_dir = Path("/tmp")
log_file = log_dir / "chroma-mcp.log"

# Create logger with dual handlers: file + null handler to avoid stdout interference
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# File handler for debugging
file_handler = logging.FileHandler(str(log_file))
file_handler.setLevel(logging.INFO)
file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)

# Add NullHandler to prevent any accidental console output
null_handler = logging.NullHandler()
logger.addHandler(null_handler)

# Prevent logging from interfering with MCP protocol stdout/stderr
logger.propagate = False

# CRITICAL: Ensure root logger doesn't interfere with FastMCP stdout/stderr
root_logger = logging.getLogger()
if not root_logger.handlers:
    # If no handlers, add NullHandler to prevent default console output
    root_logger.addHandler(logging.NullHandler())
else:
    # If handlers exist, ensure they don't output to console
    for handler in root_logger.handlers[:]:
        if isinstance(handler, logging.StreamHandler):
            root_logger.removeHandler(handler)

# Disable ChromaDB telemetry and HTTP logging to prevent MCP protocol interference
import os
os.environ['ANONYMIZED_TELEMETRY'] = 'false'
os.environ['CHROMA_TELEMETRY_DISABLED'] = 'true'

# Suppress ChromaDB and httpx logging to ERROR level only (not completely silent)
# This prevents initialization messages while allowing error reporting
logging.getLogger('chromadb').setLevel(logging.ERROR)
logging.getLogger('httpx').setLevel(logging.ERROR)
logging.getLogger('httpcore').setLevel(logging.ERROR)
logging.getLogger('posthog').setLevel(logging.ERROR)

# Ensure these loggers also don't interfere with stdout/stderr
for logger_name in ['chromadb', 'httpx', 'httpcore', 'posthog']:
    lib_logger = logging.getLogger(logger_name)
    lib_logger.propagate = False
    # Add NullHandler to prevent any console output
    if not lib_logger.handlers:
        lib_logger.addHandler(logging.NullHandler())

# Initialize FastMCP server
mcp = FastMCP("chroma")

# Ensure stdout and stderr are properly configured for MCP protocol
import sys
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

# Global variables
_chroma_client = None

def create_parser():
    """Create and return the argument parser."""
    parser = argparse.ArgumentParser(description='FastMCP server for Chroma DB')
    parser.add_argument('--client-type', 
                       choices=['http', 'cloud', 'persistent', 'ephemeral'],
                       default=os.getenv('CHROMA_CLIENT_TYPE', 'persistent'),
                       help='Type of Chroma client to use (default: persistent).')
    parser.add_argument('--data-dir',
                       default=os.getenv('CHROMA_DATA_DIR'),
                       help='Directory for persistent client data (only used with persistent client)')
    parser.add_argument('--host', 
                       help='Chroma host (required for http client)', 
                       default=os.getenv('CHROMA_HOST'))
    parser.add_argument('--port', 
                       help='Chroma port (optional for http client)', 
                       default=os.getenv('CHROMA_PORT'))
    parser.add_argument('--custom-auth-credentials',
                       help='Custom auth credentials (optional for http client)', 
                       default=os.getenv('CHROMA_CUSTOM_AUTH_CREDENTIALS'))
    parser.add_argument('--tenant', 
                       help='Chroma tenant (optional for http client)', 
                       default=os.getenv('CHROMA_TENANT'))
    parser.add_argument('--database', 
                       help='Chroma database (required if tenant is provided)', 
                       default=os.getenv('CHROMA_DATABASE'))
    parser.add_argument('--api-key', 
                       help='Chroma API key (required if tenant is provided)', 
                       default=os.getenv('CHROMA_API_KEY'))
    parser.add_argument('--ssl', 
                       help='Use SSL (optional for http client)', 
                       type=lambda x: x.lower() in ['true', 'yes', '1', 't', 'y'],
                       default=os.getenv('CHROMA_SSL', 'true').lower() in ['true', 'yes', '1', 't', 'y'])
    parser.add_argument('--dotenv-path', 
                       help='Path to .env file', 
                       default=os.getenv('CHROMA_DOTENV_PATH', '.chroma_env'))
    return parser

def get_chroma_client(args=None):
    """Get or create the global Chroma client instance."""
    global _chroma_client
    if _chroma_client is None:
        if args is None:
            # Create parser and parse args if not provided
            parser = create_parser()
            args = parser.parse_args()
        
        # Load environment variables from .env file if it exists
        load_dotenv(dotenv_path=args.dotenv_path)
        # Log to file only - stderr breaks MCP protocol
        logger.info(f"Loading environment from: {args.dotenv_path}")
        if args.client_type == 'http':
            if not args.host:
                raise ValueError("Host must be provided via --host flag or CHROMA_HOST environment variable when using HTTP client")
            
            settings = Settings()
            if args.custom_auth_credentials:
                settings = Settings(
                    chroma_client_auth_provider="chromadb.auth.basic_authn.BasicAuthClientProvider",
                    chroma_client_auth_credentials=args.custom_auth_credentials
                )
            
            # Handle SSL configuration with retry and fallback
            try:
                _chroma_client = chromadb.HttpClient(
                    host=args.host,
                    port=args.port if args.port else None,
                    ssl=args.ssl,
                    settings=settings
                )
                # Test the connection
                _chroma_client.heartbeat()
                logger.info(f"Successfully connected to Chroma HTTP server at {args.host}:{args.port}")
            except ssl.SSLError as e:
                # Log to file only - stderr breaks MCP protocol
                logger.error(f"SSL connection failed: {str(e)}")
                raise
            except Exception as e:
                # Log to file only - stderr breaks MCP protocol
                logger.error(f"Error connecting to HTTP client: {str(e)}")
                logger.error("This may be due to API version mismatch or network issues")
                raise
            
        elif args.client_type == 'cloud':
            if not args.tenant:
                raise ValueError("Tenant must be provided via --tenant flag or CHROMA_TENANT environment variable when using cloud client")
            if not args.database:
                raise ValueError("Database must be provided via --database flag or CHROMA_DATABASE environment variable when using cloud client")
            if not args.api_key:
                raise ValueError("API key must be provided via --api-key flag or CHROMA_API_KEY environment variable when using cloud client")
            
            try:
                _chroma_client = chromadb.HttpClient(
                    host="api.trychroma.com",
                    ssl=True,  # Always use SSL for cloud
                    tenant=args.tenant,
                    database=args.database,
                    headers={
                        'x-chroma-token': args.api_key
                    }
                )
            except ssl.SSLError as e:
                # Log to file only - stderr breaks MCP protocol
                logger.error(f"SSL connection failed: {str(e)}")
                raise
            except Exception as e:
                # Log to file only - stderr breaks MCP protocol
                logger.error(f"Error connecting to cloud client: {str(e)}")
                raise
                
        elif args.client_type == 'persistent':
            if not args.data_dir:
                raise ValueError("Data directory must be provided via --data-dir flag when using persistent client")
            _chroma_client = chromadb.PersistentClient(path=args.data_dir)
        else:  # ephemeral
            _chroma_client = chromadb.EphemeralClient()
            
    return _chroma_client

##### Collection Tools #####

@mcp.tool()
async def test_mcp_response() -> str:
    """Test function to verify MCP responses are working.
    
    Returns:
        Simple test message to confirm output is visible
    """
    return "MCP response test successful! If you can see this, tool responses are working."

@mcp.tool()
async def chroma_list_collections(
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
    try:
        colls = client.list_collections(limit=limit, offset=offset)
        # iterate over colls and output the names
        return [coll.name for coll in colls]

    except Exception as e:
        raise Exception(f"Failed to list collections: {str(e)}") from e

mcp_known_embedding_functions: Dict[str, EmbeddingFunction] = {
    "default": DefaultEmbeddingFunction,
    "cohere": CohereEmbeddingFunction,
    "openai": OpenAIEmbeddingFunction,
    "jina": JinaEmbeddingFunction,
    "voyageai": VoyageAIEmbeddingFunction,
    "roboflow": RoboflowEmbeddingFunction,
}
@mcp.tool()
async def chroma_create_collection(
    collection_name: str,
    embedding_function_name: Optional[str] = "default",
    metadata: Optional[Dict] = None,
    space: Optional[str] = None,
    ef_construction: Optional[int] = None,
    ef_search: Optional[int] = None,
    max_neighbors: Optional[int] = None,
    num_threads: Optional[int] = None,
    batch_size: Optional[int] = None,
    sync_threshold: Optional[int] = None,
    resize_factor: Optional[float] = None,
) -> str:
    """Create a new Chroma collection with configurable HNSW parameters.
    
    Args:
        collection_name: Name of the collection to create
        space: Distance function used in HNSW index. Options: 'l2', 'ip', 'cosine'
        ef_construction: Size of the dynamic candidate list for constructing the HNSW graph
        ef_search: Size of the dynamic candidate list for searching the HNSW graph
        max_neighbors: Maximum number of neighbors to consider during HNSW graph construction
        num_threads: Number of threads to use during HNSW construction
        batch_size: Number of elements to batch together during index construction
        sync_threshold: Number of elements to process before syncing index to disk
        resize_factor: Factor to resize the index by when it's full
        embedding_function_name: Name of the embedding function to use. Options: 'default', 'cohere', 'openai', 'jina', 'voyageai', 'ollama', 'roboflow'
        metadata: Optional metadata dict to add to the collection
    """
    client = get_chroma_client()
        
    
    embedding_function = mcp_known_embedding_functions[embedding_function_name]
    
    hnsw_config = CreateHNSWConfiguration()
    if space:
        hnsw_config["space"] = space
    if ef_construction:
        hnsw_config["ef_construction"] = ef_construction
    if ef_search:
        hnsw_config["ef_search"] = ef_search
    if max_neighbors:
        hnsw_config["max_neighbors"] = max_neighbors
    if num_threads:
        hnsw_config["num_threads"] = num_threads
    if batch_size:
        hnsw_config["batch_size"] = batch_size
    if sync_threshold:
        hnsw_config["sync_threshold"] = sync_threshold
    if resize_factor:
        hnsw_config["resize_factor"] = resize_factor
        
        
    
    configuration=CreateCollectionConfiguration(
        hnsw=hnsw_config,
        embedding_function=embedding_function()
    )
    
    try:
        client.create_collection(
            name=collection_name,
            configuration=configuration,
            metadata=metadata
        )
        config_msg = f" with configuration: {configuration}"
        return f"Successfully created collection {collection_name}{config_msg}"
    except Exception as e:
        raise Exception(f"Failed to create collection '{collection_name}': {str(e)}") from e

@mcp.tool()
async def chroma_peek_collection(
    collection_name: str,
    limit: int = 5
) -> Dict:
    """Peek at documents in a Chroma collection.
    
    Args:
        collection_name: Name of the collection to peek into
        limit: Number of documents to peek at
    """
    client = get_chroma_client()
    try:
        collection = client.get_collection(collection_name)
        results = collection.peek(limit=limit)
        return results
    except Exception as e:
        raise Exception(f"Failed to peek collection '{collection_name}': {str(e)}") from e

@mcp.tool()
async def chroma_get_collection_info(collection_name: str) -> Dict:
    """Get information about a Chroma collection.
    
    Args:
        collection_name: Name of the collection to get info about
    """
    client = get_chroma_client()
    try:
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
    except Exception as e:
        raise Exception(f"Failed to get collection info for '{collection_name}': {str(e)}") from e
    
@mcp.tool()
async def chroma_get_collection_count(collection_name: str) -> int:
    """Get the number of documents in a Chroma collection.
    
    Args:
        collection_name: Name of the collection to count
    """
    client = get_chroma_client()
    try:
        collection = client.get_collection(collection_name)
        return collection.count()
    except Exception as e:
        raise Exception(f"Failed to get collection count for '{collection_name}': {str(e)}") from e

@mcp.tool()
async def chroma_modify_collection(
    collection_name: str,
    new_name: Optional[str] = None,
    new_metadata: Optional[Dict] = None,
    ef_search: Optional[int] = None,
    num_threads: Optional[int] = None,
    batch_size: Optional[int] = None,
    sync_threshold: Optional[int] = None,
    resize_factor: Optional[float] = None,
) -> str:
    """Modify a Chroma collection's name or metadata.
    
    Args:
        collection_name: Name of the collection to modify
        new_name: Optional new name for the collection
        new_metadata: Optional new metadata for the collection
        ef_search: Size of the dynamic candidate list for searching the HNSW graph
        num_threads: Number of threads to use during HNSW construction
        batch_size: Number of elements to batch together during index construction
        sync_threshold: Number of elements to process before syncing index to disk
        resize_factor: Factor to resize the index by when it's full
    """
    client = get_chroma_client()
    try:
        collection = client.get_collection(collection_name)
        
        hnsw_config = UpdateHNSWConfiguration()
        if ef_search:
            hnsw_config["ef_search"] = ef_search
        if num_threads:
            hnsw_config["num_threads"] = num_threads
        if batch_size:
            hnsw_config["batch_size"] = batch_size
        if sync_threshold:
            hnsw_config["sync_threshold"] = sync_threshold
        if resize_factor:
            hnsw_config["resize_factor"] = resize_factor
        
        configuration = UpdateCollectionConfiguration(
            hnsw=hnsw_config
        )
        collection.modify(name=new_name, configuration=configuration, metadata=new_metadata)
        
        modified_aspects = []
        if new_name:
            modified_aspects.append("name")
        if new_metadata:
            modified_aspects.append("metadata")
        if ef_search or num_threads or batch_size or sync_threshold or resize_factor:
            modified_aspects.append("hnsw")
        
        return f"Successfully modified collection {collection_name}: updated {' and '.join(modified_aspects)}"
    except Exception as e:
        raise Exception(f"Failed to modify collection '{collection_name}': {str(e)}") from e

@mcp.tool()
async def chroma_delete_collection(collection_name: str) -> str:
    """Delete a Chroma collection.
    
    Args:
        collection_name: Name of the collection to delete
    """
    client = get_chroma_client()
    try:
        client.delete_collection(collection_name)
        return f"Successfully deleted collection {collection_name}"
    except Exception as e:
        raise Exception(f"Failed to delete collection '{collection_name}': {str(e)}") from e

##### Document Tools #####
@mcp.tool()
async def chroma_add_documents(
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
    if not documents:
        raise ValueError("The 'documents' list cannot be empty.")

    client = get_chroma_client()
    try:
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
    except Exception as e:
        raise Exception(f"Failed to add documents to collection '{collection_name}': {str(e)}") from e

@mcp.tool()
async def chroma_query_documents(
    collection_name: str,
    query_texts: List[str],
    n_results: int = 5,
    where: Optional[Dict] = None,
    where_document: Optional[Dict] = None,
    include: List[str] = ["documents", "metadatas", "distances"]
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
        include: List of what to include in response. By default, this will include documents, metadatas, and distances.
    """
    if not query_texts:
        raise ValueError("The 'query_texts' list cannot be empty.")

    client = get_chroma_client()
    try:
        collection = client.get_collection(collection_name)
        return collection.query(
            query_texts=query_texts,
            n_results=n_results,
            where=where,
            where_document=where_document,
            include=include
        )
    except Exception as e:
        raise Exception(f"Failed to query documents from collection '{collection_name}': {str(e)}") from e

@mcp.tool()
async def chroma_get_documents(
    collection_name: str,
    ids: Optional[List[str]] = None,
    where: Optional[Dict] = None,
    where_document: Optional[Dict] = None,
    include: List[str] = ["documents", "metadatas"],
    limit: Optional[int] = None,
    offset: Optional[int] = None
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
        include: List of what to include in response. By default, this will include documents, and metadatas.
        limit: Optional maximum number of documents to return
        offset: Optional number of documents to skip before returning results
    
    Returns:
        Dictionary containing the matching documents, their IDs, and requested includes
    """
    client = get_chroma_client()
    try:
        collection = client.get_collection(collection_name)
        return collection.get(
            ids=ids,
            where=where,
            where_document=where_document,
            include=include,
            limit=limit,
            offset=offset
        )
    except Exception as e:
        raise Exception(f"Failed to get documents from collection '{collection_name}': {str(e)}") from e

@mcp.tool()
async def chroma_update_documents(
    collection_name: str,
    ids: List[str],
    embeddings: Optional[List[List[float]]] = None,
    metadatas: Optional[List[Dict]] = None,
    documents: Optional[List[str]] = None
) -> str:
    """Update documents in a Chroma collection.

    Args:
        collection_name: Name of the collection to update documents in
        ids: List of document IDs to update (required)
        embeddings: Optional list of new embeddings for the documents.
                    Must match length of ids if provided.
        metadatas: Optional list of new metadata dictionaries for the documents.
                   Must match length of ids if provided.
        documents: Optional list of new text documents.
                   Must match length of ids if provided.

    Returns:
        A confirmation message indicating the number of documents updated.

    Raises:
        ValueError: If 'ids' is empty or if none of 'embeddings', 'metadatas',
                    or 'documents' are provided, or if the length of provided
                    update lists does not match the length of 'ids'.
        Exception: If the collection does not exist or if the update operation fails.
    """
    if not ids:
        raise ValueError("The 'ids' list cannot be empty.")

    if embeddings is None and metadatas is None and documents is None:
        raise ValueError(
            "At least one of 'embeddings', 'metadatas', or 'documents' "
            "must be provided for update."
        )

    # Ensure provided lists match the length of ids if they are not None
    if embeddings is not None and len(embeddings) != len(ids):
        raise ValueError("Length of 'embeddings' list must match length of 'ids' list.")
    if metadatas is not None and len(metadatas) != len(ids):
        raise ValueError("Length of 'metadatas' list must match length of 'ids' list.")
    if documents is not None and len(documents) != len(ids):
        raise ValueError("Length of 'documents' list must match length of 'ids' list.")


    client = get_chroma_client()
    try:
        collection = client.get_collection(collection_name)
    except Exception as e:
        raise Exception(
            f"Failed to get collection '{collection_name}': {str(e)}"
        ) from e

    # Prepare arguments for update, excluding None values at the top level
    update_args = {
        "ids": ids,
        "embeddings": embeddings,
        "metadatas": metadatas,
        "documents": documents,
    }
    kwargs = {k: v for k, v in update_args.items() if v is not None}

    try:
        collection.update(**kwargs)
        return (
            f"Successfully processed update request for {len(ids)} documents in "
            f"collection '{collection_name}'. Note: Non-existent IDs are ignored by ChromaDB."
        )
    except Exception as e:
        raise Exception(
            f"Failed to update documents in collection '{collection_name}': {str(e)}"
        ) from e

@mcp.tool()
async def chroma_delete_documents(
    collection_name: str,
    ids: List[str]
) -> str:
    """Delete documents from a Chroma collection.

    Args:
        collection_name: Name of the collection to delete documents from
        ids: List of document IDs to delete

    Returns:
        A confirmation message indicating the number of documents deleted.

    Raises:
        ValueError: If 'ids' is empty
        Exception: If the collection does not exist or if the delete operation fails.
    """
    if not ids:
        raise ValueError("The 'ids' list cannot be empty.")

    client = get_chroma_client()
    try:
        collection = client.get_collection(collection_name)
    except Exception as e:
        raise Exception(
            f"Failed to get collection '{collection_name}': {str(e)}"
        ) from e

    try:
        collection.delete(ids=ids)
        return (
            f"Successfully deleted {len(ids)} documents from "
            f"collection '{collection_name}'. Note: Non-existent IDs are ignored by ChromaDB."
        )
    except Exception as e:
        raise Exception(
            f"Failed to delete documents from collection '{collection_name}': {str(e)}"
        ) from e

@mcp.tool()
async def chroma_sequential_thinking(
    thought: str,
    thought_number: int,
    total_thoughts: int,
    next_thought_needed: bool,
    session_id: Optional[str] = None,
    is_revision: Optional[bool] = None,
    revises_thought: Optional[int] = None,
    branch_from_thought: Optional[int] = None,
    branch_id: Optional[str] = None,
    session_summary: Optional[str] = None,
    key_thoughts: Optional[List[int]] = None,
    needs_more_thoughts: Optional[bool] = None
) -> Dict:
    """Store and process a sequential thought in ChromaDB.
    
    Args:
        thought: The thought content as a string
        thought_number: Current thought number in the sequence
        total_thoughts: Total number of thoughts planned for this session
        next_thought_needed: Whether more thoughts are needed to continue
        session_id: Optional session identifier (generated if not provided)
        is_revision: Whether this thought revises a previous thought
        revises_thought: Thought number being revised (if is_revision is True)
        branch_from_thought: Thought number this branches from (for alternative paths)
        branch_id: Identifier for the branch (generated if not provided)
        session_summary: Summary of the session (typically provided with final thought)
        key_thoughts: List of important thought numbers in this session
        needs_more_thoughts: Whether the session needs additional thoughts beyond total_thoughts
    
    Returns:
        Dictionary containing session info, thought metadata, and persistence details
    """
    import uuid
    import time
    
    try:
        # Generate session_id if not provided
        if session_id is None:
            session_id = str(uuid.uuid4())[:8]
            
        # Generate branch_id if branching but no ID provided
        if branch_from_thought is not None and branch_id is None:
            branch_id = f"branch_{int(time.time())}"
        
        # Prepare input data for validation
        input_data = {
            "sessionId": session_id,
            "thought": thought,
            "thoughtNumber": thought_number,
            "totalThoughts": total_thoughts,
            "nextThoughtNeeded": next_thought_needed,
            "isRevision": is_revision,
            "revisesThought": revises_thought,
            "branchFromThought": branch_from_thought,
            "branchId": branch_id,
            "needsMoreThoughts": needs_more_thoughts
        }
        
        # Process the thought using existing helper function
        result = process_thought(input_data)
        
        # Add additional fields from parameters
        if session_summary:
            result["summary"] = {
                "content": session_summary,
                "version": 1
            }
            
        if key_thoughts:
            result["keyThoughts"] = key_thoughts
            
        # Generate a unique ID for this thought
        result["persistedId"] = f"{session_id}_{thought_number}"
        if branch_id:
            result["persistedId"] += f"_{branch_id}"
            
        return result
        
    except Exception as e:
        raise Exception(f"Failed to process sequential thought: {str(e)}") from e

@mcp.tool()
async def chroma_get_similar_sessions(
    session_type: Optional[str] = None,
    min_thought_count: Optional[int] = None,
    max_thought_count: Optional[int] = None,
    query_text: Optional[str] = None,
    n_results: int = 5
) -> Dict:
    """Find similar sequential thinking sessions based on metadata and content.
    
    Args:
        session_type: Optional filter by session type (e.g., 'algorithm_design', 'code_review')
        min_thought_count: Minimum number of thoughts in the session
        max_thought_count: Maximum number of thoughts in the session
        query_text: Optional text to search for similar session content
        n_results: Number of similar sessions to return
    
    Returns:
        Dictionary containing matching sessions with similarity scores
    """
    try:
        client = get_chroma_client()
        
        # Get or create the sessions collection
        try:
            collection = client.get_collection("thought_sessions")
        except Exception:
            # Collection doesn't exist yet, return empty results
            return {
                "sessions": [],
                "total_found": 0,
                "message": "No sessions collection found. Create some sequential thoughts first."
            }
        
        # Build metadata filter
        where_filter = {}
        if session_type:
            where_filter["sessionType"] = session_type
        if min_thought_count is not None:
            where_filter["thoughtCount"] = {"$gte": min_thought_count}
        if max_thought_count is not None:
            if "thoughtCount" in where_filter:
                where_filter["thoughtCount"]["$lte"] = max_thought_count
            else:
                where_filter["thoughtCount"] = {"$lte": max_thought_count}
        
        # Query the collection
        if query_text:
            # Search by similarity to query text
            results = collection.query(
                query_texts=[query_text],
                n_results=n_results,
                where=where_filter if where_filter else None,
                include=["documents", "metadatas", "distances"]
            )
        else:
            # Just get documents matching the filter
            results = collection.get(
                where=where_filter if where_filter else None,
                limit=n_results,
                include=["documents", "metadatas"]
            )
            # Add dummy distances for consistency
            if "distances" not in results:
                results["distances"] = [[0.0] * len(results["ids"][0])] if results["ids"] else [[]]
        
        # Format the response
        sessions = []
        if results["ids"]:
            # Handle both query and get results
            ids_list = results["ids"][0] if isinstance(results["ids"][0], list) else results["ids"]
            metadatas_list = results["metadatas"][0] if results["metadatas"] and isinstance(results["metadatas"][0], list) else results["metadatas"] if results["metadatas"] else []
            documents_list = results["documents"][0] if results["documents"] and isinstance(results["documents"][0], list) else results["documents"] if results["documents"] else []
            distances_list = results["distances"][0] if results["distances"] and isinstance(results["distances"][0], list) else []
            
            for i, session_id in enumerate(ids_list):
                session_data = {
                    "sessionId": session_id,
                    "metadata": metadatas_list[i] if i < len(metadatas_list) else {},
                    "summary": documents_list[i] if i < len(documents_list) else "",
                    "similarityScore": 1.0 - distances_list[i] if i < len(distances_list) else 1.0
                }
                sessions.append(session_data)
        
        return {
            "sessions": sessions,
            "total_found": len(sessions),
            "search_criteria": {
                "session_type": session_type,
                "min_thought_count": min_thought_count,
                "max_thought_count": max_thought_count,
                "query_text": query_text
            }
        }
        
    except Exception as e:
        raise Exception(f"Failed to find similar sessions: {str(e)}") from e

@mcp.tool()
async def chroma_get_thought_history(
    session_id: str,
    include_branches: bool = True,
    sort_by_number: bool = True
) -> Dict:
    """Retrieve the complete thought history for a sequential thinking session.
    
    Args:
        session_id: The session identifier to retrieve thoughts for
        include_branches: Whether to include thoughts from all branches
        sort_by_number: Whether to sort thoughts by thought number
    
    Returns:
        Dictionary containing the thought history with metadata
    """
    try:
        client = get_chroma_client()
        
        # Get the thoughts collection
        try:
            collection = client.get_collection("sequential_thoughts")
        except Exception:
            return {
                "thoughts": [],
                "session_id": session_id,
                "total_thoughts": 0,
                "message": "No thoughts collection found. Create some sequential thoughts first."
            }
        
        # Query for thoughts in this session
        results = collection.get(
            where={"sessionId": session_id},
            include=["documents", "metadatas"]
        )
        
        thoughts = []
        if results["ids"]:
            for i, thought_id in enumerate(results["ids"]):
                metadata = results["metadatas"][i] if results["metadatas"] else {}
                thought_content = results["documents"][i] if results["documents"] else ""
                
                # Skip branches if not requested
                if not include_branches and metadata.get("branchId"):
                    continue
                
                thought_data = {
                    "thoughtId": thought_id,
                    "thoughtNumber": metadata.get("thoughtNumber", 0),
                    "thought": thought_content,
                    "sessionId": metadata.get("sessionId", session_id),
                    "totalThoughts": metadata.get("totalThoughts", 0),
                    "nextThoughtNeeded": metadata.get("nextThoughtNeeded", False),
                    "isRevision": metadata.get("isRevision", False),
                    "revisesThought": metadata.get("revisesThought"),
                    "branchFromThought": metadata.get("branchFromThought"),
                    "branchId": metadata.get("branchId"),
                    "timestamp": metadata.get("timestamp"),
                    "needsMoreThoughts": metadata.get("needsMoreThoughts")
                }
                thoughts.append(thought_data)
        
        # Sort thoughts if requested
        if sort_by_number:
            thoughts.sort(key=lambda x: (x["thoughtNumber"], x.get("branchId", "")))
        
        # Group thoughts by branches
        main_branch = [t for t in thoughts if not t.get("branchId")]
        branches = {}
        for thought in thoughts:
            if thought.get("branchId"):
                branch_id = thought["branchId"]
                if branch_id not in branches:
                    branches[branch_id] = []
                branches[branch_id].append(thought)
        
        return {
            "session_id": session_id,
            "total_thoughts": len(thoughts),
            "main_branch": main_branch,
            "branches": branches,
            "all_thoughts": thoughts if include_branches else main_branch,
            "has_branches": len(branches) > 0
        }
        
    except Exception as e:
        raise Exception(f"Failed to retrieve thought history for session '{session_id}': {str(e)}") from e

@mcp.tool()
async def chroma_get_thought_branches(
    session_id: str,
    thought_number: Optional[int] = None
) -> Dict:
    """Retrieve all branches that stem from a specific thought or session.
    
    Args:
        session_id: The session identifier to search for branches
        thought_number: Optional specific thought number to find branches from
    
    Returns:
        Dictionary containing branch information organized as a tree structure
    """
    try:
        client = get_chroma_client()
        
        # Get the thoughts collection
        try:
            collection = client.get_collection("sequential_thoughts")
        except Exception:
            return {
                "branches": [],
                "session_id": session_id,
                "total_branches": 0,
                "message": "No thoughts collection found. Create some sequential thoughts first."
            }
        
        # Query for all thoughts in this session
        results = collection.get(
            where={"sessionId": session_id},
            include=["documents", "metadatas"]
        )
        
        all_thoughts = []
        if results["ids"]:
            for i, thought_id in enumerate(results["ids"]):
                metadata = results["metadatas"][i] if results["metadatas"] else {}
                thought_content = results["documents"][i] if results["documents"] else ""
                
                thought_data = {
                    "thoughtId": thought_id,
                    "thoughtNumber": metadata.get("thoughtNumber", 0),
                    "thought": thought_content,
                    "branchFromThought": metadata.get("branchFromThought"),
                    "branchId": metadata.get("branchId"),
                    "isRevision": metadata.get("isRevision", False),
                    "timestamp": metadata.get("timestamp")
                }
                all_thoughts.append(thought_data)
        
        # Filter for branches (thoughts that have branchFromThought set)
        branch_thoughts = [t for t in all_thoughts if t.get("branchFromThought") is not None]
        
        # If thought_number is specified, filter to branches from that thought
        if thought_number is not None:
            branch_thoughts = [t for t in branch_thoughts if t.get("branchFromThought") == thought_number]
        
        # Group branches by branchId
        branches = {}
        for thought in branch_thoughts:
            branch_id = thought.get("branchId", "unknown")
            if branch_id not in branches:
                branches[branch_id] = {
                    "branchId": branch_id,
                    "branchFromThought": thought.get("branchFromThought"),
                    "thoughts": []
                }
            branches[branch_id]["thoughts"].append(thought)
        
        # Sort thoughts within each branch by thought number
        for branch_info in branches.values():
            branch_info["thoughts"].sort(key=lambda x: x["thoughtNumber"])
        
        # Create a tree structure
        branch_tree = {}
        for branch_id, branch_info in branches.items():
            branch_from = branch_info["branchFromThought"]
            if branch_from not in branch_tree:
                branch_tree[branch_from] = []
            branch_tree[branch_from].append(branch_info)
        
        # Format response
        branch_list = list(branches.values())
        
        return {
            "session_id": session_id,
            "total_branches": len(branches),
            "branches": branch_list,
            "branch_tree": branch_tree,
            "filter_thought_number": thought_number,
            "summary": {
                "branches_found": len(branches),
                "branching_points": list(branch_tree.keys()) if branch_tree else []
            }
        }
        
    except Exception as e:
        raise Exception(f"Failed to retrieve thought branches for session '{session_id}': {str(e)}") from e

@mcp.tool()
async def chroma_continue_thought_chain(
    session_id: str,
    analysis_type: str = "continuation"
) -> Dict:
    """Analyze the last thought in a session and provide continuation suggestions.
    
    Args:
        session_id: The session identifier to analyze
        analysis_type: Type of analysis ('continuation', 'completion', 'branching')
    
    Returns:
        Dictionary containing analysis and recommendations for continuing the thought chain
    """
    try:
        client = get_chroma_client()
        
        # Get the thoughts collection
        try:
            collection = client.get_collection("sequential_thoughts")
        except Exception:
            return {
                "session_id": session_id,
                "recommendations": [],
                "message": "No thoughts collection found. Create some sequential thoughts first."
            }
        
        # Get all thoughts for this session
        results = collection.get(
            where={"sessionId": session_id},
            include=["documents", "metadatas"]
        )
        
        if not results["ids"]:
            return {
                "session_id": session_id,
                "recommendations": [],
                "message": f"No thoughts found for session '{session_id}'"
            }
        
        # Parse and sort thoughts
        thoughts = []
        for i, thought_id in enumerate(results["ids"]):
            metadata = results["metadatas"][i] if results["metadatas"] else {}
            thought_content = results["documents"][i] if results["documents"] else ""
            
            thought_data = {
                "thoughtId": thought_id,
                "thoughtNumber": metadata.get("thoughtNumber", 0),
                "thought": thought_content,
                "totalThoughts": metadata.get("totalThoughts", 0),
                "nextThoughtNeeded": metadata.get("nextThoughtNeeded", False),
                "branchId": metadata.get("branchId"),
                "needsMoreThoughts": metadata.get("needsMoreThoughts")
            }
            thoughts.append(thought_data)
        
        # Sort by thought number to find the latest
        main_thoughts = [t for t in thoughts if not t.get("branchId")]
        main_thoughts.sort(key=lambda x: x["thoughtNumber"])
        
        if not main_thoughts:
            return {
                "session_id": session_id,
                "recommendations": [],
                "message": "No main branch thoughts found for continuation analysis"
            }
        
        latest_thought = main_thoughts[-1]
        
        # Analyze based on type
        recommendations = []
        analysis = {
            "session_id": session_id,
            "latest_thought_number": latest_thought["thoughtNumber"],
            "total_thoughts_planned": latest_thought["totalThoughts"],
            "next_thought_needed": latest_thought["nextThoughtNeeded"],
            "needs_more_thoughts": latest_thought.get("needsMoreThoughts", False)
        }
        
        if analysis_type == "continuation":
            if latest_thought["nextThoughtNeeded"]:
                recommendations.append({
                    "type": "continue",
                    "action": "add_next_thought",
                    "suggested_thought_number": latest_thought["thoughtNumber"] + 1,
                    "reason": "Previous thought indicated more thoughts are needed"
                })
            
            if latest_thought["thoughtNumber"] < latest_thought["totalThoughts"]:
                recommendations.append({
                    "type": "planned_continuation",
                    "action": "complete_planned_thoughts",
                    "remaining_thoughts": latest_thought["totalThoughts"] - latest_thought["thoughtNumber"],
                    "reason": "Session has not reached planned total thoughts"
                })
        
        elif analysis_type == "completion":
            if not latest_thought["nextThoughtNeeded"] and latest_thought["thoughtNumber"] >= latest_thought["totalThoughts"]:
                recommendations.append({
                    "type": "complete",
                    "action": "session_complete",
                    "reason": "Session appears to be complete based on thought indicators"
                })
            else:
                recommendations.append({
                    "type": "incomplete",
                    "action": "needs_conclusion",
                    "reason": "Session may need a concluding thought or summary"
                })
        
        elif analysis_type == "branching":
            # Look for opportunities to branch
            thought_content = latest_thought["thought"].lower()
            
            if any(word in thought_content for word in ["alternative", "however", "but", "different approach", "consider"]):
                recommendations.append({
                    "type": "branch_opportunity",
                    "action": "create_branch",
                    "branch_from_thought": latest_thought["thoughtNumber"],
                    "reason": "Current thought suggests alternative approaches could be explored"
                })
            
            # Check if there are unresolved questions
            if "?" in latest_thought["thought"]:
                recommendations.append({
                    "type": "exploration_branch",
                    "action": "explore_questions",
                    "branch_from_thought": latest_thought["thoughtNumber"],
                    "reason": "Current thought contains questions that could be explored in separate branches"
                })
        
        # General recommendations
        if len(main_thoughts) >= 3:
            recommendations.append({
                "type": "review",
                "action": "review_progress",
                "reason": "Session has multiple thoughts - consider reviewing progress and coherence"
            })
        
        return {
            "session_id": session_id,
            "analysis_type": analysis_type,
            "analysis": analysis,
            "latest_thought": {
                "number": latest_thought["thoughtNumber"],
                "content_preview": latest_thought["thought"][:200] + "..." if len(latest_thought["thought"]) > 200 else latest_thought["thought"]
            },
            "recommendations": recommendations,
            "total_recommendations": len(recommendations)
        }
        
    except Exception as e:
        raise Exception(f"Failed to analyze thought chain for session '{session_id}': {str(e)}") from e

def validate_thought_data(input_data: Dict) -> Dict:
    """Validate thought data structure."""
    if not input_data.get("sessionId"):
        raise ValueError("Invalid sessionId: must be provided")
    if not input_data.get("thought") or not isinstance(input_data.get("thought"), str):
        raise ValueError("Invalid thought: must be a string")
    if not input_data.get("thoughtNumber") or not isinstance(input_data.get("thoughtNumber"), int):
            raise ValueError("Invalid thoughtNumber: must be a number")
    if not input_data.get("totalThoughts") or not isinstance(input_data.get("totalThoughts"), int):
        raise ValueError("Invalid totalThoughts: must be a number")
    if not isinstance(input_data.get("nextThoughtNeeded"), bool):
        raise ValueError("Invalid nextThoughtNeeded: must be a boolean")
        
    return {
        "sessionId": input_data.get("sessionId"),
        "thought": input_data.get("thought"),
        "thoughtNumber": input_data.get("thoughtNumber"),
        "totalThoughts": input_data.get("totalThoughts"),
        "nextThoughtNeeded": input_data.get("nextThoughtNeeded"),
        "isRevision": input_data.get("isRevision"),
        "revisesThought": input_data.get("revisesThought"),
        "branchFromThought": input_data.get("branchFromThought"),
        "branchId": input_data.get("branchId"),
        "needsMoreThoughts": input_data.get("needsMoreThoughts"),
    }
    
def process_thought(input_data: Dict) -> Dict:
    """Process a new thought and store it in ChromaDB."""
    import time
    from datetime import datetime
    
    try:
        # Validate input data
        validated_input = validate_thought_data(input_data)
            
        # Adjust total thoughts if needed
        if validated_input["thoughtNumber"] > validated_input["totalThoughts"]:
            validated_input["totalThoughts"] = validated_input["thoughtNumber"]
        
        # Get ChromaDB client
        client = get_chroma_client()
        
        # Get or create collections
        try:
            thoughts_collection = client.get_collection("sequential_thoughts")
        except Exception:
            thoughts_collection = client.create_collection(
                name="sequential_thoughts",
                metadata={"hnsw:space": "cosine"}
            )
        
        try:
            sessions_collection = client.get_collection("thought_sessions")
        except Exception:
            sessions_collection = client.create_collection(
                name="thought_sessions",
                metadata={"hnsw:space": "cosine"}
            )
        
        # Prepare thought metadata
        timestamp = datetime.now().isoformat()
        thought_metadata = {
            "sessionId": validated_input["sessionId"],
            "thoughtNumber": validated_input["thoughtNumber"],
            "totalThoughts": validated_input["totalThoughts"],
            "nextThoughtNeeded": validated_input["nextThoughtNeeded"],
            "timestamp": timestamp
        }
        
        # Add optional metadata fields (only if not None)
        for field in ["isRevision", "revisesThought", "branchFromThought", "branchId", "needsMoreThoughts"]:
            value = validated_input.get(field)
            if value is not None:
                thought_metadata[field] = value
        
        # Generate unique thought ID
        thought_id = f"{validated_input['sessionId']}_{validated_input['thoughtNumber']}"
        if validated_input.get("branchId"):
            thought_id += f"_{validated_input['branchId']}"
        
        # Store the thought in the thoughts collection
        thoughts_collection.upsert(
            ids=[thought_id],
            documents=[validated_input["thought"]],
            metadatas=[thought_metadata]
        )
        
        # Update or create session record
        session_id = validated_input["sessionId"]
        
        # Check if session already exists
        try:
            existing_sessions = sessions_collection.get(
                ids=[session_id],
                include=["metadatas"]
            )
            
            if existing_sessions["ids"]:
                # Update existing session
                existing_metadata = existing_sessions["metadatas"][0]
                session_metadata = {
                    "sessionId": session_id,
                    "thoughtCount": max(existing_metadata.get("thoughtCount", 0), validated_input["thoughtNumber"]),
                    "totalThoughts": validated_input["totalThoughts"],
                    "lastThought": validated_input["thoughtNumber"],
                    "lastUpdated": timestamp,
                    "hasRevisions": existing_metadata.get("hasRevisions", False) or bool(validated_input.get("isRevision")),
                    "hasBranches": existing_metadata.get("hasBranches", False) or bool(validated_input.get("branchId"))
                }
            else:
                # Create new session
                session_metadata = {
                    "sessionId": session_id,
                    "thoughtCount": validated_input["thoughtNumber"],
                    "totalThoughts": validated_input["totalThoughts"],
                    "lastThought": validated_input["thoughtNumber"],
                    "created": timestamp,
                    "lastUpdated": timestamp,
                    "hasRevisions": bool(validated_input.get("isRevision")),
                    "hasBranches": bool(validated_input.get("branchId"))
                }
            
            # Store session summary (placeholder - could be improved with actual summary)
            session_summary = f"Sequential thinking session with {session_metadata['thoughtCount']} thoughts"
            
            sessions_collection.upsert(
                ids=[session_id],
                documents=[session_summary],
                metadatas=[session_metadata]
            )
            
        except Exception as e:
            # Log but don't fail if session update fails
            # Log to file only - stderr breaks MCP protocol
            logger.warning(f"Failed to update session record: {str(e)}")
        
        # Return response
        return {
            "sessionId": validated_input["sessionId"],
            "thoughtNumber": validated_input["thoughtNumber"],
            "totalThoughts": validated_input["totalThoughts"],
            "nextThoughtNeeded": validated_input["nextThoughtNeeded"],
            "persistedId": thought_id,
            "timestamp": timestamp
            }
            
    except Exception as e:
        return {
            "error": str(e),
            "status": "failed"
        }

def main():
    """Entry point for the Chroma MCP server."""
    parser = create_parser()
    args = parser.parse_args()
    
    if args.dotenv_path:
        load_dotenv(dotenv_path=args.dotenv_path)
        # re-parse args to read the updated environment variables
        parser = create_parser()
        args = parser.parse_args()
    
    # Validate required arguments based on client type
    if args.client_type == 'http':
        if not args.host:
            parser.error("Host must be provided via --host flag or CHROMA_HOST environment variable when using HTTP client")
    
    elif args.client_type == 'cloud':
        if not args.tenant:
            parser.error("Tenant must be provided via --tenant flag or CHROMA_TENANT environment variable when using cloud client")
        if not args.database:
            parser.error("Database must be provided via --database flag or CHROMA_DATABASE environment variable when using cloud client")
        if not args.api_key:
            parser.error("API key must be provided via --api-key flag or CHROMA_API_KEY environment variable when using cloud client")
    
    # Initialize client with parsed args
    try:
        get_chroma_client(args)
        # Log to file only - stderr breaks MCP protocol
        logger.info("Successfully initialized Chroma client")
    except Exception as e:
        # Log to file only - stderr breaks MCP protocol
        logger.error(f"Failed to initialize Chroma client: {str(e)}")
        raise
    
    # Initialize and run the server
    # Log to file only - stderr breaks MCP protocol
    logger.info("Starting MCP server")
    mcp.run(transport='stdio')
    
if __name__ == "__main__":
    main()
