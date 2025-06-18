#!/usr/bin/env python3
"""
Test script for sequential thinking tools in chroma-mcp.

This script tests all the sequential thinking tools to ensure they work correctly.
"""

import asyncio
import sys
import os

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from chroma_mcp.server import (
    chroma_sequential_thinking,
    chroma_get_similar_sessions, 
    chroma_get_thought_history,
    chroma_get_thought_branches,
    chroma_continue_thought_chain,
    get_chroma_client,
    create_parser
)

async def test_basic_sequential_thinking():
    """Test basic sequential thinking functionality."""
    print("\n=== Testing Basic Sequential Thinking ===")
    
    # Test creating a sequential thought
    result1 = await chroma_sequential_thinking(
        thought="This is the first thought in our test session. We're testing the sequential thinking functionality.",
        thought_number=1,
        total_thoughts=3,
        next_thought_needed=True,
        session_id="test_session_001"
    )
    
    print(f"Thought 1 result: {result1}")
    
    # Test creating a second thought
    result2 = await chroma_sequential_thinking(
        thought="This is the second thought, building on the first. We're verifying that the system can handle multiple thoughts in sequence.",
        thought_number=2,
        total_thoughts=3,
        next_thought_needed=True,
        session_id="test_session_001"
    )
    
    print(f"Thought 2 result: {result2}")
    
    # Test creating a final thought
    result3 = await chroma_sequential_thinking(
        thought="This is the final thought in our test session. We've successfully tested the basic sequential thinking functionality.",
        thought_number=3,
        total_thoughts=3,
        next_thought_needed=False,
        session_id="test_session_001",
        session_summary="Successfully tested basic sequential thinking with three connected thoughts."
    )
    
    print(f"Thought 3 result: {result3}")
    
    return result1["sessionId"]

async def test_thought_revision():
    """Test thought revision functionality."""
    print("\n=== Testing Thought Revision ===")
    
    session_id = "test_revision_001"
    
    # Create initial thought
    await chroma_sequential_thinking(
        thought="Initial approach: Use a simple sorting algorithm.",
        thought_number=1,
        total_thoughts=2,
        next_thought_needed=True,
        session_id=session_id
    )
    
    # Create revision
    result = await chroma_sequential_thinking(
        thought="Revised approach: Use a more efficient merge sort algorithm for better performance.",
        thought_number=1,
        total_thoughts=2,
        next_thought_needed=True,
        session_id=session_id,
        is_revision=True,
        revises_thought=1
    )
    
    print(f"Revision result: {result}")
    return session_id

async def test_thought_branching():
    """Test thought branching functionality."""
    print("\n=== Testing Thought Branching ===")
    
    session_id = "test_branching_001"
    
    # Create main branch thoughts
    await chroma_sequential_thinking(
        thought="We need to solve this problem efficiently.",
        thought_number=1,
        total_thoughts=3,
        next_thought_needed=True,
        session_id=session_id
    )
    
    await chroma_sequential_thinking(
        thought="One approach is to use algorithm A.",
        thought_number=2,
        total_thoughts=3,
        next_thought_needed=True,
        session_id=session_id
    )
    
    # Create branch from thought 2
    result = await chroma_sequential_thinking(
        thought="Alternative approach: Let's explore algorithm B instead.",
        thought_number=2,
        total_thoughts=4,
        next_thought_needed=True,
        session_id=session_id,
        branch_from_thought=2,
        branch_id="algorithm_b_branch"
    )
    
    print(f"Branch result: {result}")
    return session_id

async def test_get_thought_history():
    """Test retrieving thought history."""
    print("\n=== Testing Get Thought History ===")
    
    # Use the session from basic test
    session_id = "test_session_001"
    
    result = await chroma_get_thought_history(
        session_id=session_id,
        include_branches=True,
        sort_by_number=True
    )
    
    print(f"Thought history: {result}")
    return result

async def test_get_thought_branches():
    """Test retrieving thought branches."""
    print("\n=== Testing Get Thought Branches ===")
    
    # Use the session from branching test
    session_id = "test_branching_001"
    
    result = await chroma_get_thought_branches(
        session_id=session_id
    )
    
    print(f"Thought branches: {result}")
    return result

async def test_continue_thought_chain():
    """Test thought chain continuation analysis."""
    print("\n=== Testing Continue Thought Chain ===")
    
    session_id = "test_session_001"
    
    # Test continuation analysis
    result = await chroma_continue_thought_chain(
        session_id=session_id,
        analysis_type="continuation"
    )
    
    print(f"Continuation analysis: {result}")
    
    # Test completion analysis
    result2 = await chroma_continue_thought_chain(
        session_id=session_id,
        analysis_type="completion"
    )
    
    print(f"Completion analysis: {result2}")
    
    return result

async def test_get_similar_sessions():
    """Test finding similar sessions."""
    print("\n=== Testing Get Similar Sessions ===")
    
    # Test without query
    result = await chroma_get_similar_sessions(
        min_thought_count=2,
        n_results=5
    )
    
    print(f"Similar sessions (no query): {result}")
    
    # Test with query
    result2 = await chroma_get_similar_sessions(
        query_text="testing sequential thinking",
        n_results=3
    )
    
    print(f"Similar sessions (with query): {result2}")
    
    return result

async def run_all_tests():
    """Run all sequential thinking tests."""
    print("Starting Sequential Thinking Tools Test Suite")
    print("=" * 60)
    
    try:
        # Initialize ChromaDB client (using persistent client for testing)
        print("Initializing ChromaDB client...")
        
        # Create mock args for client initialization
        parser = create_parser()
        args = parser.parse_args(['--client-type', 'persistent', '--data-dir', './chroma_data'])
        get_chroma_client(args)
        print("ChromaDB client initialized successfully!")
        
        # Test each functionality
        session_id = await test_basic_sequential_thinking()
        revision_session = await test_thought_revision()
        branch_session = await test_thought_branching()
        
        # Test retrieval functions
        await test_get_thought_history()
        await test_get_thought_branches()
        await test_continue_thought_chain()
        await test_get_similar_sessions()
        
        print("\n" + "=" * 60)
        print("All tests completed successfully!")
        print("Sequential thinking tools are working correctly.")
        
    except Exception as e:
        print(f"\nTest failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    # Set up environment for testing
    os.environ.setdefault('CHROMA_CLIENT_TYPE', 'persistent')
    os.environ.setdefault('CHROMA_DATA_DIR', './chroma_data')
    
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)