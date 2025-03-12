# Context-Extended AI Software Development Agent POC

This project implements a proof of concept for an AI software development agent that can maintain context across large Python projects. The system uses retrieval-augmented generation (RAG) to provide AI code assistance with extended context awareness, and is designed to run with limited resources (4GB RAM, 32GB disk) while connecting to a networked Ollama service.

## Key Features

- **Context Awareness**: Maintains understanding across large codebases
- **Code Generation**: Creates Python code informed by existing project context
- **Semantic Search**: Retrieves relevant code fragments based on meaning
- **Docker Integration**: Runs in containers with minimal resource requirements
- **Lightweight Design**: Optimized for systems with limited resources

## Prerequisites

- Docker and Docker Compose
- External Ollama service running on a networked machine
- Debian Linux environment (or compatible)
- 4GB RAM, 32GB disk space (minimum)
- Python 3.8+ with pip

### Debian Dependencies

The following packages are required to run all scripts and utilities:

```bash
# Install required system dependencies
sudo apt-get update
sudo apt-get install -y \
    git \
    curl \
    bc \
    jq \
    python3-pip \
    python3-venv \
    docker.io \
    docker-compose

# Optional: Install GitHub CLI (gh)
curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
sudo apt update
sudo apt install gh
```

## Components

### Phase 1 (Completed)

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

### Phase 2 (Current)

Phase 2 implements the context extension capabilities:

1. **Vector Database**
   - Qdrant for storing and retrieving code fragments
   - Efficient vector similarity search
   - Project-based organization of code contexts

2. **Text Embedding**
   - Sentence Transformers with all-MiniLM-L6-v2 model
   - Code fragment embedding for semantic search
   - Efficient representation of code semantics

3. **RAG Framework**
   - LlamaIndex integration with Qdrant vector store
   - Context-aware code generation via LiteLLM
   - Semantic retrieval of relevant code fragments
   - Intelligent composition of new code based on existing codebase

## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/ai-dev-agent.git
   cd ai-dev-agent
   ```

2. Run the Phase 2 setup script:
   ```bash
   chmod +x setup_phase2.sh
   ./setup_phase2.sh
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

5. Verify the Qdrant installation:
   ```bash
   chmod +x test_qdrant.sh
   ./test_qdrant.sh
   ```

6. Test the embedding functionality:
   ```bash
   source python-env/bin/activate
   python3 test_embedding.py
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

### Qdrant Dashboard

Qdrant's built-in dashboard is available at:
- URL: http://localhost:6333/dashboard

### Portainer CE (Optional)

If you've installed Portainer using the provided script:
- URL: http://localhost:9000

## Redis Caching

The system utilizes Redis for caching LLM responses, significantly improving performance for repeated queries.

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

## Vector Storage and Embedding

The system uses Qdrant and Sentence Transformers to store and retrieve code fragments based on semantic similarity.

### Managing Code in Qdrant

You can use the provided Python helper library:

```bash
# Activate the Python virtual environment
source python-env/bin/activate

# Check Qdrant health
python3 qdrant_helper.py health

# Initialize collections
python3 qdrant_helper.py init

# List projects
python3 qdrant_helper.py list-projects

# Delete a project
python3 qdrant_helper.py delete-project PROJECT_ID
```

### Using the RAG System

The RAG (Retrieval Augmented Generation) system allows you to generate code with context awareness:

```bash
# Activate the Python virtual environment
source python-env/bin/activate

# Test the RAG system with sample code
python3 test_rag.py

# Use the RAG system directly
python3 code_rag.py generate --query "Write a function to parse CSV files" --project-id "your-project-id"

# Add code to the index
python3 code_rag.py add --code "path/to/your/file.py" --filename "file.py" --project-id "your-project-id" --type "class" --name "YourClass"

