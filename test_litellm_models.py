#!/usr/bin/env python3
"""
Test script to check available models in LiteLLM.
"""

import requests
import json
import os
import sys

# Configuration
LITELLM_HOST = os.environ.get("LITELLM_HOST", "localhost")
LITELLM_PORT = os.environ.get("LITELLM_PORT", "8081")
LITELLM_URL = f"http://{LITELLM_HOST}:{LITELLM_PORT}"

def get_available_models():
    """Get the list of available models from LiteLLM."""
    try:
        response = requests.get(f"{LITELLM_URL}/v1/models")
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error: Status code {response.status_code}")
            print(f"Response: {response.text}")
            return None
    except Exception as e:
        print(f"Exception: {str(e)}")
        return None

def test_completion(model_name):
    """Test a completion with the given model."""
    try:
        payload = {
            "model": model_name,
            "messages": [
                {"role": "user", "content": "Write a hello world function in Python"}
            ]
        }
        
        print(f"Testing completion with model: {model_name}")
        print(f"Sending request to: {LITELLM_URL}/v1/chat/completions")
        print(f"Payload: {json.dumps(payload, indent=2)}")
        
        response = requests.post(
            f"{LITELLM_URL}/v1/chat/completions",
            headers={"Content-Type": "application/json"},
            json=payload
        )
        
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            print(f"Success! Response content (first 100 chars): {content[:100]}...")
            return True
        else:
            print(f"Error response: {response.text}")
            return False
    except Exception as e:
        print(f"Exception: {str(e)}")
        return False

if __name__ == "__main__":
    print(f"Testing LiteLLM at {LITELLM_URL}")
    
    # Get available models
    print("\nGetting available models...")
    models_data = get_available_models()
    
    if models_data:
        print("\nAvailable models:")
        for model in models_data.get("data", []):
            model_id = model.get("id", "Unknown")
            print(f"- {model_id}")
        
        # Test the first model
        if models_data.get("data"):
            first_model = models_data["data"][0]["id"]
            print(f"\nTesting completion with first available model: {first_model}")
            test_completion(first_model)
    else:
        print("Failed to get available models.")
    
    # Also try with known model names
    print("\nTesting with specific model names:")
    test_models = ["llama2", "codellama"]
    
    for model in test_models:
        print(f"\nTesting model: {model}")
        test_completion(model)
