#!/usr/bin/env python3
"""
Qdrant Helper for AI Development Agent
This script provides utility functions for managing code fragments in Qdrant.
"""

import os
import sys
import json
import argparse
import uuid
from typing import List, Dict, Any, Optional

import requests
import numpy as np

# Configuration
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = os.getenv("QDRANT_PORT", "6333")
QDRANT_URL = f"http://{QDRANT_HOST}:{QDRANT_PORT}"

# Collection names
CODE_COLLECTION = "code_fragments"
PROJECT_COLLECTION = "project_metadata"

def check_qdrant_health() -> bool:
    """Check if Qdrant is running and healthy."""
    try:
        response = requests.get(f"{QDRANT_URL}/readyz")
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False

def create_collections(vector_size: int = 384) -> Dict[str, bool]:
    """
    Create the necessary collections for storing code fragments and project metadata.
    
    Args:
        vector_size: Dimension size of the vector embeddings
        
    Returns:
        Dictionary with collection names and creation status
    """
    results = {}
    
    # Define collections configuration
    collections = {
        CODE_COLLECTION: {
            "vectors": {
                "size": vector_size,
                "distance": "Cosine"
            },
            "optimizers_config": {
                "indexing_threshold": 10000  # Smaller for faster indexing with less data
            },
            "on_disk_payload": True  # Store payload on disk to save RAM
        },
        PROJECT_COLLECTION: {
            "vectors": {
                "size": vector_size,
                "distance": "Cosine"
            }
        }
    }
    
    # Create each collection
    for name, config in collections.items():
        url = f"{QDRANT_URL}/collections/{name}"
        try:
            # Check if collection exists
            response = requests.get(url)
            if response.status_code == 200:
                print(f"Collection '{name}' already exists")
                results[name] = True
                continue
                
            # Create collection
            response = requests.put(url, json=config)
            results[name] = response.status_code == 200
            if results[name]:
                print(f"Created collection '{name}'")
            else:
                print(f"Failed to create collection '{name}': {response.text}")
        except requests.exceptions.RequestException as e:
            print(f"Error creating collection '{name}': {str(e)}")
            results[name] = False
    
    return results

def store_code_fragment(
    code: str,
    embedding: List[float],
    filename: str,
    project_id: str,
    metadata: Optional[Dict[str, Any]] = None
) -> str:
    """
    Store a code fragment in Qdrant.
    
    Args:
        code: The code fragment text
        embedding: Vector embedding of the code
        filename: Source filename
        project_id: ID of the project
        metadata: Additional metadata like function name, class name, etc.
        
    Returns:
        ID of the stored fragment
    """
    if metadata is None:
        metadata = {}
    
    # Generate a unique ID
    point_id = str(uuid.uuid4())
    
    # Prepare the point data
    point = {
        "id": point_id,
        "vector": embedding,
        "payload": {
            "code": code,
            "filename": filename,
            "project_id": project_id,
            "created_at": "auto",  # Qdrant will add timestamp
            **metadata
        }
    }
    
    # Store the point
    url = f"{QDRANT_URL}/collections/{CODE_COLLECTION}/points"
    try:
        response = requests.put(url, json={"points": [point]})
        if response.status_code == 200:
            print(f"Stored code fragment with ID: {point_id}")
            return point_id
        else:
            print(f"Failed to store code fragment: {response.text}")
            return ""
    except requests.exceptions.RequestException as e:
        print(f"Error storing code fragment: {str(e)}")
        return ""

