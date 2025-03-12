# Context-Extended AI Software Development Agent POC

This project implements a proof of concept for an AI software development agent that can maintain context across large Python projects, designed to run with limited resources (4GB RAM, 32GB disk) and connect to a networked Ollama service.

## Prerequisites

- Docker and Docker Compose
- External Ollama service running on a networked machine
- Debian Linux environment (or compatible)
- 4GB RAM, 32GB disk space (minimum)

## Phase 1 Components

Phase 1 sets up the core infrastructure:

1. **Docker Environment**
   - Docker Compose configuration
   - Portainer CE for container management (optional)
   - Volume mounts for data persistence
   - Network configuration for communication

2. **LLM Integration**
   - LiteLLM for connecting to the external Ollama service
   - Redis for caching LLM responses
   - Basic prompt templates for code generation

3. **User Interface**
   - Ollama WebUI for direct interaction with models
   - Nginx proxy for routing requests

## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/ai-dev-agent.git
   cd ai-dev-agent
   ```

2. Run the setup script:
   ```bash
   chmod +x setup.sh
   ./setup.sh
   ```

3. Test and configure the connection to your Ollama server:
   ```bash
   chmod +x test_ollama_connection.sh
   ./test_ollama_connection.sh YOUR_OLLAMA_IP
   ```

4. Start the services:
   ```bash
   ./start.sh
   ```

## Usage

### LiteLLM API

The LiteLLM API is available at:
- URL: http://localhost:8081

You can test it with:
```bash
curl -X POST http://localhost:8081/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "ollama-codellama", "messages": [{"role": "user", "content": "Write a hello world in Python"}]}'
```

### Ollama WebUI

The Ollama WebUI provides a user-friendly interface:
- URL: http://localhost:8083

### Portainer CE (Optional)

If you've installed Portainer using the provided script:
- URL: http://localhost:9000

## Redis Caching

As of version 0.1.1, the system utilizes Redis for caching LLM responses, significantly improving performance for repeated queries.

### Testing Caching

Two scripts are provided to verify and monitor caching:

1. Test if caching is working:
   ```bash
   chmod +x test_cache.sh
   ./test_cache.sh
   ```

2. Monitor Redis cache statistics:
   ```bash
   chmod +x monitor_redis.sh
   ./monitor_redis.sh
   ```

### Cache Performance

When functioning correctly, you should observe:
- Significantly faster response times for repeated queries (typically 10-100x faster)
- Consistent responses for identical prompts
- Reduced load on the Ollama service

## Directory Structure

```
ai-dev-agent/
├── configs/                # Configuration files
│   ├── litellm_config.yaml # LiteLLM configuration
├── data/                   # Persistent data storage
│   ├── redis/              # Redis data
│   ├── ollama-webui/       # Ollama WebUI data
├── logs/                   # Log files
├── docker-compose.yml      # Docker Compose configuration
├── setup.sh                # Setup script
├── start.sh                # Start services script
├── stop.sh                 # Stop services script
├── test_litellm.sh         # Test LiteLLM connectivity
├── test_nginx_proxy.sh     # Test Nginx proxy
├── test_cache.sh           # Test Redis caching
├── monitor_redis.sh        # Monitor Redis statistics
├── install_portainer.sh    # Optional Portainer installer
└── README.md               # This file
```

## Next Steps

After completing and validating Phase 1 (which now includes Redis caching), proceed to Phase 2:
- Setting up the Vector Database (Chroma DB or Qdrant)
- Configuring the Text Embedding service
- Implementing the RAG framework for context extension

## Troubleshooting

### Common Issues

1. **Connection to Ollama fails**
   - Ensure your Ollama service is running on the specified IP
   - Verify there are no firewall rules blocking port 11434
   - Check if the Ollama model (codellama/llama2) is installed

2. **Services do not start**
   - Verify Docker and Docker Compose are installed
   - Ensure ports 8081-8083, 6379 are available
   - Check logs with `docker-compose logs`

3. **Caching not working**
   - Verify Redis is running with `docker ps | grep redis`
   - Check Redis connectivity with `docker exec redis redis-cli PING`
   - Review Redis logs with `docker logs redis`

4. **Resource Constraints**
   - Monitor resource usage with `docker stats`
   - Adjust memory limits in docker-compose.yml if needed
