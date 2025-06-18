"""
Chroma MCP Sequential Thinking Example

This script demonstrates how to use the Chroma MCP sequential thinking tools
for complex problem-solving and analysis. Sequential thinking allows for
step-by-step reasoning with the ability to revise previous thoughts and
branch into alternative solution paths.
"""

import asyncio
import json
import time
import uuid
from datetime import datetime

# Wrap the MCP tool for sequential thinking
async def sequential_thinking(thought, thought_number, total_thoughts, 
                             next_thought_needed, session_id=None, 
                             is_revision=None, revises_thought=None,
                             branch_from_thought=None, branch_id=None,
                             session_summary=None, key_thoughts=None):
    """
    Wrapper for the chroma_sequential_thinking MCP tool.
    In a real implementation, this would call the actual MCP server.
    """
    print(f"\n=== THOUGHT {thought_number} ===")
    print(thought)
    
    if session_id is None:
        session_id = str(uuid.uuid4())[:8]
    
    # In a real implementation, this would be:
    # result = await client.call_tool("chroma-mcp", "chroma_sequential_thinking", {
    #    "thought": thought,
    #    "thoughtNumber": thought_number,
    #    ...
    # })
    
    # For demonstration, simulate a response
    result = {
        "sessionId": session_id,
        "thoughtNumber": thought_number,
        "totalThoughts": total_thoughts,
        "nextThoughtNeeded": next_thought_needed,
        "persistedId": f"{session_id}_{thought_number}"
    }
    
    if is_revision:
        result["isRevision"] = True
        result["revisesThought"] = revises_thought
    
    if branch_from_thought:
        result["branchFromThought"] = branch_from_thought
        result["branchId"] = branch_id or f"branch_{int(time.time())}"
    
    if not next_thought_needed and session_summary:
        result["summary"] = {
            "content": session_summary,
            "version": 1
        }
    
    print(f"\n[Result: {json.dumps(result, indent=2)}]")
    return result

