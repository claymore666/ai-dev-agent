#!/bin/bash

# Test if the nginx proxy is correctly mapping paths

echo "Testing nginx proxy at http://localhost:8082..."

echo -n "Testing /tags endpoint (should map to /api/tags): "
curl -s -o /dev/null -w "%{http_code}\n" "http://localhost:8082/tags"

echo -n "Testing /version endpoint (should map to /api/version): "
curl -s -o /dev/null -w "%{http_code}\n" "http://localhost:8082/version"

echo "Full response from /tags:"
curl -s "http://localhost:8082/tags" | jq || echo "Response is not valid JSON"

echo "Full response from /version:"
curl -s "http://localhost:8082/version" | jq || echo "Response is not valid JSON"

echo -n "Testing direct access to Ollama WebUI: "
curl -s -o /dev/null -w "%{http_code}\n" "http://localhost:8083"

echo "If all endpoints return 200, the nginx proxy is working correctly."
echo "The Ollama WebUI should now be accessible at http://localhost:8083"