# Search for relevant code
python3 code_rag.py search --query "How to normalize data" --project-id "your-project-id"
```

## Directory Structure

```
ai-dev-agent/
├── configs/                # Configuration files
│   ├── litellm_config.yaml # LiteLLM configuration
├── data/                   # Persistent data storage
│   ├── redis/              # Redis data
│   ├── ollama-webui/       # Ollama WebUI data
│   ├── qdrant/             # Qdrant vector database storage
├── logs/                   # Log files
├── python-env/             # Python virtual environment
├── docker-compose.yml      # Docker Compose configuration
├── setup.sh                # Setup script for Phase 1
├── setup_phase2.sh         # Setup script for Phase 2
├── start.sh                # Start services script
├── start_phase2.sh         # Start Phase 2 services script
├── stop.sh                 # Stop services script
├── test_litellm.sh         # Test LiteLLM connectivity
├── test_nginx_proxy.sh     # Test Nginx proxy
├── test_cache.sh           # Test Redis caching
├── test_qdrant.sh          # Test Qdrant functionality
├── test_embedding.py       # Test embedding and vector search
├── test_rag.py             # Test RAG context-aware generation
├── qdrant_helper.py        # Helper library for Qdrant
├── code_rag.py             # RAG framework for code generation
├── monitor_redis.sh        # Monitor Redis statistics
├── install_portainer.sh    # Optional Portainer installer
├── requirements.txt        # Python dependencies
└── README.md               # This file
```

## Next Steps

After completing and validating Phase 2, proceed to Phase 3:
- Implementing a unified CLI tool for interacting with the agent
- Creating autonomous code generation and refinement capabilities
- Developing project management features for tracking context
- Implementing advanced context handling for larger codebases
- Adding support for code debugging and testing

## Example Usage Scenario

The following example demonstrates how the context-extended agent can understand and generate code based on an existing codebase:

1. A data science team has a repository with data loading, processing, and model training modules
2. A developer needs to create a function that combines functionality from multiple modules
3. Using our agent, they can query: "Write a function to combine the data loading and processing capabilities"
4. The agent:
   - Retrieves relevant code from the data loading and processing modules
   - Understands the interfaces and dependencies between them
   - Generates a new function that properly integrates the existing components
   - Provides the developer with properly formatted, compatible code

This context-aware code generation saves development time and ensures consistency with the existing codebase.

## Troubleshooting

### Common Issues

1. **Connection to Ollama fails**
   - Ensure your Ollama service is running on the specified IP
   - Verify there are no firewall rules blocking port 11434
   - Check if the Ollama model (codellama/llama2) is installed

2. **Services do not start**
   - Verify Docker and Docker Compose are installed
   - Ensure ports 8081-8083, 6333-6334, 6379 are available
   - Check logs with `docker-compose logs`

3. **Caching not working**
   - Verify Redis is running with `docker ps | grep redis`
   - Check Redis connectivity with `docker exec redis redis-cli PING`
   - Review Redis logs with `docker logs redis`

4. **Qdrant issues**
   - Check Qdrant health with `curl http://localhost:6333/health`
   - Verify volume mounts with `docker inspect qdrant`
   - Check Qdrant logs with `docker logs qdrant`

5. **Embedding problems**
   - Ensure the Python virtual environment is activated
   - Verify Sentence Transformers installation
   - Check for network connectivity issues when downloading models

6. **Resource Constraints**
   - Monitor resource usage with `docker stats`
   - Adjust memory limits in docker-compose.yml if needed

7. **Dependency Issues**
   - If you encounter `bc` not found errors in scripts, install with `sudo apt install bc`
   - If you encounter `jq` not found errors in test scripts, install with `sudo apt install jq`
   - If Python scripts fail with import errors, ensure you've activated the virtual environment with `source python-env/bin/activate`
   - If Docker commands fail with permission errors, add your user to the docker group with `sudo usermod -aG docker $USER` and then log out and back in
   - If you get "python: command not found" errors, use `python3` instead as many Debian-based systems don't have a `python` command linked to Python 3