async def run_algorithm_design_session():
    """
    Run a sequential thinking session for algorithm design.
    This example tackles a sorting algorithm selection problem.
    """
    print("\n" + "=" * 80)
    print(" SEQUENTIAL THINKING: ALGORITHM DESIGN PROBLEM ".center(80, "="))
    print("=" * 80 + "\n")
    
    session_id = f"sorting_problem_{str(uuid.uuid4())[:8]}"
    print(f"Session ID: {session_id}")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # The problem statement
    problem = """
    Problem: Design an efficient algorithm to sort a large dataset of customer transactions
    with the following characteristics:
    - Approximately 10 million records
    - Each record contains customer ID, timestamp, transaction amount, and category
    - The dataset needs to be sorted by multiple criteria (e.g., first by customer ID,
      then by timestamp)
    - New transactions are periodically added in small batches (100-1000 records)
    - The system needs to output the sorted data frequently

    Design an efficient sorting approach for this scenario.
    """
    
    print("\nPROBLEM STATEMENT:")
    print(problem)
    
    # Thought 1: Initial analysis of the problem
    thought1 = """
    First, I need to analyze the characteristics of this sorting problem:
    
    1. Large dataset (10M records) - This suggests we need an efficient algorithm with good average-case performance
    2. Multiple sort criteria - We need to sort by customer ID first, then timestamp
    3. Incremental updates - New data is added in small batches
    4. Frequent output needs - The sorted data needs to be accessible often
    
    Standard sorting algorithms to consider:
    - Quick Sort: O(n log n) average case, but O(n²) worst case
    - Merge Sort: Stable O(n log n) in all cases, but requires additional space
    - Heap Sort: O(n log n) in all cases, in-place but not stable
    - Insertion Sort: O(n²) but efficient for small or nearly sorted data
    
    Given the characteristics, I need to consider both the initial sort and the strategy
    for handling incremental updates efficiently.
    """
    
    result1 = await sequential_thinking(
        thought=thought1,
        thought_number=1,
        total_thoughts=5,
        next_thought_needed=True,
        session_id=session_id
    )
    
    # Thought 2: Exploring initial sorting approaches
    thought2 = """
    For the initial sort of 10M records, we need an efficient algorithm. Let's evaluate options:
    
    1. Merge Sort:
       - Advantages: Stable, guaranteed O(n log n) performance
       - Disadvantages: Requires O(n) extra space
       
    2. Quick Sort:
       - Advantages: In-place, usually faster constants than merge sort
       - Disadvantages: Worst-case O(n²), not stable
       
    3. External sorting:
       - Given the large dataset, we might need to consider disk-based approaches
       - Could use a B-tree or similar disk-friendly data structure
    
    For the incremental updates, possibilities include:
    1. Rebuild the entire sorted dataset (inefficient for frequent updates)
    2. Insert new elements into the proper position (O(n) per element)
    3. Maintain a separate "new elements" list and periodically merge
    
    I'm leaning toward a hybrid approach: use merge sort for the initial load,
    then maintain a balanced tree structure (e.g., B+ tree or similar) for 
    efficient insertions and range queries.
    """
    
    result2 = await sequential_thinking(
        thought=thought2,
        thought_number=2,
        total_thoughts=5,
        next_thought_needed=True,
        session_id=session_id
    )
    
    # Thought 3: Refining the solution with database concepts
    thought3 = """
    Upon further reflection, this problem strongly resembles database indexing challenges.
    
    Instead of implementing a custom sorting algorithm, a more practical approach would be:
    
    1. Store the data in a database system (relational or NoSQL) that supports indexing
    2. Create a composite index on (customer_id, timestamp)
    3. For writes:
       - New transactions are inserted with standard B-tree index updates (O(log n))
    4. For reads:
       - Queries utilize the index for efficient sorted retrieval
    
    This approach has several advantages:
    - Mature database systems have optimized B-tree implementations
    - Transactions can be added incrementally with O(log n) cost
    - Range queries are efficient
    - The database handles concurrency and persistence
    
    A specific implementation could use:
    - PostgreSQL with a properly indexed table
    - A specialized time-series database if the timestamp is the primary access pattern
    - In-memory database like Redis sorted sets if the dataset fits in memory
    
    This seems more practical than implementing a custom sort algorithm from scratch.
    """
    
    result3 = await sequential_thinking(
        thought=thought3,
        thought_number=3,
        total_thoughts=5,
        next_thought_needed=True,
        session_id=session_id
    )
    
    # Thought 4: Revising the approach based on new insights
    thought4 = """
    I need to revise my previous thinking. While a database approach is practical,
    the problem specifically asks for a sorting algorithm design, not a system design.
    
    Let's reconsider with a more algorithm-focused approach:
    
    For this specific use case, a combination of approaches would be most efficient:
    
    1. Initial sort: Use a parallel merge sort for the 10M records
       - Can be distributed across multiple cores/machines
       - Stable sort preserves order for equal customer IDs
       
    2. For incremental updates: Use an insertion-based approach with optimization
       - Maintain a sorted main dataset
       - Keep a separate, smaller sorted buffer for new transactions
       - When the buffer reaches a threshold size, merge it with the main dataset
       - This is essentially the core idea behind a Log-Structured Merge Tree (LSM-Tree)
    
    3. Optimization for frequent output:
       - The main dataset plus the buffer represent the current state
       - Queries can merge results from both on-the-fly
       - For range queries, we can efficiently skip sections that don't match
    
    This approach combines the efficiency of merge sort with the incremental
    update capability of buffer-based insertion.
    """
    
    result4 = await sequential_thinking(
        thought=thought4,
        thought_number=4,
        total_thoughts=5,
        next_thought_needed=True,
        session_id=session_id,
        is_revision=True,
        revises_thought=3
    )
    
    # Branch: Alternative approach using a different algorithm
    branch_thought = """
    I want to explore an alternative approach using a different algorithm structure.
    
    Instead of the LSM-tree like approach, we could consider:
    
    1. Use a Skip List data structure
       - Probabilistic alternative to balanced trees
       - Expected O(log n) operations for search, insert, delete
       - Can efficiently support range queries
       - Simpler to implement than balanced trees
       
    2. Implementation approach:
       - Create a skip list with customer_id as the primary key
       - For records with the same customer_id, maintain a nested skip list ordered by timestamp
       - This creates a two-level indexing structure
       
    3. Handling updates:
       - New transactions are inserted directly into the skip list (O(log n) expected)
       - No need for separate buffers or periodic merges
       
    4. Query processing:
       - Range queries can utilize the skip list's efficient iteration capabilities
       - The multi-level structure naturally supports the composite sorting criteria
       
    This approach trades some theoretical worst-case guarantees for simplicity and
    consistent performance without the need for periodic merges.
    """
    
    branch_result = await sequential_thinking(
        thought=branch_thought,
        thought_number=4,
        total_thoughts=6,
        next_thought_needed=True,
        session_id=session_id,
        branch_from_thought=3,
        branch_id="skip_list_approach"
    )
    
    # Final thought (main branch)
    thought5 = """
    Based on the analysis, here's the final algorithm design for the transaction sorting problem:
    
    ALGORITHM: LSM-TREE INSPIRED SORTING
    
    Data structures:
    1. Main dataset: Array of sorted records (by customer_id, then timestamp)
    2. Buffer: Balanced binary search tree (e.g., Red-Black Tree)
    
    Initialization:
    1. Load the initial 10M records into memory
    2. Use parallel merge sort to sort by (customer_id, timestamp)
    3. Initialize an empty buffer
    
    For adding new transactions (100-1000 records batch):
    1. For each record, insert into the buffer tree (O(log b) where b is buffer size)
    2. If buffer size > threshold (e.g., 10,000 records):
       a. Sort the buffer if not already sorted
       b. Merge the buffer with the main dataset (O(n + b))
       c. Reset the buffer to empty
    
    For querying the sorted data:
    1. If the query only needs main dataset, return directly
    2. If buffer is not empty, perform a merge iterator:
       a. Initialize pointers to the head of both structures
       b. Advance pointers in order based on comparison
       c. This gives the appearance of a fully sorted dataset
    
    Optimization considerations:
    1. Buffer threshold can be tuned based on query/update frequency
    2. Main dataset can be periodically rebalanced or reorganized
    3. For very large datasets, the approach can be extended with disk-based strategies
    
    Time complexity:
    - Initial sort: O(n log n)
    - Insert single record: O(log b)
    - Merge buffer: O(n + b) but amortized over many inserts
    - Query: O(n + b) worst case, but can be optimized for specific queries
    
    This design efficiently balances the need for fast initial sorting,
    incremental updates, and frequent sorted outputs.
    """
    
    result5 = await sequential_thinking(
        thought=thought5,
        thought_number=5,
        total_thoughts=5,
        next_thought_needed=False,
        session_id=session_id,
        session_summary="Designed an efficient algorithm for sorting large transaction datasets with incremental updates. The solution uses a merge-sort based approach for initial sorting combined with a buffer-based strategy for handling incremental updates, inspired by Log-Structured Merge Trees (LSM-Trees).",
        key_thoughts=[1, 4, 5]
    )
    
    # Final thought for the branch
    branch_final_thought = """
    Final Skip List based solution:
    
    ALGORITHM: MULTI-LEVEL SKIP LIST SORTING
    
    Data structures:
    1. Primary Skip List: Keys are customer_ids
    2. Secondary Skip Lists: One per customer_id, keys are timestamps
    
    Initialization:
    1. Create an empty primary skip list
    2. For each record in the initial 10M dataset:
       a. If customer_id doesn't exist in primary list, add it with a new secondary skip list
       b. Add the record to the appropriate secondary skip list, ordered by timestamp
    
    For adding new transactions (100-1000 records batch):
    1. For each record:
       a. Locate the customer_id in the primary skip list (O(log n) expected)
       b. If not found, insert a new node with a new secondary skip list
       c. Insert the record into the secondary skip list (O(log m) where m is the number 
          of transactions for that customer)
    
    For querying the sorted data:
    1. For full dataset traversal:
       a. Iterate through the primary skip list (by customer_id)
       b. For each customer, iterate through their secondary skip list (by timestamp)
    2. For range queries:
       a. Use skip list's efficient search to find starting points
       b. Traverse until ending condition is met
    
    Advantages:
    1. Consistent O(log n) expected performance for all operations
    2. No need for separate buffer structures or periodic merges
    3. Naturally supports the composite sorting criteria
    4. Simpler to implement and reason about than LSM-tree based approaches
    
    Disadvantages:
    1. Higher space overhead due to the probabilistic nature of skip lists
    2. Might have slightly worse cache performance than arrays
    3. Probabilistic guarantees rather than worst-case guarantees
    
    Overall, this approach is most suitable when:
    - Simplicity is valued over absolute space efficiency
    - Insert and query operations are intermixed (no clear separation)
    - Consistent performance is preferred over occasionally faster but sometimes slower operations
    """
    
    branch_final_result = await sequential_thinking(
        thought=branch_final_thought,
        thought_number=5,
        total_thoughts=6,
        next_thought_needed=False,
        session_id=session_id,
        branch_from_thought=3,
        branch_id="skip_list_approach",
        session_summary="Developed an alternative sorting algorithm for transaction data using a multi-level Skip List approach. The solution provides consistent O(log n) expected performance for all operations without requiring periodic merges, trading some space efficiency for implementation simplicity and predictable performance.",
        key_thoughts=[3, 4, 5]
    )
    
    print("\n" + "=" * 80)
    print(" SEQUENTIAL THINKING SESSION COMPLETED ".center(80, "="))
    print("=" * 80 + "\n")
    print("The sequential thinking process demonstrated:")
    print("1. Initial problem analysis")
    print("2. Exploration of potential solutions")
    print("3. Revision of thoughts based on new insights")
    print("4. Branching to explore alternative approaches")
    print("5. Final solution with detailed algorithm design")

