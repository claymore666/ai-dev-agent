#!/bin/bash

# Start services for AI Development Agent POC

echo "Starting AI Development Agent services..."

# Start docker containers in detached mode
docker-compose up -d

# Check if services are running
echo "Checking service status..."
docker-compose ps

# Display access information
echo "----------------------------------------"
echo "Services should now be running:"
echo "Yacht UI: http://localhost:8000"
echo "LiteLLM API: http://localhost:8080"
echo "----------------------------------------"
echo "First time Yacht login credentials:"
echo "Email: admin@yacht.local"
echo "Password: password"
echo "----------------------------------------"
echo "To test LiteLLM connection to Ollama:"
echo "curl -X POST http://localhost:8080/v1/chat/completions \\"
echo "  -H \"Content-Type: application/json\" \\"
echo "  -d '{\"model\": \"ollama-codellama\", \"messages\": [{\"role\": \"user\", \"content\": \"Write a hello world in Python\"}]}'"
echo "----------------------------------------"
