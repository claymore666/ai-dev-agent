#!/usr/bin/env python3
"""
Test script for the Code RAG system.
This script tests the RAG functionality by adding sample code,
performing searches, and generating code with context.
"""

import os
import sys
import time
import uuid
from typing import List, Dict, Any

from code_rag import CodeRAG

def get_sample_code_fragments() -> List[Dict[str, Any]]:
    """Return a list of sample code fragments for testing."""
    return [
        {
            "filename": "data_loader.py",
            "code": """
class DataLoader:
    \"\"\"Load data from various sources into standardized formats.\"\"\"
    
    def __init__(self, config=None):
        \"\"\"Initialize with optional configuration.\"\"\"
        self.config = config or {}
        self.data_sources = {}
        
    def register_source(self, name, source_config):
        \"\"\"Register a new data source.\"\"\"
        self.data_sources[name] = source_config
        
    def load_csv(self, filepath, **kwargs):
        \"\"\"Load data from a CSV file.\"\"\"
        import pandas as pd
        return pd.read_csv(filepath, **kwargs)
    
    def load_json(self, filepath, **kwargs):
        \"\"\"Load data from a JSON file.\"\"\"
        import json
        with open(filepath, 'r') as f:
            return json.load(f, **kwargs)
    
    def load_from_source(self, source_name, **kwargs):
        \"\"\"Load data from a registered source.\"\"\"
        if source_name not in self.data_sources:
            raise ValueError(f"Source {source_name} not registered")
        
        source_config = self.data_sources[source_name]
        source_type = source_config.get('type', 'unknown')
        
        if source_type == 'csv':
            return self.load_csv(source_config['path'], **kwargs)
        elif source_type == 'json':
            return self.load_json(source_config['path'], **kwargs)
        else:
            raise ValueError(f"Unsupported source type: {source_type}")
            """,
            "metadata": {
                "type": "class",
                "name": "DataLoader",
                "description": "Utility for loading data from various sources"
            }
        },
        {
            "filename": "data_processor.py",
            "code": """
class DataProcessor:
    \"\"\"Process and transform data for analysis and modeling.\"\"\"
    
    def __init__(self, data=None):
        \"\"\"Initialize with optional data.\"\"\"
        self.data = data
        
    def set_data(self, data):
        \"\"\"Set the data to process.\"\"\"
        self.data = data
        return self
        
    def filter_columns(self, columns):
        \"\"\"Filter data to include only specified columns.\"\"\"
        if self.data is None:
            raise ValueError("No data to process")
        
        return self.data[columns]
    
    def fill_missing(self, strategy='mean', columns=None):
        \"\"\"Fill missing values using the specified strategy.\"\"\"
        if self.data is None:
            raise ValueError("No data to process")
        
        data_copy = self.data.copy()
        
        if columns is None:
            columns = data_copy.columns
        
        for column in columns:
            if column not in data_copy.columns:
                continue
                
            if strategy == 'mean':
                data_copy[column] = data_copy[column].fillna(data_copy[column].mean())
            elif strategy == 'median':
                data_copy[column] = data_copy[column].fillna(data_copy[column].median())
            elif strategy == 'mode':
                data_copy[column] = data_copy[column].fillna(data_copy[column].mode()[0])
            elif strategy == 'zero':
                data_copy[column] = data_copy[column].fillna(0)
            else:
                raise ValueError(f"Unsupported strategy: {strategy}")
        
        return data_copy
    
    def normalize(self, columns=None, method='min-max'):
        \"\"\"Normalize data using the specified method.\"\"\"
        if self.data is None:
            raise ValueError("No data to process")
        
        data_copy = self.data.copy()
        
        if columns is None:
            columns = data_copy.select_dtypes(include=['number']).columns
        
        for column in columns:
            if column not in data_copy.columns:
                continue
                
            if method == 'min-max':
                min_val = data_copy[column].min()
                max_val = data_copy[column].max()
                
                if max_val > min_val:
                    data_copy[column] = (data_copy[column] - min_val) / (max_val - min_val)
            elif method == 'z-score':
                mean = data_copy[column].mean()
                std = data_copy[column].std()
                
                if std > 0:
                    data_copy[column] = (data_copy[column] - mean) / std
            else:
                raise ValueError(f"Unsupported method: {method}")
        
        return data_copy
            """,
            "metadata": {
                "type": "class",
                "name": "DataProcessor",
                "description": "Utility for processing and transforming data"
            }
        },
        {
            "filename": "model_trainer.py",
            "code": """
class ModelTrainer:
    \"\"\"Train machine learning models on processed data.\"\"\"
    
    def __init__(self, model_type='linear'):
        \"\"\"Initialize with the model type.\"\"\"
        self.model_type = model_type
        self.model = None
        
    def create_model(self):
        \"\"\"Create a model instance based on the specified type.\"\"\"
        if self.model_type == 'linear':
            from sklearn.linear_model import LinearRegression
            self.model = LinearRegression()
        elif self.model_type == 'ridge':
            from sklearn.linear_model import Ridge
            self.model = Ridge(alpha=1.0)
        elif self.model_type == 'lasso':
            from sklearn.linear_model import Lasso
            self.model = Lasso(alpha=1.0)
        elif self.model_type == 'random_forest':
            from sklearn.ensemble import RandomForestRegressor
            self.model = RandomForestRegressor(n_estimators=100)
        else:
            raise ValueError(f"Unsupported model type: {self.model_type}")
        
        return self.model
    
    def train(self, X, y):
        \"\"\"Train the model on the provided data.\"\"\"
        if self.model is None:
            self.create_model()
        
        self.model.fit(X, y)
        return self
    
    def predict(self, X):
        \"\"\"Make predictions using the trained model.\"\"\"
        if self.model is None:
            raise ValueError("Model not trained yet")
        
        return self.model.predict(X)
    
    def evaluate(self, X, y_true):
        \"\"\"Evaluate the model performance.\"\"\"
        from sklearn.metrics import mean_squared_error, r2_score
        
        if self.model is None:
            raise ValueError("Model not trained yet")
        
        y_pred = self.predict(X)
        
        mse = mean_squared_error(y_true, y_pred)
        r2 = r2_score(y_true, y_pred)
        
        return {
            'mse': mse,
            'rmse': mse ** 0.5,
            'r2': r2
        }
            """,
            "metadata": {
                "type": "class",
                "name": "ModelTrainer",
                "description": "Utility for training machine learning models"
            }
        }
    ]