def search_similar_code(
    embedding: List[float],
    limit: int = 5,
    filter_dict: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """
    Search for similar code fragments.
    
    Args:
        embedding: Vector to search for
        limit: Maximum number of results
        filter_dict: Filter to apply (e.g., by project_id, filename)
        
    Returns:
        List of matching code fragments with similarity scores
    """
    query = {
        "vector": embedding,
        "limit": limit,
        "with_payload": True,
        "with_vectors": False,  # Don't need the vectors back
    }
    
    if filter_dict:
        query["filter"] = {"must": [{"key": k, "match": {"value": v}} for k, v in filter_dict.items()]}
    
    url = f"{QDRANT_URL}/collections/{CODE_COLLECTION}/points/search"
    try:
        response = requests.post(url, json=query)
        if response.status_code == 200:
            return response.json().get("result", [])
        else:
            print(f"Failed to search: {response.text}")
            return []
    except requests.exceptions.RequestException as e:
        print(f"Error during search: {str(e)}")
        return []

def delete_project_data(project_id: str) -> bool:
    """
    Delete all code fragments and metadata for a specific project.
    
    Args:
        project_id: ID of the project to delete
        
    Returns:
        True if deletion was successful
    """
    filter_dict = {
        "must": [
            {
                "key": "project_id",
                "match": {
                    "value": project_id
                }
            }
        ]
    }
    
    # Delete from code collection
    url = f"{QDRANT_URL}/collections/{CODE_COLLECTION}/points/delete"
    try:
        response = requests.post(url, json={"filter": filter_dict})
        code_success = response.status_code == 200
        
        # Also delete from project collection
        url = f"{QDRANT_URL}/collections/{PROJECT_COLLECTION}/points/delete"
        response = requests.post(url, json={"filter": filter_dict})
        proj_success = response.status_code == 200
        
        return code_success and proj_success
    except requests.exceptions.RequestException as e:
        print(f"Error deleting project data: {str(e)}")
        return False

def list_projects() -> List[Dict[str, Any]]:
    """
    List all projects stored in Qdrant.
    
    Returns:
        List of project metadata
    """
    url = f"{QDRANT_URL}/collections/{PROJECT_COLLECTION}/points/scroll"
    try:
        response = requests.post(url, json={"limit": 100, "with_payload": True})
        if response.status_code == 200:
            return [point["payload"] for point in response.json().get("result", {}).get("points", [])]
        else:
            print(f"Failed to list projects: {response.text}")
            return []
    except requests.exceptions.RequestException as e:
        print(f"Error listing projects: {str(e)}")
        return []

def main():
    """Command-line interface for Qdrant helper."""
    parser = argparse.ArgumentParser(description="Qdrant Helper for AI Development Agent")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Health check command
    health_parser = subparsers.add_parser("health", help="Check Qdrant health")
    
    # Initialize collections command
    init_parser = subparsers.add_parser("init", help="Initialize Qdrant collections")
    init_parser.add_argument("--vector-size", type=int, default=384, 
                            help="Size of vector embeddings (default: 384 for all-MiniLM-L6-v2)")
    
    # List projects command
    list_parser = subparsers.add_parser("list-projects", help="List all projects")
    
    # Delete project command
    delete_parser = subparsers.add_parser("delete-project", help="Delete all data for a project")
    delete_parser.add_argument("project_id", help="Project ID to delete")
    
    args = parser.parse_args()
    
    # Execute commands
    if args.command == "health":
        healthy = check_qdrant_health()
        print(f"Qdrant health: {'HEALTHY' if healthy else 'UNHEALTHY'}")
        sys.exit(0 if healthy else 1)
    
    elif args.command == "init":
        if not check_qdrant_health():
            print("Qdrant is not healthy. Please check if it's running.")
            sys.exit(1)
        results = create_collections(args.vector_size)
        all_success = all(results.values())
        print(f"Initialization {'successful' if all_success else 'failed'}")
        sys.exit(0 if all_success else 1)
    
    elif args.command == "list-projects":
        if not check_qdrant_health():
            print("Qdrant is not healthy. Please check if it's running.")
            sys.exit(1)
        projects = list_projects()
        if projects:
            print(json.dumps(projects, indent=2))
        else:
            print("No projects found or failed to retrieve projects")
    
    elif args.command == "delete-project":
        if not check_qdrant_health():
            print("Qdrant is not healthy. Please check if it's running.")
            sys.exit(1)
        success = delete_project_data(args.project_id)
        print(f"Project deletion {'successful' if success else 'failed'}")
        sys.exit(0 if success else 1)
    
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
