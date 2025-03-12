#!/bin/bash

# Test basic Ollama API endpoints
OLLAMA_HOST="pluto.fritz.box:11434"

echo "Testing Ollama API endpoints on $OLLAMA_HOST..."

echo -n "Testing /api/tags: "
curl -s -o /dev/null -w "%{http_code}\n" "http://$OLLAMA_HOST/api/tags"

echo -n "Testing /api/version: "
curl -s -o /dev/null -w "%{http_code}\n" "http://$OLLAMA_HOST/api/version"

echo -n "Testing basic generate endpoint: "
curl -s -o /dev/null -w "%{http_code}\n" -X POST "http://$OLLAMA_HOST/api/generate" \
  -H "Content-Type: application/json" \
  -d '{"model":"llama2","prompt":"Hello","stream":false}'

echo "Full response from /api/tags:"
curl -s "http://$OLLAMA_HOST/api/tags" | jq || echo "Response is not valid JSON"

echo "Full response from /api/version:"
curl -s "http://$OLLAMA_HOST/api/version" | jq || echo "Response is not valid JSON"
