# Context-Extended AI Software Development Agent POC

This project implements a proof of concept for an AI software development agent that can maintain context across large Python projects, designed to run with limited resources (4GB RAM, 32GB disk) and connect to a networked Ollama service.

## Architecture Overview

This project consists of several containerized services:

1. **LiteLLM**: Provides a standardized API interface to the Ollama service
2. **Ollama WebUI**: A web-based user interface for interacting with Ollama models
3. **Nginx Proxy**: Handles path mapping for the Ollama WebUI to communicate with the Ollama API
4. **Redis**: Used for caching LLM responses to improve performance
5. **Portainer** (optional): Container management UI (installed separately)

## Prerequisites

- Docker and Docker Compose
- External Ollama service running on a networked machine
- Debian Linux environment (or compatible)
- 4GB RAM, 32GB disk space (minimum)

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

5. (Optional) Install Portainer for container management:
   ```bash
   chmod +x install_portainer.sh
   ./install_portainer.sh
   ```

## Usage

### Ollama WebUI

Access the Ollama WebUI for chat interactions and file processing:
- URL: http://localhost:8083
- Features:
  - Chat with Ollama models
  - Upload and analyze files (up to 100MB)
  - Use text-to-speech and speech-to-text capabilities
  - Save and manage conversation history
  - Configure model parameters

### LiteLLM API

The LiteLLM API is available at:
- URL: http://localhost:8081

You can test it with:
```bash
curl -X POST http://localhost:8081/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "ollama-codellama", "messages": [{"role": "user", "content": "Write a hello world in Python"}]}'
```

### Portainer (Optional)

If you installed Portainer, access it at:
- URL: http://localhost:9000
- Use the UI to manage containers, view logs, and monitor resources

## Testing Tools

The repository includes several testing and troubleshooting scripts:

- `test_ollama_connection.sh`: Verify connectivity to your Ollama server
- `test_litellm.sh`: Test the LiteLLM API functionality
- `test_nginx_proxy.sh`: Verify nginx proxy configuration
- `troubleshoot_litellm.sh`: Diagnose issues with the LiteLLM service

## Architecture Details

### Nginx Proxy Configuration

The nginx proxy serves a critical role in this setup, handling path mapping between the Ollama WebUI and the Ollama API. The WebUI expects endpoints at paths like `/tags` and `/version`, while the Ollama API serves them at `/api/tags` and `/api/version`. The nginx proxy bridges this gap by:

- Mapping direct top-level endpoints to their API counterparts
- Supporting both direct and prefixed path patterns
- Handling WebSocket connections for streaming responses
- Providing CORS headers for browser compatibility
- Managing file uploads with appropriate buffer sizes

### Docker Network Architecture

The services communicate through an internal Docker network (`ai-dev-network`), with specific ports exposed to the host machine:
- Ollama WebUI: Port 8083
- LiteLLM API: Port 8081
- Nginx Proxy: Port 8082
- Redis: Port 6379 (only accessible from localhost)
- Portainer: Ports 8000 and 9000 (if installed)

## Troubleshooting

### Common Issues

1. **Ollama WebUI can't connect to Ollama**
   - Verify the Ollama service is running on the specified IP
   - Check the nginx proxy logs for connection issues
   - Ensure ports 8082 and 8083 are not blocked by firewall

2. **File uploads fail**
   - Check the upload size limit in docker-compose.yml and nginx.conf
   - Verify the proper CORS headers are being sent
   - Look for errors in the Ollama WebUI container logs

3. **Microphone access denied**
   - Ensure your browser has granted microphone permissions
   - Access the WebUI through localhost (http://localhost:8083)
   - Verify WEBUI_STT_ENABLE is set to true in docker-compose.yml

4. **LiteLLM API not responding**
   - Check the connection to your Ollama server
   - Verify the LiteLLM configuration in configs/litellm_config.yaml
   - Run the troubleshoot_litellm.sh script for detailed diagnostics

## Directory Structure

```
ai-dev-agent/
├── configs/                # Configuration files
│   ├── litellm_config.yaml # LiteLLM configuration
│   └── litellm_simple_config.yaml # Simplified config for troubleshooting
├── data/                   # Persistent data storage
│   ├── ollama-webui/       # WebUI configuration and data
│   └── redis/              # Redis data
├── nginx.conf              # Nginx proxy configuration
├── docker-compose.yml      # Docker Compose configuration
├── setup.sh                # Setup script
├── start.sh                # Start services script
├── stop.sh                 # Stop services script
├── test_*.sh               # Various testing scripts
├── install_portainer.sh    # Portainer installation script
└── README.md               # This file
```

## Advanced Configuration

### Scaling for Larger Projects

For handling larger Python projects:
1. Adjust memory limits in docker-compose.yml based on available resources
2. Configure LiteLLM caching parameters in litellm_config.yaml
3. Consider adding a vector database like Chroma DB or Qdrant in Phase 2

### Security Considerations

This POC prioritizes functionality over security. For production use:
1. Add proper authentication to all services
2. Use HTTPS with valid certificates
3. Implement network segmentation
4. Apply principle of least privilege for all containers

## Next Steps

After this Phase 1 setup is completed and validated, proceed to Phase 2:
- Setting up the Vector Database (Chroma DB or Qdrant)
- Configuring the Text Embedding service
- Implementing retrieval-augmented generation (RAG) for context extension
- Developing the code parsing and analysis system