async def run_code_review_session():
    """
    Run a sequential thinking session for code review and improvement.
    This example analyzes a hypothetical function and suggests improvements.
    """
    print("\n" + "=" * 80)
    print(" SEQUENTIAL THINKING: CODE REVIEW EXAMPLE ".center(80, "="))
    print("=" * 80 + "\n")
    
    session_id = f"code_review_{str(uuid.uuid4())[:8]}"
    print(f"Session ID: {session_id}")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # The code to review
    code = """
    def process_transactions(transactions, user_id=None):
        results = []
        for transaction in transactions:
            # Skip transactions that don't match user_id if specified
            if user_id is not None and transaction['user_id'] != user_id:
                continue
                
            # Calculate transaction fee
            amount = transaction['amount']
            if amount < 100:
                fee = amount * 0.02
            elif amount < 1000:
                fee = amount * 0.015
            else:
                fee = amount * 0.01
                
            # Apply discount for preferred customers
            if transaction['customer_type'] == 'preferred':
                fee = fee * 0.9
                
            # Add processed transaction to results
            processed_transaction = transaction.copy()
            processed_transaction['fee'] = fee
            processed_transaction['total'] = amount + fee
            results.append(processed_transaction)
            
        return results
    """
    
    print("\nCODE TO REVIEW:")
    print(code)
    
    # Thought 1: Initial code review
    thought1 = """
    Let me analyze this `process_transactions` function:
    
    Purpose: The function processes a list of transactions, optionally filtering by user_id,
    calculates fees based on amount tiers, applies discounts for preferred customers,
    and returns enriched transaction objects.
    
    Initial observations:
    
    1. Functionality:
       - Filters transactions by user_id (if provided)
       - Calculates tiered fees (2% for <$100, 1.5% for <$1000, 1% for >=$1000)
       - Applies a 10% discount on fees for preferred customers
       - Returns enriched transaction objects with fee and total
    
    2. Potential issues:
       - Inefficient filtering by looping through all transactions
       - No input validation
       - Business logic is embedded directly in the function
       - No documentation or type hints
       - Copy of transaction dict might be inefficient for large objects
    
    Let me think more about potential improvements.
    """
    
    result1 = await sequential_thinking(
        thought=thought1,
        thought_number=1,
        total_thoughts=4,
        next_thought_needed=True,
        session_id=session_id
    )
    
    # Thought 2: Detailed improvement suggestions
    thought2 = """
    Here are specific improvements I'd recommend for this function:
    
    1. Add proper documentation and type hints:
       - Include a docstring explaining purpose, parameters, and return values
       - Add type hints for parameters and return value
    
    2. Add input validation:
       - Check if transactions is iterable
       - Validate the structure of transaction objects
       - Handle edge cases (empty list, None values, etc.)
    
    3. Extract business logic to separate functions:
       - Move fee calculation to a dedicated function
       - Move discount calculation to another function
       - This improves testability and makes changes easier
    
    4. Optimize filtering:
       - If filtering by user_id is common, consider filtering before processing
       - Could use a list comprehension or filter() for cleaner code
    
    5. Use more efficient data structures:
       - Consider using namedtuples or dataclasses instead of dictionaries
       - Alternatively, modify dictionaries in-place if they're not needed elsewhere
    
    6. Improve performance for large transaction sets:
       - Consider using generator expressions for lazy evaluation
       - Process transactions in chunks if the list is very large
    
    I'll refactor this code with these improvements in the next step.
    """
    
    result2 = await sequential_thinking(
        thought=thought2,
        thought_number=2,
        total_thoughts=4,
        next_thought_needed=True,
        session_id=session_id
    )
    
    # Thought 3: Refactored code
    thought3 = """
    Here's my refactored version of the code with improvements:
    
    ```
    # Example of refactored code (for demonstration only)
    
    from typing import List, Dict, Optional, Any, Iterator
    from dataclasses import dataclass
    
    @dataclass
    class ProcessedTransaction:
        user_id: str
        amount: float
        customer_type: str
        fee: float
        total: float
        # Include other fields from original transaction
        
    def calculate_fee(amount: float) -> float:
        """Calculate transaction fee based on amount tiers."""
        if amount < 100:
            return amount * 0.02
        elif amount < 1000:
            return amount * 0.015
        else:
            return amount * 0.01
            
    def apply_customer_discount(fee: float, customer_type: str) -> float:
        """Apply customer-specific discounts to the fee."""
        if customer_type == 'preferred':
            return fee * 0.9
        return fee
        
    def process_transactions(
        transactions: List[Dict[str, Any]], 
        user_id: Optional[str] = None
    ) -> List[ProcessedTransaction]:
        """
        Process a list of transactions, calculating fees and totals.
        
        Args:
            transactions: List of transaction dictionaries with at least 'user_id',
                         'amount', and 'customer_type' keys
            user_id: Optional user ID to filter transactions by
            
        Returns:
            List of ProcessedTransaction objects with calculated fee and total
            
        Raises:
            ValueError: If transactions is not iterable or has invalid structure
        """
        # Input validation
        if not hasattr(transactions, '__iter__'):
            raise ValueError("Transactions must be an iterable")
            
        # Filter by user_id first if provided
        if user_id is not None:
            transactions = [t for t in transactions if t.get('user_id') == user_id]
            
        results = []
        
        for transaction in transactions:
            # Validate transaction structure
            for key in ('user_id', 'amount', 'customer_type'):
                if key not in transaction:
                    raise ValueError(f"Transaction missing required key: {key}")
                    
            amount = transaction['amount']
            customer_type = transaction['customer_type']
            
            # Calculate fee with extracted business logic
            fee = calculate_fee(amount)
            fee = apply_customer_discount(fee, customer_type)
            
            # Create processed transaction object
            processed = ProcessedTransaction(
                user_id=transaction['user_id'],
                amount=amount,
                customer_type=customer_type,
                fee=fee,
                total=amount + fee
            )
            
            results.append(processed)
            
        return results
        
    # For processing very large transaction sets
    def process_transactions_stream(
        transactions: Iterator[Dict[str, Any]],
        user_id: Optional[str] = None
    ) -> Iterator[ProcessedTransaction]:
        """
        Process a stream of transactions lazily, yielding results one by one.
        Useful for very large transaction sets to avoid loading everything into memory.
        """
        for transaction in transactions:
            if user_id is not None and transaction.get('user_id') != user_id:
                continue
                
            # Validation and processing code would go here
            # Similar to the non-streaming version
            
            # This is just a placeholder for demonstration
            processed = ProcessedTransaction(
                user_id=transaction.get('user_id', ''),
                amount=transaction.get('amount', 0.0),
                customer_type=transaction.get('customer_type', ''),
                fee=0.0,  # Would calculate this properly
                total=0.0  # Would calculate this properly
            )
            
            yield processed
    ```
    
    This refactored version has several improvements:
    
    1. Separated business logic into dedicated functions
    2. Added proper type hints and documentation
    3. Added input validation
    4. Created a proper data structure for results
    5. Pre-filtered transactions for efficiency
    6. Added a streaming version for large datasets
    
    The code is now more maintainable, testable, and handles edge cases better.
    """
    
    result3 = await sequential_thinking(
        thought=thought3,
        thought_number=3,
        total_thoughts=4,
        next_thought_needed=True,
        session_id=session_id
    )
    
    # Thought 4: Final thoughts and additional considerations
    thought4 = """
    Upon further reflection, here are some additional considerations for this code:
    
    1. Performance considerations:
    
       - The `ProcessedTransaction` dataclass is more memory-efficient and safer than using dictionaries
       - However, if we need to preserve all original transaction fields, this approach might be limiting
       - An alternative would be to use `transaction.copy()` and update it, but add a unit test to ensure
         we're not modifying the original transaction
         
    2. Error handling:
    
       - Our validation is better, but we could add more specific error types
       - For production code, we might want to log validation errors rather than raising exceptions
       - Consider adding a "strict mode" parameter that controls whether to raise exceptions or skip invalid entries
    
    3. Extensibility:
    
       - The fee calculation and discount logic is now easier to modify
       - We could further extend this by creating a configuration-based approach
       - Example: define tiers and rates in a config file or database
    
    4. Testing:
    
       - The refactored code is much more testable
       - Each component (fee calculation, discount application) can be tested independently
       - Edge cases can be tested systematically
    
    5. Real-world considerations:
    
       - For a production application, fees and discounts likely come from a database
       - Currency handling should be done carefully (consider using Decimal instead of float)
       - External integrations (e.g., payment processors) would add complexity
    
    Final assessment:
    
    The refactored code significantly improves upon the original by:
    - Separating concerns
    - Adding proper validation and documentation
    - Improving performance characteristics
    - Making the code more maintainable and testable
    
    These improvements would make a substantial difference in a real-world application,
    especially as the codebase grows in size and complexity.
    """
    
    result4 = await sequential_thinking(
        thought=thought4,
        thought_number=4,
        total_thoughts=4,
        next_thought_needed=False,
        session_id=session_id,
        session_summary="Reviewed and refactored a transaction processing function, improving its structure, type safety, validation, performance, and maintainability. Separated business logic, added proper documentation, and enhanced error handling, resulting in code that is more robust and easier to maintain.",
        key_thoughts=[2, 3, 4]
    )
    
    print("\n" + "=" * 80)
    print(" CODE REVIEW SESSION COMPLETED ".center(80, "="))
    print("=" * 80 + "\n")

async def main():
    """Run the sequential thinking examples."""
    print("\n" + "=" * 80)
    print(" CHROMA MCP SEQUENTIAL THINKING EXAMPLES ".center(80, "="))
    print("=" * 80 + "\n")
    
    # Run the algorithm design example
    await run_algorithm_design_session()
    
    # Run the code review example
    await run_code_review_session()
    
    print("\nAll examples completed successfully!")

if __name__ == "__main__":
    asyncio.run(main())
