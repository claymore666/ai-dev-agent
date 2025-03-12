#!/bin/bash

# Test connection to the Ollama service

# Get Ollama IP from the user
if [ -z "$1" ]; then
  read -p "Enter your Ollama server IP: " OLLAMA_IP
else
  OLLAMA_IP=$1
fi

echo "Testing connection to Ollama at $OLLAMA_IP:11434..."

# Test direct Ollama connection
curl -s -X POST "http://$OLLAMA_IP:11434/api/generate" \
  -H "Content-Type: application/json" \
  -d '{"model": "codellama", "prompt": "Write a hello world in Python", "stream": false}' \
  -o /dev/null -w "Ollama direct connection: %{http_code}\n"

# Update the LiteLLM config with the provided IP
sed -i "s|http://YOUR_OLLAMA_IP:11434|http://$OLLAMA_IP:11434|g" configs/litellm_config.yaml

echo "Updated LiteLLM config with Ollama IP: $OLLAMA_IP"
echo "You can now run ./start.sh to start the services."