def test_code_rag():
    """Test the CodeRAG system."""
    print("Testing Code RAG system...")
    
    # Initialize CodeRAG
    rag = CodeRAG(llm_model_name="ollama-codellama")
    
    # Create a test project ID
    project_id = f"test-project-{uuid.uuid4().hex[:8]}"
    print(f"Using project ID: {project_id}")
    
    # Add sample code fragments
    fragments = get_sample_code_fragments()
    print(f"Adding {len(fragments)} sample code fragments to the index...")
    
    for i, fragment in enumerate(fragments):
        print(f"\nProcessing fragment {i+1}/{len(fragments)}...")
        
        code = fragment["code"]
        metadata = {
            "filename": fragment["filename"],
            "project_id": project_id,
            **fragment["metadata"]
        }
        
        doc_id = rag.add_code_to_index(code, metadata)
        print(f"Added fragment with ID: {doc_id}")
    
    # Let's give Qdrant a moment to index
    print("\nWaiting for indexing to complete...")
    time.sleep(2)
    
    # Test search functionality
    print("\nTesting search functionality...")
    search_query = "how to normalize data columns"
    
    search_results = rag.retrieve_relevant_code(
        query=search_query,
        project_id=project_id,
        top_k=3
    )
    
    print(f"Search query: '{search_query}'")
    print(f"Found {len(search_results)} relevant code fragments:")
    
    for i, result in enumerate(search_results):
        score_display = f"{result['score']:.4f}" if result['score'] is not None else "N/A"
        print(f"\nResult {i+1} (Score: {score_display}):")
        print(f"Filename: {result['metadata'].get('filename', 'unknown')}")
        print(f"Type: {result['metadata'].get('type', 'unknown')}")
        print(f"Name: {result['metadata'].get('name', 'unknown')}")
        print("Code snippet (first 200 chars):")
        print(result['text'][:200] + "...")
    
    # Test generation functionality
    print("\nTesting generation functionality...")
    generate_query = "Write a function to combine the data loading and processing capabilities"
    
    print(f"Generation query: '{generate_query}'")
    
    response = rag.generate_with_context(
        query=generate_query,
        project_id=project_id
    )
    
    print("\nGenerated Response:")
    print("===================")
    print(response)
    
    # Clean up (optional)
    print("\nTest completed! The test data is kept in Qdrant for inspection.")
    print(f"You can delete the test project later with: python qdrant_helper.py delete-project {project_id}")

if __name__ == "__main__":
    test_code_rag()
