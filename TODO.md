# Sequential Thinking Features Implementation TODO

## Overview
Implement missing sequential thinking features in chroma-mcp by adding properly registered MCP tools to server.py.

## Tasks

### High Priority - Tool Registration (2-3 hours)

1. **Add chroma_sequential_thinking tool**
   - [ ] Add @mcp.tool() decorator before line 610
   - [ ] Create async function that wraps existing process_thought() helper
   - [ ] Define proper parameters matching sequential_thinking_example.py format
   - [ ] Return structured response with sessionId, thoughtNumber, totalThoughts

2. **Add chroma_get_similar_sessions tool**
   - [ ] Add @mcp.tool() decorator
   - [ ] Implement using ChromaDB query on sessions collection
   - [ ] Search by metadata fields (sessionType, thoughtCount range)
   - [ ] Return list of similar sessions with scores

3. **Add chroma_get_thought_history tool**
   - [ ] Add @mcp.tool() decorator
   - [ ] Query thoughts collection filtered by sessionId
   - [ ] Sort by thoughtNumber
   - [ ] Include revision and branch information

4. **Add chroma_get_thought_branches tool**
   - [ ] Add @mcp.tool() decorator
   - [ ] Query thoughts where branchFromThought equals given thoughtId
   - [ ] Group by branchId
   - [ ] Return tree structure of branches

5. **Add chroma_continue_thought_chain tool**
   - [ ] Add @mcp.tool() decorator
   - [ ] Analyze last thought in session
   - [ ] Generate continuation suggestions
   - [ ] Return next thought recommendations

### Medium Priority - Storage Implementation (1 hour)

6. **Implement ChromaDB storage logic**
   - [ ] Create/get "sequential_thoughts" collection
   - [ ] Create/get "thought_sessions" collection
   - [ ] Store thoughts with proper metadata structure
   - [ ] Implement embedding generation for thought similarity

### Medium Priority - Testing (30 minutes)

7. **Test all sequential thinking tools**
   - [ ] Create test script with sample session
   - [ ] Test thought creation and revision
   - [ ] Test branching functionality
   - [ ] Verify similarity search works
   - [ ] Ensure thought history retrieval is accurate

### Low Priority - Cleanup (15 minutes)

8. **Update http_server.py imports**
   - [ ] Remove imports of non-existent functions
   - [ ] Add imports for newly created tool functions
   - [ ] Ensure HTTP server can access all tools

## Implementation Notes

- All tools should follow the existing pattern in server.py using @mcp.tool() decorator
- Use async functions for consistency
- Leverage existing helper functions (validate_thought_data, process_thought)
- Store data in ChromaDB collections with appropriate metadata
- Follow the API structure shown in sequential_thinking_example.py

## Estimated Time: 2-4 hours total