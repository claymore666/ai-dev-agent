#!/bin/bash

# Test the LiteLLM API

echo "Testing LiteLLM API at http://localhost:8081..."

# Check health endpoint
echo -n "Testing health endpoint: "
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8081/health

# Check models list
echo "Testing models list:"
curl -s http://localhost:8081/v1/models | jq || echo "Response is not valid JSON"

# Test completion with codellama
echo "Testing completion with codellama:"
curl -s -X POST http://localhost:8081/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "ollama-codellama",
    "messages": [{"role": "user", "content": "Write a simple Python function to calculate the fibonacci sequence"}]
  }' | jq || echo "Response is not valid JSON"

# Test completion with llama2
echo "Testing completion with llama2:"
curl -s -X POST http://localhost:8081/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "ollama-llama2",
    "messages": [{"role": "user", "content": "Write a simple Python function to calculate the fibonacci sequence"}]
  }' | jq || echo "Response is not valid JSON"
