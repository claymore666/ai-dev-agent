#!/usr/bin/env python3
"""
Test script for embedding code fragments and storing them in Qdrant.
"""

import os
import sys
import time
from typing import List

import numpy as np
from sentence_transformers import SentenceTransformer
import requests

# Import the Qdrant helper
import qdrant_helper

def get_sample_code_fragments() -> List[dict]:
    """Return a list of sample code fragments for testing."""
    return [
        {
            "filename": "sample_utils.py",
            "code": """
def calculate_fibonacci(n: int) -> int:
    \"\"\"Calculate the nth Fibonacci number recursively.\"\"\"
    if n <= 0:
        return 0
    elif n == 1:
        return 1
    else:
        return calculate_fibonacci(n-1) + calculate_fibonacci(n-2)
            """,
            "metadata": {
                "type": "function",
                "name": "calculate_fibonacci",
                "description": "Recursive Fibonacci calculator"
            }
        },
        {
            "filename": "data_processor.py",
            "code": """
import pandas as pd
from typing import Dict, List, Any

class DataProcessor:
    \"\"\"A class for processing and analyzing data.\"\"\"
    
    def __init__(self, data_path: str):
        \"\"\"Initialize with the path to a data file.\"\"\"
        self.data_path = data_path
        self.data = None
        
    def load_data(self) -> pd.DataFrame:
        \"\"\"Load data from the specified path.\"\"\"
        self.data = pd.read_csv(self.data_path)
        return self.data
        
    def get_summary_stats(self) -> Dict[str, Any]:
        \"\"\"Return summary statistics of the data.\"\"\"
        if self.data is None:
            self.load_data()
        
        return {
            "count": len(self.data),
            "columns": list(self.data.columns),
            "numeric_stats": self.data.describe().to_dict()
        }
            """,
            "metadata": {
                "type": "class",
                "name": "DataProcessor",
                "description": "Data processing utility class"
            }
        },
        {
            "filename": "main.py",
            "code": """
import argparse
import logging
from data_processor import DataProcessor

def setup_logging(level: str = "INFO"):
    \"\"\"Set up logging configuration.\"\"\"
    numeric_level = getattr(logging, level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f"Invalid log level: {level}")
    
    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

def main():
    \"\"\"Main entry point for the application.\"\"\"
    parser = argparse.ArgumentParser(description="Process data files")
    parser.add_argument("--data-path", required=True, help="Path to data file")
    parser.add_argument("--log-level", default="INFO", help="Logging level")
    args = parser.parse_args()
    
    setup_logging(args.log_level)
    
    processor = DataProcessor(args.data_path)
    data = processor.load_data()
    
    stats = processor.get_summary_stats()
    print(f"Loaded {stats['count']} records with {len(stats['columns'])} columns")

if __name__ == "__main__":
    main()
            """,
            "metadata": {
                "type": "module",
                "name": "main",
                "description": "Main application entry point"
            }
        }
    ]

def test_embedding_and_storage():
    """Test embedding code fragments and storing them in Qdrant."""
    print("Testing code embedding and Qdrant storage...")
    
    # Check if Qdrant is healthy
    if not qdrant_helper.check_qdrant_health():
        print("Qdrant is not healthy. Please make sure it's running.")
        sys.exit(1)
    
    # Create collections if they don't exist
    print("Initializing Qdrant collections...")
    qdrant_helper.create_collections()
    
    # Load the embedding model
    print("Loading Sentence Transformer model...")
    try:
        model = SentenceTransformer('all-MiniLM-L6-v2')
        print(f"Model loaded with embedding dimension: {model.get_sentence_embedding_dimension()}")
    except Exception as e:
        print(f"Failed to load embedding model: {str(e)}")
        sys.exit(1)
    
    # Get sample code fragments
    fragments = get_sample_code_fragments()
    print(f"Generated {len(fragments)} sample code fragments")
    
    # Create a test project ID
    project_id = "test-project-" + str(int(time.time()))
    print(f"Using project ID: {project_id}")
    
    # Embed and store each fragment
    for i, fragment in enumerate(fragments):
        print(f"\nProcessing fragment {i+1}/{len(fragments)}...")
        
        # Generate embedding
        code = fragment["code"]
        embedding = model.encode(code, convert_to_numpy=True).tolist()
        
        # Store in Qdrant
        point_id = qdrant_helper.store_code_fragment(
            code=code,
            embedding=embedding,
            filename=fragment["filename"],
            project_id=project_id,
            metadata=fragment["metadata"]
        )
        
        if point_id:
            print(f"Successfully stored fragment with ID: {point_id}")
        else:
            print("Failed to store fragment")
    
    # Test search functionality
    print("\nTesting search functionality...")
    search_code = """
def fibonacci(n):
    # Calculate fibonacci number
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)
    """
    
    search_embedding = model.encode(search_code, convert_to_numpy=True).tolist()
    results = qdrant_helper.search_similar_code(
        embedding=search_embedding,
        limit=3,
        filter_dict={"project_id": project_id}
    )
    
    print(f"Found {len(results)} similar code fragments:")
    for i, result in enumerate(results):
        print(f"\nResult {i+1} (Score: {result['score']:.4f}):")
        print(f"Filename: {result['payload']['filename']}")
        print(f"Type: {result['payload'].get('type', 'N/A')}")
        print(f"Name: {result['payload'].get('name', 'N/A')}")
        print("Code snippet (first 200 chars):")
        print(result['payload']['code'][:200] + "...")
    
    # Clean up test data
    print("\nCleaning up test data...")
    if qdrant_helper.delete_project_data(project_id):
        print(f"Successfully deleted test project: {project_id}")
    else:
        print(f"Failed to delete test project: {project_id}")
    
    print("\nTest completed!")

if __name__ == "__main__":
    test_embedding_and_storage()
