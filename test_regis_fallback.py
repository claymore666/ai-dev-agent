#!/usr/bin/env python3
"""
Test script to verify the Redis caching fallback functionality.
This script specifically tests that the code will continue to work 
even when Redis is not available or encounters errors.
"""

import os
import sys
import time
import importlib.util
import traceback

# Set up colors for output
GREEN = '\033[0;32m'
RED = '\033[0;31m'
YELLOW = '\033[1;33m'
NC = '\033[0m'  # No Color

def print_colored(color, message):
    """Print a message in color."""
    print(f"{color}{message}{NC}")

def test_module_import(module_name):
    """Test if a module can be imported and handle errors gracefully."""
    print_colored(YELLOW, f"Testing import of {module_name}...")
    try:
        module = __import__(module_name)
        print_colored(GREEN, f"✓ Successfully imported {module_name}")
        return True
    except ImportError:
        print_colored(RED, f"✗ Failed to import {module_name}")
        return False
    except Exception as e:
        print_colored(RED, f"✗ Error importing {module_name}: {e}")
        return False

def test_coderag_initialization():
    """Test CodeRAG initialization with Redis errors."""
    print_colored(YELLOW, "Testing CodeRAG initialization with Redis errors...")
    
    try:
        # Import the CodeRAG module
        from code_rag import CodeRAG
        
        # Test initialization with invalid Redis configuration
        os.environ["REDIS_HOST"] = "nonexistent-redis-host"
        os.environ["REDIS_PORT"] = "6379"
        
        print("Initializing CodeRAG with invalid Redis configuration (should gracefully handle errors)...")
        
        # Start timing
        start_time = time.time()
        
        # Initialize CodeRAG
        rag = CodeRAG()
        
        # End timing
        end_time = time.time()
        
        # Calculate initialization time
        init_time = end_time - start_time
        
        print_colored(GREEN, f"✓ CodeRAG initialized successfully in {init_time:.2f} seconds despite Redis errors")
        
        # Test a basic functionality
        print("Testing retrieval function (should work despite Redis errors)...")
        results = rag.retrieve_relevant_code("test query", project_id=None, top_k=1)
        
        print_colored(GREEN, "✓ CodeRAG retrieval function works despite Redis errors")
        return True
    
    except Exception as e:
        print_colored(RED, f"✗ Error testing CodeRAG: {e}")
        traceback.print_exc()
        return False

def test_context_selector():
    """Test ContextSelector with Redis errors."""
    print_colored(YELLOW, "Testing ContextSelector with Redis errors...")
    
    try:
        # Import the ContextSelector module
        from context_selector import ContextSelector
        
        # Create a mock RAG system
        class MockRAG:
            def retrieve_relevant_code(self, query, project_id=None, top_k=5):
                return []
        
        mock_rag = MockRAG()
        
        # Test initialization with invalid Redis configuration
        os.environ["REDIS_HOST"] = "nonexistent-redis-host"
        os.environ["REDIS_PORT"] = "6379"
        
        print("Initializing ContextSelector with invalid Redis configuration (should gracefully handle errors)...")
        
        # Initialize ContextSelector
        selector = ContextSelector(mock_rag)
        
        # Test classification method
        print("Testing query classification (should work despite Redis errors)...")
        is_conversation = selector.is_conversation_meta_query("What did we discuss earlier?")
        
        print_colored(GREEN, f"✓ ContextSelector classification works despite Redis errors (result: {is_conversation})")
        return True
        
    except Exception as e:
        print_colored(RED, f"✗ Error testing ContextSelector: {e}")
        traceback.print_exc()
        return False

def main():
    """Main test function."""
    print_colored(YELLOW, "========== Testing Redis Caching Fallback ==========")
    
    # Test required modules
    modules_pass = test_module_import("redis")
    
    # Test CodeRAG with Redis errors
    coderag_pass = test_coderag_initialization()
    
    # Test ContextSelector with Redis errors
    context_selector_pass = test_context_selector()
    
    # Print summary
    print_colored(YELLOW, "\n========== Test Summary ==========")
    
    if coderag_pass:
        print_colored(GREEN, "✓ CodeRAG handles Redis errors gracefully")
    else:
        print_colored(RED, "✗ CodeRAG does not handle Redis errors gracefully")
        
    if context_selector_pass:
        print_colored(GREEN, "✓ ContextSelector handles Redis errors gracefully")
    else:
        print_colored(RED, "✗ ContextSelector does not handle Redis errors gracefully")
    
    if coderag_pass and context_selector_pass:
        print_colored(GREEN, "\n✓ All Redis fallback tests PASSED!")
        return True
    else:
        print_colored(RED, "\n✗ Some Redis fallback tests FAILED!")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
