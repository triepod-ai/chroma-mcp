from typing import Dict, List, Optional, Any, Annotated
from enum import Enum
import chromadb
from mcp.server.fastmcp import Context, FastMCP
from pydantic import Field
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

# Ensure stdout and stderr are properly configured for MCP protocol
import sys
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)


class ChromaSettings:
    """Settings for Chroma client configuration."""
    def __init__(self, args):
        self.client_type = args.client_type
        self.data_dir = args.data_dir
        self.host = args.host
        self.port = args.port
        self.custom_auth_credentials = args.custom_auth_credentials
        self.tenant = args.tenant
        self.database = args.database
        self.api_key = args.api_key
        self.ssl = args.ssl
        self.dotenv_path = args.dotenv_path


class ChromaConnector:
    """Business logic layer for ChromaDB operations."""

    def __init__(self, settings: ChromaSettings):
        self.settings = settings
        self.client = None
        self._initialize_client()

    def _initialize_client(self):
        """Initialize ChromaDB client based on settings."""
        # Load environment variables from .env file if it exists
        load_dotenv(dotenv_path=self.settings.dotenv_path)
        # Log to file only - stderr breaks MCP protocol
        logger.info(f"Loading environment from: {self.settings.dotenv_path}")

        if self.settings.client_type == 'http':
            if not self.settings.host:
                raise ValueError("Host must be provided via --host flag or CHROMA_HOST environment variable when using HTTP client")

            settings = Settings()
            if self.settings.custom_auth_credentials:
                settings = Settings(
                    chroma_client_auth_provider="chromadb.auth.basic_authn.BasicAuthClientProvider",
                    chroma_client_auth_credentials=self.settings.custom_auth_credentials
                )

            # Handle SSL configuration with retry and fallback
            try:
                self.client = chromadb.HttpClient(
                    host=self.settings.host,
                    port=self.settings.port if self.settings.port else None,
                    ssl=self.settings.ssl,
                    settings=settings
                )
                # Test the connection
                self.client.heartbeat()
                logger.info(f"Successfully connected to Chroma HTTP server at {self.settings.host}:{self.settings.port}")
            except ssl.SSLError as e:
                # Log to file only - stderr breaks MCP protocol
                logger.error(f"SSL connection failed: {str(e)}")
                raise
            except Exception as e:
                # Log to file only - stderr breaks MCP protocol
                logger.error(f"Error connecting to HTTP client: {str(e)}")
                logger.error("This may be due to API version mismatch or network issues")
                raise

        elif self.settings.client_type == 'cloud':
            if not self.settings.tenant:
                raise ValueError("Tenant must be provided via --tenant flag or CHROMA_TENANT environment variable when using cloud client")
            if not self.settings.database:
                raise ValueError("Database must be provided via --database flag or CHROMA_DATABASE environment variable when using cloud client")
            if not self.settings.api_key:
                raise ValueError("API key must be provided via --api-key flag or CHROMA_API_KEY environment variable when using cloud client")

            try:
                self.client = chromadb.HttpClient(
                    host="api.trychroma.com",
                    ssl=True,  # Always use SSL for cloud
                    tenant=self.settings.tenant,
                    database=self.settings.database,
                    headers={
                        'x-chroma-token': self.settings.api_key
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

        elif self.settings.client_type == 'persistent':
            if not self.settings.data_dir:
                # Use current working directory if data_dir is not provided
                self.settings.data_dir = "./chroma_data"
            try:
                self.client = chromadb.PersistentClient(path=self.settings.data_dir)
                logger.info(f"Successfully created persistent client with data dir: {self.settings.data_dir}")
            except Exception as e:
                # Log to file only - stderr breaks MCP protocol
                logger.error(f"Error creating persistent client: {str(e)}")
                raise

        elif self.settings.client_type == 'ephemeral':
            try:
                self.client = chromadb.EphemeralClient()
                logger.info("Successfully created ephemeral client")
            except Exception as e:
                # Log to file only - stderr breaks MCP protocol
                logger.error(f"Error creating ephemeral client: {str(e)}")
                raise
        else:
            raise ValueError(f"Unsupported client type: {self.settings.client_type}")

    # Known embedding functions mapping
    _known_embedding_functions: Dict[str, EmbeddingFunction] = {
        "default": DefaultEmbeddingFunction,
        "cohere": CohereEmbeddingFunction,
        "openai": OpenAIEmbeddingFunction,
        "jina": JinaEmbeddingFunction,
        "voyageai": VoyageAIEmbeddingFunction,
        "roboflow": RoboflowEmbeddingFunction,
    }

    def list_collections(self, limit: Optional[int] = None, offset: Optional[int] = None) -> List[str]:
        """List all collection names."""
        try:
            colls = self.client.list_collections(limit=limit, offset=offset)
            return [coll.name for coll in colls]
        except Exception as e:
            raise Exception(f"Failed to list collections: {str(e)}") from e

    def create_collection(
        self,
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
        """Create a new collection."""
        try:
            # Get embedding function
            embedding_function = None
            if embedding_function_name in self._known_embedding_functions:
                embedding_function_class = self._known_embedding_functions[embedding_function_name]
                embedding_function = embedding_function_class()

            # Create configuration if HNSW parameters are provided
            configuration = None
            if any([space, ef_construction, ef_search, max_neighbors, num_threads, batch_size, sync_threshold, resize_factor]):
                hnsw_config = CreateHNSWConfiguration(
                    space=space,
                    ef_construction=ef_construction,
                    ef_search=ef_search,
                    max_neighbors=max_neighbors,
                    num_threads=num_threads,
                    batch_size=batch_size,
                    sync_threshold=sync_threshold,
                    resize_factor=resize_factor
                )
                configuration = CreateCollectionConfiguration(hnsw_configuration=hnsw_config)

            # Create the collection
            collection = self.client.create_collection(
                name=collection_name,
                embedding_function=embedding_function,
                configuration=configuration,
                metadata=metadata
            )
            return f"Collection '{collection_name}' created successfully."
        except Exception as e:
            raise Exception(f"Failed to create collection: {str(e)}") from e

    def peek_collection(self, collection_name: str, limit: int = 5) -> Dict:
        """Peek at documents in a collection."""
        try:
            collection = self.client.get_collection(collection_name)
            results = collection.peek(limit=limit)
            # Remove embeddings to avoid serialization issues
            if 'embeddings' in results:
                del results['embeddings']
            return results
        except Exception as e:
            raise Exception(f"Failed to peek collection '{collection_name}': {str(e)}") from e

    def get_collection_info(self, collection_name: str) -> Dict:
        """Get information about a collection."""
        try:
            collection = self.client.get_collection(collection_name)
            info = {
                'name': collection.name,
                'id': collection.id,
                'metadata': collection.metadata,
                'count': collection.count()
            }
            return info
        except Exception as e:
            raise Exception(f"Failed to get collection info '{collection_name}': {str(e)}") from e

    def get_collection_count(self, collection_name: str) -> int:
        """Get document count in a collection."""
        try:
            collection = self.client.get_collection(collection_name)
            return collection.count()
        except Exception as e:
            raise Exception(f"Failed to get collection count '{collection_name}': {str(e)}") from e

    def modify_collection(
        self,
        collection_name: str,
        new_name: Optional[str] = None,
        new_metadata: Optional[Dict] = None,
        ef_search: Optional[int] = None,
        num_threads: Optional[int] = None,
        batch_size: Optional[int] = None,
        sync_threshold: Optional[int] = None,
        resize_factor: Optional[float] = None
    ) -> str:
        """Modify a collection's name or metadata."""
        try:
            collection = self.client.get_collection(collection_name)

            # Update configuration if HNSW parameters are provided
            if any([ef_search, num_threads, batch_size, sync_threshold, resize_factor]):
                hnsw_config = UpdateHNSWConfiguration(
                    ef_search=ef_search,
                    num_threads=num_threads,
                    batch_size=batch_size,
                    sync_threshold=sync_threshold,
                    resize_factor=resize_factor
                )
                update_config = UpdateCollectionConfiguration(hnsw_configuration=hnsw_config)
                collection.modify(configuration=update_config)

            # Update name and/or metadata if provided
            if new_name or new_metadata:
                collection.modify(name=new_name, metadata=new_metadata)

            return f"Collection '{collection_name}' modified successfully."
        except Exception as e:
            raise Exception(f"Failed to modify collection: {str(e)}") from e

    def fork_collection(self, collection_name: str, new_collection_name: str) -> str:
        """Fork a collection."""
        try:
            # Get source collection
            source_collection = self.client.get_collection(collection_name)

            # Get all documents from source
            all_docs = source_collection.get()

            # Create new collection with same metadata and configuration
            target_collection = self.client.create_collection(
                name=new_collection_name,
                metadata=source_collection.metadata,
                embedding_function=source_collection._embedding_function
            )

            # Add all documents to target collection if source has data
            if all_docs['ids']:
                target_collection.add(
                    ids=all_docs['ids'],
                    documents=all_docs['documents'],
                    metadatas=all_docs['metadatas'],
                    embeddings=all_docs['embeddings']
                )

            return f"Successfully forked collection '{collection_name}' to '{new_collection_name}' with {len(all_docs['ids']) if all_docs['ids'] else 0} documents."
        except Exception as e:
            raise Exception(f"Failed to fork collection: {str(e)}") from e

    def delete_collection(self, collection_name: str) -> str:
        """Delete a collection."""
        try:
            self.client.delete_collection(name=collection_name)
            return f"Collection '{collection_name}' deleted successfully."
        except Exception as e:
            raise Exception(f"Failed to delete collection: {str(e)}") from e

    def add_documents(
        self,
        collection_name: str,
        documents: List[str],
        metadatas: Optional[List[Dict]] = None,
        ids: Optional[List[str]] = None
    ) -> str:
        """Add documents to a collection."""
        try:
            collection = self.client.get_collection(collection_name)

            # Generate IDs if not provided
            if ids is None:
                ids = [str(uuid.uuid4()) for _ in documents]

            collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            return f"Added {len(documents)} documents to collection '{collection_name}'."
        except Exception as e:
            raise Exception(f"Failed to add documents: {str(e)}") from e

    def query_documents(
        self,
        collection_name: str,
        query_texts: List[str],
        n_results: int = 5,
        where: Optional[Dict] = None,
        where_document: Optional[Dict] = None,
        include: List[str] = ["documents", "metadatas", "distances"]
    ) -> Dict:
        """Query documents from a collection."""
        try:
            collection = self.client.get_collection(collection_name)
            results = collection.query(
                query_texts=query_texts,
                n_results=n_results,
                where=where,
                where_document=where_document,
                include=include
            )
            return results
        except Exception as e:
            raise Exception(f"Failed to query documents: {str(e)}") from e

    def get_documents(
        self,
        collection_name: str,
        ids: Optional[List[str]] = None,
        where: Optional[Dict] = None,
        where_document: Optional[Dict] = None,
        include: List[str] = ["documents", "metadatas"],
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> Dict:
        """Get documents from a collection."""
        try:
            collection = self.client.get_collection(collection_name)
            results = collection.get(
                ids=ids,
                where=where,
                where_document=where_document,
                include=include,
                limit=limit,
                offset=offset
            )
            return results
        except Exception as e:
            raise Exception(f"Failed to get documents: {str(e)}") from e

    def update_documents(
        self,
        collection_name: str,
        ids: List[str],
        embeddings: Optional[List[List[float]]] = None,
        metadatas: Optional[List[Dict]] = None,
        documents: Optional[List[str]] = None
    ) -> str:
        """Update documents in a collection."""
        try:
            if not ids:
                raise ValueError("'ids' parameter cannot be empty")

            if not any([embeddings, metadatas, documents]):
                raise ValueError("At least one of 'embeddings', 'metadatas', or 'documents' must be provided")

            # Validate lengths match if provided
            if embeddings and len(embeddings) != len(ids):
                raise ValueError(f"Length of 'embeddings' ({len(embeddings)}) must match length of 'ids' ({len(ids)})")
            if metadatas and len(metadatas) != len(ids):
                raise ValueError(f"Length of 'metadatas' ({len(metadatas)}) must match length of 'ids' ({len(ids)})")
            if documents and len(documents) != len(ids):
                raise ValueError(f"Length of 'documents' ({len(documents)}) must match length of 'ids' ({len(ids)})")

            collection = self.client.get_collection(collection_name)
            collection.update(
                ids=ids,
                embeddings=embeddings,
                metadatas=metadatas,
                documents=documents
            )
            return f"Updated {len(ids)} documents in collection '{collection_name}'."
        except Exception as e:
            raise Exception(f"Failed to update documents: {str(e)}") from e

    def delete_documents(self, collection_name: str, ids: List[str]) -> str:
        """Delete documents from a collection."""
        try:
            if not ids:
                raise ValueError("'ids' parameter cannot be empty")

            collection = self.client.get_collection(collection_name)
            collection.delete(ids=ids)
            return f"Deleted {len(ids)} documents from collection '{collection_name}'."
        except Exception as e:
            raise Exception(f"Failed to delete documents: {str(e)}") from e

    # Sequential thinking methods
    def sequential_thinking(
        self,
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
        """Store and process a sequential thought."""
        try:
            # Generate session_id if not provided
            if session_id is None:
                session_id = str(uuid.uuid4())

            # Generate branch_id if branching but not provided
            if branch_from_thought is not None and branch_id is None:
                branch_id = str(uuid.uuid4())[:8]

            # Create or get the sequential thinking collection
            collection_name = "sequential_thinking"
            try:
                collection = self.client.get_collection(collection_name)
            except:
                collection = self.client.create_collection(
                    name=collection_name,
                    metadata={"description": "Sequential thinking sessions with branching and revision support"}
                )

            # Create document ID
            doc_id = f"{session_id}_{thought_number}"
            if branch_id:
                doc_id += f"_branch_{branch_id}"
            if is_revision:
                doc_id += f"_rev_{int(time.time())}"

            # Create metadata
            metadata = {
                "session_id": session_id,
                "thought_number": thought_number,
                "total_thoughts": total_thoughts,
                "next_thought_needed": next_thought_needed,
                "timestamp": int(time.time()),
                "session_type": "sequential_thinking"
            }

            # Add optional metadata
            if is_revision is not None:
                metadata["is_revision"] = is_revision
            if revises_thought is not None:
                metadata["revises_thought"] = revises_thought
            if branch_from_thought is not None:
                metadata["branch_from_thought"] = branch_from_thought
            if branch_id is not None:
                metadata["branch_id"] = branch_id
            if session_summary is not None:
                metadata["session_summary"] = session_summary
            if key_thoughts is not None:
                metadata["key_thoughts"] = json.dumps(key_thoughts)
            if needs_more_thoughts is not None:
                metadata["needs_more_thoughts"] = needs_more_thoughts

            # Add the thought to the collection
            collection.add(
                ids=[doc_id],
                documents=[thought],
                metadatas=[metadata]
            )

            return {
                "session_id": session_id,
                "document_id": doc_id,
                "thought_number": thought_number,
                "branch_id": branch_id,
                "status": "stored",
                "collection": collection_name,
                "metadata": metadata
            }
        except Exception as e:
            raise Exception(f"Failed to store sequential thought: {str(e)}") from e

    def get_similar_sessions(
        self,
        session_type: Optional[str] = None,
        min_thought_count: Optional[int] = None,
        max_thought_count: Optional[int] = None,
        query_text: Optional[str] = None,
        n_results: int = 5
    ) -> Dict:
        """Find similar sequential thinking sessions."""
        try:
            collection_name = "sequential_thinking"
            try:
                collection = self.client.get_collection(collection_name)
            except:
                return {"sessions": [], "message": "No sequential thinking collection found"}

            # Build where filter
            where = {}
            if session_type:
                where["session_type"] = session_type

            # If query_text provided, use semantic search
            if query_text:
                results = collection.query(
                    query_texts=[query_text],
                    n_results=n_results,
                    where=where if where else None,
                    include=["documents", "metadatas", "distances"]
                )
            else:
                # Get all matching documents
                results = collection.get(
                    where=where if where else None,
                    include=["documents", "metadatas"]
                )

            # Group by session and apply filters
            sessions = {}
            if results["ids"]:
                for i, doc_id in enumerate(results["ids"]):
                    metadata = results["metadatas"][i] if results["metadatas"] else {}
                    session_id = metadata.get("session_id")
                    if session_id:
                        if session_id not in sessions:
                            sessions[session_id] = {
                                "session_id": session_id,
                                "thoughts": [],
                                "total_thoughts": metadata.get("total_thoughts", 0),
                                "session_type": metadata.get("session_type", "unknown")
                            }
                        sessions[session_id]["thoughts"].append({
                            "document_id": doc_id,
                            "thought_number": metadata.get("thought_number"),
                            "content": results["documents"][i] if results["documents"] else "",
                            "metadata": metadata
                        })

            # Apply count filters
            filtered_sessions = []
            for session in sessions.values():
                thought_count = len(session["thoughts"])
                if min_thought_count and thought_count < min_thought_count:
                    continue
                if max_thought_count and thought_count > max_thought_count:
                    continue
                filtered_sessions.append(session)

            # Sort by relevance if semantic search, otherwise by total thoughts
            if query_text and "distances" in results:
                # Sort by best match
                pass  # Already ordered by similarity
            else:
                filtered_sessions.sort(key=lambda x: x["total_thoughts"], reverse=True)

            return {
                "sessions": filtered_sessions[:n_results],
                "total_found": len(filtered_sessions)
            }
        except Exception as e:
            raise Exception(f"Failed to get similar sessions: {str(e)}") from e

    def get_thought_history(
        self,
        session_id: str,
        include_branches: bool = True,
        sort_by_number: bool = True
    ) -> Dict:
        """Retrieve complete thought history for a session."""
        try:
            collection_name = "sequential_thinking"
            try:
                collection = self.client.get_collection(collection_name)
            except:
                return {"thoughts": [], "message": "No sequential thinking collection found"}

            # Get all thoughts for the session
            results = collection.get(
                where={"session_id": session_id},
                include=["documents", "metadatas"]
            )

            if not results["ids"]:
                return {"thoughts": [], "session_id": session_id, "message": "No thoughts found for this session"}

            # Process thoughts
            thoughts = []
            for i, doc_id in enumerate(results["ids"]):
                metadata = results["metadatas"][i] if results["metadatas"] else {}

                # Skip branches if not including them
                if not include_branches and metadata.get("branch_id"):
                    continue

                thought = {
                    "document_id": doc_id,
                    "content": results["documents"][i] if results["documents"] else "",
                    "thought_number": metadata.get("thought_number"),
                    "timestamp": metadata.get("timestamp"),
                    "is_revision": metadata.get("is_revision", False),
                    "branch_id": metadata.get("branch_id"),
                    "metadata": metadata
                }
                thoughts.append(thought)

            # Sort thoughts
            if sort_by_number:
                thoughts.sort(key=lambda x: (x["thought_number"] or 0, x["timestamp"] or 0))

            return {
                "session_id": session_id,
                "thoughts": thoughts,
                "total_thoughts": len(thoughts),
                "has_branches": any(t["branch_id"] for t in thoughts)
            }
        except Exception as e:
            raise Exception(f"Failed to get thought history: {str(e)}") from e

    def get_thought_branches(
        self,
        session_id: str,
        thought_number: Optional[int] = None
    ) -> Dict:
        """Retrieve branches stemming from a session or specific thought."""
        try:
            collection_name = "sequential_thinking"
            try:
                collection = self.client.get_collection(collection_name)
            except:
                return {"branches": [], "message": "No sequential thinking collection found"}

            # Get all thoughts for the session
            where_filter = {"session_id": session_id}
            if thought_number is not None:
                where_filter["branch_from_thought"] = thought_number

            results = collection.get(
                where=where_filter,
                include=["documents", "metadatas"]
            )

            # Group by branch_id
            branches = {}
            for i, doc_id in enumerate(results["ids"]):
                metadata = results["metadatas"][i] if results["metadatas"] else {}
                branch_id = metadata.get("branch_id")

                if branch_id:  # Only include actual branches
                    if branch_id not in branches:
                        branches[branch_id] = {
                            "branch_id": branch_id,
                            "branch_from_thought": metadata.get("branch_from_thought"),
                            "thoughts": []
                        }

                    branches[branch_id]["thoughts"].append({
                        "document_id": doc_id,
                        "content": results["documents"][i] if results["documents"] else "",
                        "thought_number": metadata.get("thought_number"),
                        "timestamp": metadata.get("timestamp"),
                        "metadata": metadata
                    })

            # Sort thoughts within each branch
            for branch in branches.values():
                branch["thoughts"].sort(key=lambda x: x["thought_number"] or 0)

            return {
                "session_id": session_id,
                "filter_thought": thought_number,
                "branches": list(branches.values()),
                "total_branches": len(branches)
            }
        except Exception as e:
            raise Exception(f"Failed to get thought branches: {str(e)}") from e

    def continue_thought_chain(
        self,
        session_id: str,
        analysis_type: str = "continuation"
    ) -> Dict:
        """Analyze the last thought and provide continuation suggestions."""
        try:
            # Get the thought history first
            history = self.get_thought_history(session_id, include_branches=False)

            if not history["thoughts"]:
                return {"analysis": "No thoughts found for this session", "suggestions": []}

            # Get the last thought
            last_thought = history["thoughts"][-1]

            # Create analysis based on type
            analysis = {
                "session_id": session_id,
                "last_thought_number": last_thought["thought_number"],
                "last_thought_content": last_thought["content"][:200] + "..." if len(last_thought["content"]) > 200 else last_thought["content"],
                "analysis_type": analysis_type,
                "total_thoughts_so_far": len(history["thoughts"]),
                "suggestions": []
            }

            # Generate suggestions based on analysis type
            if analysis_type == "continuation":
                analysis["suggestions"] = [
                    "Continue developing the main line of reasoning",
                    "Address any remaining questions or gaps",
                    "Consider practical applications or next steps",
                    "Synthesize key insights from previous thoughts"
                ]
            elif analysis_type == "completion":
                analysis["suggestions"] = [
                    "Summarize the key conclusions reached",
                    "Identify the most important insights",
                    "Note any remaining open questions",
                    "Consider the broader implications"
                ]
            elif analysis_type == "branching":
                analysis["suggestions"] = [
                    "Explore an alternative perspective on the topic",
                    "Consider a different approach to the problem",
                    "Examine potential counterarguments",
                    "Investigate a related but distinct aspect"
                ]

            analysis["recommendation"] = f"Based on {len(history['thoughts'])} thoughts in this session, consider {analysis_type} to further develop your reasoning."

            return analysis
        except Exception as e:
            raise Exception(f"Failed to continue thought chain: {str(e)}") from e


class ChromaMCPServer(FastMCP):
    """Chroma MCP server following FastMCP template pattern."""

    def __init__(
        self,
        settings: ChromaSettings,
        name: str = "chroma",
        instructions: str | None = None,
        **kwargs: Any,
    ):
        # Critical 4-step initialization order from FastMCP template
        try:
            # 1. Store settings
            self.settings = settings

            # 2. Initialize business logic layer
            self.connector = ChromaConnector(settings)

            # 3. Initialize FastMCP parent
            super().__init__(name=name, instructions=instructions, **kwargs)

            # 4. Setup tools AFTER FastMCP initialization
            self.setup_tools()

        except Exception as e:
            logger.error(f"Failed to initialize ChromaMCPServer: {str(e)}")
            raise

    def setup_tools(self):
        """Setup all MCP tools - The Working Magic from FastMCP template."""

        # Test function
        async def test_mcp_response(
            ctx: Context
        ) -> str:
            """Test function to verify MCP responses are working.

            Returns:
                Simple test message to confirm output is visible
            """
            await ctx.debug("Testing MCP response functionality")
            return "MCP response test successful! If you can see this, tool responses are working."

        # List collections
        async def chroma_list_collections(
            ctx: Context,
            limit: Annotated[Optional[int], Field(default=None, description="Optional maximum number of collections to return")] = None,
            offset: Annotated[Optional[int], Field(default=None, description="Optional number of collections to skip before returning results")] = None
        ) -> List[str]:
            """List all collection names in the Chroma database with pagination support.

            Args:
                limit: Optional maximum number of collections to return
                offset: Optional number of collections to skip before returning results

            Returns:
                List of collection names
            """
            await ctx.debug(f"Listing collections with limit={limit}, offset={offset}")
            return self.connector.list_collections(limit, offset)

        # Create collection
        async def chroma_create_collection(
            ctx: Context,
            collection_name: Annotated[str, Field(description="Name of the collection to create")],
            space: Annotated[Optional[str], Field(default=None, description="Distance function used in HNSW index. Options: 'l2', 'ip', 'cosine'")] = None,
            ef_construction: Annotated[Optional[int], Field(default=None, description="Size of the dynamic candidate list for constructing the HNSW graph")] = None,
            ef_search: Annotated[Optional[int], Field(default=None, description="Size of the dynamic candidate list for searching the HNSW graph")] = None,
            max_neighbors: Annotated[Optional[int], Field(default=None, description="Maximum number of neighbors to consider during HNSW graph construction")] = None,
            num_threads: Annotated[Optional[int], Field(default=None, description="Number of threads to use during HNSW construction")] = None,
            batch_size: Annotated[Optional[int], Field(default=None, description="Number of elements to batch together during index construction")] = None,
            sync_threshold: Annotated[Optional[int], Field(default=None, description="Number of elements to process before syncing index to disk")] = None,
            resize_factor: Annotated[Optional[float], Field(default=None, description="Factor to resize the index by when it's full")] = None,
            embedding_function_name: Annotated[Optional[str], Field(default="default", description="Name of the embedding function to use. Options: 'default', 'cohere', 'openai', 'jina', 'voyageai', 'ollama', 'roboflow'")] = "default",
            metadata: Annotated[Optional[Dict], Field(default=None, description="Optional metadata dict to add to the collection")] = None
        ) -> str:
            """Create a new Chroma collection with configurable HNSW parameters."""
            await ctx.debug(f"Creating collection: {collection_name}")
            return self.connector.create_collection(
                collection_name=collection_name,
                embedding_function_name=embedding_function_name,
                metadata=metadata,
                space=space,
                ef_construction=ef_construction,
                ef_search=ef_search,
                max_neighbors=max_neighbors,
                num_threads=num_threads,
                batch_size=batch_size,
                sync_threshold=sync_threshold,
                resize_factor=resize_factor
            )

        # Peek collection
        async def chroma_peek_collection(
            ctx: Context,
            collection_name: Annotated[str, Field(description="Name of the collection to peek into")],
            limit: Annotated[int, Field(default=5, description="Number of documents to peek at")] = 5
        ) -> Dict:
            """Peek at documents in a Chroma collection."""
            await ctx.debug(f"Peeking collection: {collection_name}")
            return self.connector.peek_collection(collection_name, limit)

        # Get collection info
        async def chroma_get_collection_info(
            ctx: Context,
            collection_name: Annotated[str, Field(description="Name of the collection to get info about")]
        ) -> Dict:
            """Get information about a Chroma collection."""
            await ctx.debug(f"Getting collection info: {collection_name}")
            return self.connector.get_collection_info(collection_name)

        # Get collection count
        async def chroma_get_collection_count(
            ctx: Context,
            collection_name: Annotated[str, Field(description="Name of the collection to count")]
        ) -> int:
            """Get the number of documents in a Chroma collection."""
            await ctx.debug(f"Getting collection count: {collection_name}")
            return self.connector.get_collection_count(collection_name)

        # Modify collection
        async def chroma_modify_collection(
            ctx: Context,
            collection_name: Annotated[str, Field(description="Name of the collection to modify")],
            new_name: Annotated[Optional[str], Field(default=None, description="Optional new name for the collection")] = None,
            new_metadata: Annotated[Optional[Dict], Field(default=None, description="Optional new metadata for the collection")] = None,
            ef_search: Annotated[Optional[int], Field(default=None, description="Size of the dynamic candidate list for searching the HNSW graph")] = None,
            num_threads: Annotated[Optional[int], Field(default=None, description="Number of threads to use during HNSW construction")] = None,
            batch_size: Annotated[Optional[int], Field(default=None, description="Number of elements to batch together during index construction")] = None,
            sync_threshold: Annotated[Optional[int], Field(default=None, description="Number of elements to process before syncing index to disk")] = None,
            resize_factor: Annotated[Optional[float], Field(default=None, description="Factor to resize the index by when it's full")] = None
        ) -> str:
            """Modify a Chroma collection's name or metadata."""
            await ctx.debug(f"Modifying collection: {collection_name}")
            return self.connector.modify_collection(
                collection_name, new_name, new_metadata, ef_search, num_threads, batch_size, sync_threshold, resize_factor
            )

        # Fork collection
        async def chroma_fork_collection(
            ctx: Context,
            collection_name: Annotated[str, Field(description="Name of the collection to fork")],
            new_collection_name: Annotated[str, Field(description="Name of the new collection to create")]
        ) -> str:
            """Fork a Chroma collection."""
            await ctx.debug(f"Forking collection: {collection_name} -> {new_collection_name}")
            return self.connector.fork_collection(collection_name, new_collection_name)

        # Delete collection
        async def chroma_delete_collection(
            ctx: Context,
            collection_name: Annotated[str, Field(description="Name of the collection to delete")]
        ) -> str:
            """Delete a Chroma collection."""
            await ctx.debug(f"Deleting collection: {collection_name}")
            return self.connector.delete_collection(collection_name)

        # Add documents
        async def chroma_add_documents(
            ctx: Context,
            collection_name: Annotated[str, Field(description="Name of the collection to add documents to")],
            documents: Annotated[List[str], Field(description="List of text documents to add")],
            metadatas: Annotated[Optional[List[Dict]], Field(default=None, description="Optional list of metadata dictionaries for each document")] = None,
            ids: Annotated[Optional[List[str]], Field(default=None, description="Optional list of IDs for the documents")] = None
        ) -> str:
            """Add documents to a Chroma collection."""
            await ctx.debug(f"Adding {len(documents)} documents to collection: {collection_name}")
            return self.connector.add_documents(collection_name, documents, metadatas, ids)

        # Query documents
        async def chroma_query_documents(
            ctx: Context,
            collection_name: Annotated[str, Field(description="Name of the collection to query")],
            query_texts: Annotated[List[str], Field(description="List of query texts to search for")],
            n_results: Annotated[int, Field(default=5, description="Number of results to return per query")] = 5,
            where: Annotated[Optional[Dict], Field(default=None, description="Optional metadata filters using Chroma's query operators")] = None,
            where_document: Annotated[Optional[Dict], Field(default=None, description="Optional document content filters")] = None,
            include: Annotated[List[str], Field(default=["documents", "metadatas", "distances"], description="List of what to include in response")] = ["documents", "metadatas", "distances"]
        ) -> Dict:
            """Query documents from a Chroma collection with advanced filtering."""
            await ctx.debug(f"Querying collection: {collection_name}")
            return self.connector.query_documents(collection_name, query_texts, n_results, where, where_document, include)

        # Get documents
        async def chroma_get_documents(
            ctx: Context,
            collection_name: Annotated[str, Field(description="Name of the collection to get documents from")],
            ids: Annotated[Optional[List[str]], Field(default=None, description="Optional list of document IDs to retrieve")] = None,
            where: Annotated[Optional[Dict], Field(default=None, description="Optional metadata filters using Chroma's query operators")] = None,
            where_document: Annotated[Optional[Dict], Field(default=None, description="Optional document content filters")] = None,
            include: Annotated[List[str], Field(default=["documents", "metadatas"], description="List of what to include in response")] = ["documents", "metadatas"],
            limit: Annotated[Optional[int], Field(default=None, description="Optional maximum number of documents to return")] = None,
            offset: Annotated[Optional[int], Field(default=None, description="Optional number of documents to skip before returning results")] = None
        ) -> Dict:
            """Get documents from a Chroma collection with optional filtering."""
            await ctx.debug(f"Getting documents from collection: {collection_name}")
            return self.connector.get_documents(collection_name, ids, where, where_document, include, limit, offset)

        # Update documents
        async def chroma_update_documents(
            ctx: Context,
            collection_name: Annotated[str, Field(description="Name of the collection to update documents in")],
            ids: Annotated[List[str], Field(description="List of document IDs to update (required)")],
            embeddings: Annotated[Optional[List[List[float]]], Field(default=None, description="Optional list of new embeddings for the documents")] = None,
            metadatas: Annotated[Optional[List[Dict]], Field(default=None, description="Optional list of new metadata dictionaries for the documents")] = None,
            documents: Annotated[Optional[List[str]], Field(default=None, description="Optional list of new text documents")] = None
        ) -> str:
            """Update documents in a Chroma collection."""
            await ctx.debug(f"Updating {len(ids)} documents in collection: {collection_name}")
            return self.connector.update_documents(collection_name, ids, embeddings, metadatas, documents)

        # Delete documents
        async def chroma_delete_documents(
            ctx: Context,
            collection_name: Annotated[str, Field(description="Name of the collection to delete documents from")],
            ids: Annotated[List[str], Field(description="List of document IDs to delete")]
        ) -> str:
            """Delete documents from a Chroma collection."""
            await ctx.debug(f"Deleting {len(ids)} documents from collection: {collection_name}")
            return self.connector.delete_documents(collection_name, ids)

        # Sequential thinking
        async def chroma_sequential_thinking(
            ctx: Context,
            thought: Annotated[str, Field(description="The thought content as a string")],
            thought_number: Annotated[int, Field(description="Current thought number in the sequence")],
            total_thoughts: Annotated[int, Field(description="Total number of thoughts planned for this session")],
            next_thought_needed: Annotated[bool, Field(description="Whether more thoughts are needed to continue")],
            session_id: Annotated[Optional[str], Field(default=None, description="Optional session identifier (generated if not provided)")] = None,
            is_revision: Annotated[Optional[bool], Field(default=None, description="Whether this thought revises a previous thought")] = None,
            revises_thought: Annotated[Optional[int], Field(default=None, description="Thought number being revised (if is_revision is True)")] = None,
            branch_from_thought: Annotated[Optional[int], Field(default=None, description="Thought number this branches from (for alternative paths)")] = None,
            branch_id: Annotated[Optional[str], Field(default=None, description="Identifier for the branch (generated if not provided)")] = None,
            session_summary: Annotated[Optional[str], Field(default=None, description="Summary of the session (typically provided with final thought)")] = None,
            key_thoughts: Annotated[Optional[List[int]], Field(default=None, description="List of important thought numbers in this session")] = None,
            needs_more_thoughts: Annotated[Optional[bool], Field(default=None, description="Whether the session needs additional thoughts beyond total_thoughts")] = None
        ) -> Dict:
            """Store and process a sequential thought in ChromaDB."""
            await ctx.debug(f"Storing sequential thought #{thought_number}")
            return self.connector.sequential_thinking(
                thought, thought_number, total_thoughts, next_thought_needed, session_id,
                is_revision, revises_thought, branch_from_thought, branch_id,
                session_summary, key_thoughts, needs_more_thoughts
            )

        # Get similar sessions
        async def chroma_get_similar_sessions(
            ctx: Context,
            session_type: Annotated[Optional[str], Field(default=None, description="Optional filter by session type")] = None,
            min_thought_count: Annotated[Optional[int], Field(default=None, description="Minimum number of thoughts in the session")] = None,
            max_thought_count: Annotated[Optional[int], Field(default=None, description="Maximum number of thoughts in the session")] = None,
            query_text: Annotated[Optional[str], Field(default=None, description="Optional text to search for similar session content")] = None,
            n_results: Annotated[int, Field(default=5, description="Number of similar sessions to return")] = 5
        ) -> Dict:
            """Find similar sequential thinking sessions based on metadata and content."""
            await ctx.debug("Finding similar sessions")
            return self.connector.get_similar_sessions(session_type, min_thought_count, max_thought_count, query_text, n_results)

        # Get thought history
        async def chroma_get_thought_history(
            ctx: Context,
            session_id: Annotated[str, Field(description="The session identifier to retrieve thoughts for")],
            include_branches: Annotated[bool, Field(default=True, description="Whether to include thoughts from all branches")] = True,
            sort_by_number: Annotated[bool, Field(default=True, description="Whether to sort thoughts by thought number")] = True
        ) -> Dict:
            """Retrieve the complete thought history for a sequential thinking session."""
            await ctx.debug(f"Getting thought history for session: {session_id}")
            return self.connector.get_thought_history(session_id, include_branches, sort_by_number)

        # Get thought branches
        async def chroma_get_thought_branches(
            ctx: Context,
            session_id: Annotated[str, Field(description="The session identifier to search for branches")],
            thought_number: Annotated[Optional[int], Field(default=None, description="Optional specific thought number to find branches from")] = None
        ) -> Dict:
            """Retrieve all branches that stem from a specific thought or session."""
            await ctx.debug(f"Getting thought branches for session: {session_id}")
            return self.connector.get_thought_branches(session_id, thought_number)

        # Continue thought chain
        async def chroma_continue_thought_chain(
            ctx: Context,
            session_id: Annotated[str, Field(description="The session identifier to analyze")],
            analysis_type: Annotated[str, Field(default="continuation", description="Type of analysis ('continuation', 'completion', 'branching')")] = "continuation"
        ) -> Dict:
            """Analyze the last thought in a session and provide continuation suggestions."""
            await ctx.debug(f"Analyzing thought chain for session: {session_id}")
            return self.connector.continue_thought_chain(session_id, analysis_type)

        # Register all tools with FastMCP
        self.tool(description="Test function to verify MCP responses are working")(test_mcp_response)
        self.tool(description="List all collection names in the Chroma database with pagination support")(chroma_list_collections)
        self.tool(description="Create a new Chroma collection with configurable HNSW parameters")(chroma_create_collection)
        self.tool(description="Peek at documents in a Chroma collection")(chroma_peek_collection)
        self.tool(description="Get information about a Chroma collection")(chroma_get_collection_info)
        self.tool(description="Get the number of documents in a Chroma collection")(chroma_get_collection_count)
        self.tool(description="Modify a Chroma collection's name or metadata")(chroma_modify_collection)
        self.tool(description="Fork a Chroma collection")(chroma_fork_collection)
        self.tool(description="Delete a Chroma collection")(chroma_delete_collection)
        self.tool(description="Add documents to a Chroma collection")(chroma_add_documents)
        self.tool(description="Query documents from a Chroma collection with advanced filtering")(chroma_query_documents)
        self.tool(description="Get documents from a Chroma collection with optional filtering")(chroma_get_documents)
        self.tool(description="Update documents in a Chroma collection")(chroma_update_documents)
        self.tool(description="Delete documents from a Chroma collection")(chroma_delete_documents)
        self.tool(description="Store and process a sequential thought in ChromaDB")(chroma_sequential_thinking)
        self.tool(description="Find similar sequential thinking sessions based on metadata and content")(chroma_get_similar_sessions)
        self.tool(description="Retrieve the complete thought history for a sequential thinking session")(chroma_get_thought_history)
        self.tool(description="Retrieve all branches that stem from a specific thought or session")(chroma_get_thought_branches)
        self.tool(description="Analyze the last thought in a session and provide continuation suggestions")(chroma_continue_thought_chain)


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

    # Create settings object
    settings = ChromaSettings(args)

    # Initialize and run the server following FastMCP template
    try:
        server = ChromaMCPServer(settings)
        logger.info("Successfully initialized ChromaMCPServer")
        logger.info("Starting MCP server")
        server.run(transport='stdio')
    except Exception as e:
        logger.error(f"Failed to initialize or run server: {str(e)}")
        raise


if __name__ == "__main__":
    main()