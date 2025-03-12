#!/bin/bash

# Test script to verify Redis caching in LiteLLM
# This script makes the same API call twice and compares response times
# If caching is working, the second call should be noticeably faster

echo "Testing LiteLLM Redis caching at http://localhost:8081..."

# Make sure jq is installed
if ! command -v jq &> /dev/null; then
    echo "This script requires jq to be installed. Please install it first."
    exit 1
fi

# First check if services are running
echo "Checking if services are running..."

# Check Redis
redis_status=$(docker ps | grep redis | wc -l)
if [ "$redis_status" -eq 0 ]; then
    echo "Redis container is not running. Please start your services first."
    exit 1
fi

# Check LiteLLM
litellm_status=$(docker ps | grep litellm | wc -l)
if [ "$litellm_status" -eq 0 ]; then
    echo "LiteLLM container is not running. Please start your services first."
    exit 1
fi

# Clear Redis cache first to ensure a clean test
echo "Clearing Redis cache..."
docker exec redis redis-cli FLUSHALL
echo "Redis cache cleared."

# The test prompt to use
TEST_PROMPT='Write a function to calculate the factorial of a number'

# First request - this should be cached
echo "Making first API call (uncached)..."
start_time=$(date +%s.%N)

first_response=$(curl -s -X POST http://localhost:8081/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "ollama-llama2",
    "messages": [{"role": "user", "content": "'"$TEST_PROMPT"'"}]
  }')

end_time=$(date +%s.%N)
first_duration=$(echo "$end_time - $start_time" | bc)
echo "First call completed in $first_duration seconds"

# Extract a portion of the response to show
first_content=$(echo "$first_response" | jq -r '.choices[0].message.content' | head -c 100)
echo "Response preview: ${first_content}..."

# Wait a moment before second request
sleep 2

# Second request - this should use the cached result
echo "Making second API call (should be cached)..."
start_time=$(date +%s.%N)

second_response=$(curl -s -X POST http://localhost:8081/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "ollama-llama2",
    "messages": [{"role": "user", "content": "'"$TEST_PROMPT"'"}]
  }')

end_time=$(date +%s.%N)
second_duration=$(echo "$end_time - $start_time" | bc)
echo "Second call completed in $second_duration seconds"

# Extract cached information from the response header if available
cached=$(echo "$second_response" | jq -r '.cached // "Not specified in response"')
echo "Cache information from response: $cached"

# Calculate speed difference
speed_diff=$(echo "scale=2; $first_duration / $second_duration" | bc)

# Analyze results
echo ""
echo "========== RESULTS =========="
echo "First call (uncached): $first_duration seconds"
echo "Second call (cached): $second_duration seconds"
echo "Speed difference: ${speed_diff}x faster"

if (( $(echo "$second_duration < $first_duration" | bc -l) )); then
    echo "✅ The second call was faster, suggesting caching might be working."
    
    # Check Redis keys to confirm caching
    echo ""
    echo "Checking Redis for cache keys..."
    redis_keys=$(docker exec redis redis-cli --raw KEYS "*" | wc -l)
    echo "Number of keys in Redis: $redis_keys"
    
    if [ "$redis_keys" -gt 0 ]; then
        echo "✅ Redis contains cache keys, confirming caching is working!"
        
        # Show some details about the keys
        echo ""
        echo "Sample of Redis keys (up to 5):"
        docker exec redis redis-cli --raw KEYS "*" | head -5
    else
        echo "❌ No keys found in Redis. Caching might not be properly configured."
    fi
else
    echo "❌ The second call was not faster. Caching might not be working as expected."
    echo "Check your LiteLLM configuration and Redis connection."
fi

echo ""
echo "To verify actual cache contents, run:"
echo "docker exec redis redis-cli --raw KEYS \"*\""
