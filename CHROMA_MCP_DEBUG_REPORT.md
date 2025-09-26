# Chroma MCP Server Debug Report

**Date**: 2025-07-23  
**Issue**: Numpy array serialization error in MCP Chroma server  
**Reporter**: Claude Code (claude.ai/code)  

## 🐛 Problem Summary

Two MCP Chroma server functions are failing with numpy array serialization errors:
- `chroma_peek_collection`
- `chroma_get_collection_info`

## 🔍 Error Details

### Error Message
```
Error executing tool chroma_peek_collection: Unable to serialize unknown type: <class 'numpy.ndarray'>
Error executing tool chroma_get_collection_info: Unable to serialize unknown type: <class 'numpy.ndarray'>
```

### Affected Functions
1. **`chroma_peek_collection`**
   - Parameters: `collection_name: "music_video_blame_it_on_me"`, `limit: 3`
   - Expected: Return sampled documents from collection
   - Actual: Serialization error

2. **`chroma_get_collection_info`**
   - Parameters: `collection_name: "music_video_blame_it_on_me"`
   - Expected: Return collection metadata and configuration
   - Actual: Serialization error

## ✅ Working Functions (Verification)

These MCP Chroma functions work correctly with the same collection:

### `chroma_get_collection_count`
```json
{
  "collection_name": "music_video_blame_it_on_me",
  "result": 68
}
```

### `chroma_query_documents`
```json
{
  "collection_name": "music_video_blame_it_on_me",
  "query_texts": ["dancer"],
  "n_results": 1,
  "include": ["documents", "metadatas"],
  "result": {
    "ids": [["c7b2e0d6-a9c4-4328-8b47-66d3e1a5c8f9"]],
    "metadatas": [[{"duration": "5s", "scene_name": "Ballet in Neon", ...}]],
    "documents": [["Act 1, Scene 3A-2 - Ballet in Neon from \"Blame It on Me\"..."]]
  }
}
```

### `chroma_add_documents`
```json
{
  "result": "Successfully added X documents to collection music_video_blame_it_on_me"
}
```

## 🔧 Collection Details

**Collection Name**: `music_video_blame_it_on_me`  
**Document Count**: 68  
**Embedding Function**: `default` (DefaultEmbeddingFunction)  
**Created**: 2025-07-23  
**Migration Source**: Migrated from Qdrant music_videos collection  

### Sample Document Structure
```json
{
  "id": "002d3a29-9250-4c35-b532-4bfb20f084d1",
  "document": "Act 5, Scene 26 - Parallel Isolation Return (Full Scene)...",
  "metadata": {
    "scene": "Act 5, Scene 26",
    "scene_name": "Parallel Isolation Return",
    "act": 5,
    "duration": "8s",
    "migrated_from": "music_videos",
    "migration_date": "2025-07-23",
    "original_id": "002d3a29-9250-4c35-b532-4bfb20f084d1"
  }
}
```

## 🎯 Root Cause Analysis

The error suggests that `chroma_peek_collection` and `chroma_get_collection_info` are attempting to return numpy arrays (likely embeddings or collection configuration data) that cannot be serialized to JSON for MCP response.

**Likely causes**:
1. **Embeddings in peek response**: `peek_collection` may be including embeddings (numpy arrays) in the response
2. **Collection info structure**: `get_collection_info` may be returning embedding function objects or numpy array configurations
3. **Serialization handler**: Missing numpy array → JSON conversion in these specific functions

## 💡 Suggested Fixes

### Option 1: Exclude embeddings from problematic functions
```python
# In chroma_peek_collection
result = collection.peek(limit=limit)
# Remove or convert numpy arrays before returning
if 'embeddings' in result:
    del result['embeddings']  # or convert to list
```

### Option 2: Add numpy serialization handler
```python
import numpy as np
import json

class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)
```

### Option 3: Use include parameter pattern
```python
# Similar to query_documents, allow controlling what's included
def chroma_peek_collection(collection_name: str, limit: int = 5, 
                          include: List[str] = ["documents", "metadatas"]):
    # Only include requested fields, exclude embeddings by default
```

## 🧪 Test Environment

**System**: WSL2 Ubuntu on Windows  
**Python Version**: 3.11+  
**Chroma Version**: Latest (as of 2025-07-22)  
**MCP Framework**: Latest  
**Collection Type**: Text documents with metadata  
**Embedding Function**: ChromaDB DefaultEmbeddingFunction  

## 📋 Reproduction Steps

1. Create a Chroma collection with documents and metadata
2. Call `chroma_peek_collection` via MCP
3. Observe serialization error
4. Call `chroma_get_collection_info` via MCP  
5. Observe same serialization error
6. Verify other functions work (query_documents, add_documents, etc.)

## 🔍 Additional Context

- Collection was created and populated successfully
- 68 documents migrated without issues
- Queries work perfectly with `include=["documents", "metadatas"]`
- Error only occurs with peek and info functions
- Collection is fully functional for search and retrieval

## ✅ RESOLUTION - FIXED (2025-07-23)

**Status**: ✅ **RESOLVED**  
**Fix Applied**: 2025-07-23  
**Resolution Method**: Container rebuild with numpy array handling  

### 🔧 Solution Implemented

**Root Cause**: ChromaDB's `.peek()` method returns embeddings as numpy arrays that cannot be JSON-serialized for MCP protocol responses.

**Fix Applied**: Modified both functions to remove embeddings before returning:
```python
# Remove embeddings to avoid numpy array serialization issues
# Embeddings are numpy arrays that cannot be JSON serialized for MCP responses
if 'embeddings' in results:
    del results['embeddings']
```

**Files Modified**: 
- `src/chroma_mcp/server.py` (lines 340-347 and 366-371)

**Deployment**: Container rebuilt with `docker-compose build chroma-mcp` to include fixes

### ✅ Verification Results

**✅ `chroma_peek_collection`**:
- Successfully returns 3 sample documents
- JSON serialization: ✅ PASSED
- Data includes: IDs, metadata, documents, data, uris, included
- No numpy array errors

**✅ `chroma_get_collection_info`**:
- Successfully returns collection information  
- Collection count: 73 documents
- Sample documents included without serialization errors
- JSON serialization: ✅ PASSED

### 🎯 Impact

- **Debugging Workflows**: ✅ Fully functional
- **Collection Inspection**: ✅ Complete capability restored  
- **MCP Compatibility**: ✅ All functions now JSON-serialize correctly
- **Data Integrity**: ✅ All essential data preserved (IDs, metadata, documents)
- **Performance**: ✅ No impact, only removes unnecessary embedding data

## 📞 Contact

This report was generated by Claude Code for debugging MCP Chroma server issues. 

**Final Status**: ✅ **RESOLVED** - All MCP Chroma functions now working correctly  
**Environment**: Development/Testing  
**Resolution Date**: 2025-07-23