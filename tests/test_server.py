import pytest
from chroma_mcp.server import get_chroma_client, mcp
import chromadb

def test_get_chroma_client_ephemeral():
    # Test ephemeral client creation
    client = get_chroma_client()
    assert isinstance(client, chromadb.Client)

@pytest.mark.asyncio
async def test_list_collections():
    # Test list_collections tool
    result = await mcp.tools["list_collections"](limit=5)
    assert isinstance(result, list)

@pytest.mark.asyncio
async def test_create_and_delete_collection():
    # Test collection creation and deletion
    collection_name = "test_collection"
    
    # Create collection
    create_result = await mcp.tools["create_collection"](collection_name=collection_name)
    assert isinstance(create_result, str)
    assert "Successfully created collection" in create_result
    
    # Delete collection
    delete_result = await mcp.tools["delete_collection"](collection_name=collection_name)
    assert isinstance(delete_result, str)
    assert "Successfully deleted collection" in delete_result 