#!/bin/bash

# Test script to verify Qdrant installation and functionality

echo "Testing Qdrant vector database at http://localhost:6333..."

# First check if Qdrant is running
echo "Checking if Qdrant container is running..."
qdrant_status=$(docker ps | grep qdrant | wc -l)

if [ "$qdrant_status" -eq 0 ]; then
    echo "❌ Qdrant container is not running. Please start your services first."
    exit 1
fi

# Check health endpoint
echo -n "Testing health endpoint: "
health_response=$(curl -s -o /dev/null -w "%{http_code}\n" http://localhost:6333/readyz)

if [ "$health_response" == "200" ]; then
    echo "✅ Qdrant is healthy!"
else
    echo "❌ Qdrant health check failed with HTTP code: $health_response"
    exit 1
fi

# Get Qdrant version
echo "Checking Qdrant version:"
curl -s http://localhost:6333/version | jq || echo "Response is not valid JSON"

# List collections
echo "Listing existing collections:"
curl -s http://localhost:6333/collections | jq || echo "Response is not valid JSON"

# Create a test collection
echo "Creating a test collection 'code_fragments'..."
curl -X PUT \
     -H 'Content-Type: application/json' \
     -d '{
       "vectors": {
         "size": 384,
         "distance": "Cosine"
       }
     }' \
     http://localhost:6333/collections/code_fragments | jq || echo "Failed to create collection"

# Check if collection was created
echo "Verifying collection creation:"
curl -s http://localhost:6333/collections/code_fragments | jq || echo "Response is not valid JSON"

echo "=========================="
echo "Qdrant tests completed!"
echo "If all tests passed, your Qdrant vector database is properly set up."
echo "You can now proceed with configuring your text embedding service."
echo "=========================="
