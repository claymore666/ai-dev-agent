#!/bin/bash

# Troubleshooting script for LiteLLM connection issues

echo "===== LiteLLM Troubleshooting ====="

# Get Ollama IP
if [ -z "$1" ]; then
  read -p "Enter your Ollama server IP: " OLLAMA_IP
else
  OLLAMA_IP=$1
fi

# 1. Check if LiteLLM container is running
echo "Checking LiteLLM container status..."
CONTAINER_STATUS=$(docker ps -f name=litellm --format "{{.Status}}")

if [ -z "$CONTAINER_STATUS" ]; then
  echo "❌ LiteLLM container is not running!"
else
  echo "✅ LiteLLM container is running: $CONTAINER_STATUS"
fi

# 2. Check direct Ollama connection
echo "Testing direct connection to Ollama at $OLLAMA_IP:11434..."
OLLAMA_RESPONSE=$(curl -s -X POST "http://$OLLAMA_IP:11434/api/generate" \
  -H "Content-Type: application/json" \
  -d '{"model": "codellama", "prompt": "test", "stream": false}' \
  -o /dev/null -w "%{http_code}")

if [ "$OLLAMA_RESPONSE" == "200" ]; then
  echo "✅ Ollama connection successful"
else
  echo "❌ Ollama connection failed with HTTP code: $OLLAMA_RESPONSE"
fi

# 3. Check if Redis is running
echo "Checking Redis container status..."
REDIS_STATUS=$(docker ps -f name=redis --format "{{.Status}}")

if [ -z "$REDIS_STATUS" ]; then
  echo "❌ Redis container is not running!"
else
  echo "✅ Redis container is running: $REDIS_STATUS"
fi

# 4. Update LiteLLM config with correct Ollama IP
echo "Updating LiteLLM config with Ollama IP: $OLLAMA_IP"

# Update both config files
sed -i "s|http://YOUR_OLLAMA_IP:11434|http://$OLLAMA_IP:11434|g" configs/litellm_config.yaml
sed -i "s|http://YOUR_OLLAMA_IP:11434|http://$OLLAMA_IP:11434|g" configs/litellm_simple_config.yaml

# 5. Try the simple config
echo "Creating simple config directory..."
mkdir -p configs

echo "Switching to simple LiteLLM config for testing..."
cp configs/litellm_simple_config.yaml configs/litellm_config.yaml

# 6. Restart LiteLLM container
echo "Restarting LiteLLM container..."
docker-compose restart litellm

echo "Waiting for LiteLLM to start up (10 seconds)..."
sleep 10

echo "Checking LiteLLM logs (last 20 lines)..."
docker-compose logs --tail=20 litellm

# 7. Test LiteLLM connection
echo "Testing LiteLLM API connection..."
LITELLM_RESPONSE=$(curl -s -X GET "http://localhost:8080/v1/models" -o /dev/null -w "%{http_code}")

if [ "$LITELLM_RESPONSE" == "200" ]; then
  echo "✅ LiteLLM API connection successful"
else
  echo "❌ LiteLLM API connection failed with HTTP code: $LITELLM_RESPONSE"
fi

echo "===== Troubleshooting Complete ====="
echo "If issues persist, please check:"
echo "1. Docker-compose.yml configuration"
echo "2. LiteLLM config file path and format"
echo "3. Ollama service accessibility and model availability"
echo "4. Network connectivity between containers"
echo
echo "You can view detailed logs with: docker-compose logs litellm"
