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
   - Yacht as a lightweight container management UI
   - Volume mounts for data persistence
   - Network configuration for communication

2. **LLM Integration**
   - LiteLLM for connecting to the external Ollama service
   - Redis for caching LLM responses
   - Basic prompt templates for code generation

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

### Yacht UI

Access the Yacht UI for container management:
- URL: http://localhost:8000
- Default login: admin@yacht.local / password

### LiteLLM API

The LiteLLM API is available at:
- URL: http://localhost:8080

You can test it with:
```bash
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "ollama-codellama", "messages": [{"role": "user", "content": "Write a hello world in Python"}]}'
```

## Directory Structure

```
ai-dev-agent/
├── configs/                # Configuration files
│   ├── litellm_config.yaml # LiteLLM configuration
├── data/                   # Persistent data storage
│   ├── yacht/              # Yacht configuration
│   ├── redis/              # Redis data
├── logs/                   # Log files
├── docker-compose.yml      # Docker Compose configuration
├── setup.sh                # Setup script
├── start.sh                # Start services script
├── stop.sh                 # Stop services script
├── test_ollama_connection.sh # Test connection to Ollama
└── README.md               # This file
```

## Next Steps

After Phase 1 is completed and validated, proceed to Phase 2:
- Setting up the Vector Database (Chroma DB or Qdrant)
- Configuring the Text Embedding service

## Troubleshooting

### Common Issues

1. **Connection to Ollama fails**
   - Ensure your Ollama service is running on the specified IP
   - Verify there are no firewall rules blocking port 11434
   - Check if the Ollama model (codellama) is installed

2. **Services do not start**
   - Verify Docker and Docker Compose are installed
   - Ensure ports 8000, 8080, and 6379 are available
   - Check logs with `docker-compose logs`

3. **Resource Constraints**
   - Monitor resource usage with `docker stats`
   - Adjust memory limits in docker-compose.yml if needed
