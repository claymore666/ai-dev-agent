#!/bin/bash

# Start services for AI Development Agent POC - Phase 2

echo "Starting AI Development Agent services (Phase 2)..."

# Start docker containers in detached mode
docker-compose up -d

# Check if services are running
echo "Checking service status..."
docker-compose ps

# Wait for Qdrant to be ready
echo "Waiting for Qdrant to initialize..."
for i in {1..30}; do
  response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:6333/readyz)
  if [ "$response" == "200" ]; then
    echo "✅ Qdrant is ready!"
    break
  fi
  echo -n "."
  sleep 1
done

if [ "$response" != "200" ]; then
  echo "❌ Qdrant failed to start properly. Please check the logs with 'docker-compose logs qdrant'"
fi

# Initialize Qdrant collections
echo "Initializing Qdrant collections..."
source python-env/bin/activate
python qdrant_helper.py init

# Display access information
echo "----------------------------------------"
echo "Services are now running:"
echo "LiteLLM API: http://localhost:8081"
echo "Ollama WebUI: http://localhost:8083"
echo "Qdrant API: http://localhost:6333"
echo "Qdrant Dashboard: http://localhost:6333/dashboard"
echo "----------------------------------------"
echo "Useful commands:"
echo "- Test LiteLLM: ./test_litellm.sh"
echo "- Test direct LLM API: curl -X POST http://localhost:8082/v1/chat/completions \\"
echo "  -H \"Content-Type: application/json\" \\"
echo "  -d '{\"model\": \"codellama\", \"messages\": [{\"role\": \"user\", \"content\": \"Write a hello world in Python\"}]}'"
echo "- Test Qdrant: ./test_qdrant.sh"
echo "- Test embedding: python3 test_embedding.py"
echo "- Test RAG: python3 test_rag.py"
echo "- Monitor Redis: ./monitor_redis.sh"
echo "----------------------------------------"
