# Context-Extended AI Software Development Agent POC

This project implements a proof of concept for an AI software development agent that can maintain context across large Python projects. The system uses retrieval-augmented generation (RAG) to provide AI code assistance with extended context awareness, and is designed to run with limited resources (4GB RAM, 32GB disk) while connecting to a networked Ollama service.

**Current Version: 0.2.1** - Added CLI & Project Configuration System

## Key Features

- **Context Awareness**: Maintains understanding across large codebases
- **Code Generation**: Creates Python code informed by existing project context
- **Semantic Search**: Retrieves relevant code fragments based on meaning
- **Project Management**: Tracks projects, files, and generation history
- **CLI Interface**: Unified command-line tool for all agent operations
- **Docker Integration**: Runs in containers with minimal resource requirements
- **Lightweight Design**: Optimized for systems with limited resources

## What's New in v0.2.1

- **Unified CLI Interface**: A comprehensive command-line tool for all DevAgent operations
- **Project Configuration System**: Persistent project management with metadata tracking
- **File Tracking**: Track files and their associations with projects
- **Generation History**: Record code generation requests and outputs
- **Import/Export**: Share project configurations between systems

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

### Phase 2 (Completed)

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

### Phase 3 (In Progress)

Phase 3 focuses on improving usability and extending functionality:

1. **Unified CLI** (Completed v0.2.1)
   - Comprehensive command-line interface
   - Access to all agent functionality
   - Consistent command format and documentation

2. **Project Configuration System** (Completed v0.2.1)
   - YAML-based project storage
   - File tracking within projects
   - Metadata and history tracking
   - Project export/import capabilities

3. **Enhanced Context Selection** (Planned)
   - Smarter context filtering
   - Weighted context selection
   - Improved relevance of retrieved code

4. **Session Management** (Planned)
   - Persistent development sessions
   - Session state tracking
   - Resumable operations

5. **Code Quality Assessment** (Planned)
   - Analysis of generated code
   - Quality metrics and reporting
   - Suggestions for improvement

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
   ./start_phase2.sh
   ```

5. Install the DevAgent CLI:
   ```bash
   chmod +x install_cli.sh
   ./install_cli.sh
   ```

6. Test the Project Configuration System:
   ```bash
   chmod +x test_project_config.sh
   ./test_project_config.sh
   ```

## Usage

### DevAgent CLI

The new unified CLI provides access to all functionality:

```bash
# Check system status
devagent status

# Create a new project
devagent project create "My Project" --description "Description" --tags python api

# Add code to a project
devagent add my_file.py --project-id my-project --name "MyClass"

# Generate code with context
devagent generate "Write a function to parse CSV files" --project-id my-project --output result.py

# Search for code
devagent search "data processing" --project-id my-project

# Manage projects
devagent project list
devagent project get my-project
devagent project export my-project --output my-project.json
```

For full CLI documentation, see [CLI_README.md](CLI_README.md).

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

## Project Workflow Example

A typical workflow using the Project Configuration System:

1. Create a project:
   ```bash
   devagent project create "Data Processing Library" --tags data python library
   ```

2. Add existing code:
   ```bash
   devagent project add-file data-processing-library data_loader.py
   devagent add data_loader.py --project-id data-processing-library
   ```

3. Generate new code with context:
   ```bash
   devagent generate "Create a CSV parser that handles quoted fields" \
     --project-id data-processing-library \
     --output csv_parser.py
   ```

4. Add the generated code to the project's context:
   ```bash
   devagent add csv_parser.py --project-id data-processing-library
   ```

5. Generate more code that builds on previous work:
   ```bash
   devagent generate "Add JSON export functionality to the CSV parser" \
     --project-id data-processing-library \
     --output json_exporter.py
   ```

6. Export the project:
   ```bash
   devagent project export data-processing-library
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
├── devagent.py             # Main CLI tool
├── project_manager.py      # Project Configuration System
├── code_rag.py             # RAG framework for code generation
├── qdrant_helper.py        # Helper library for Qdrant
├── *.sh                    # Various utility scripts
└── README.md               # This file
```

## Next Steps

Future development will focus on the remaining Phase 3 components:
- Enhanced context selection for more relevant code retrieval
- Session management for persistent development sessions
- Code quality metrics and testing framework integration
- Iterative refinement of generated code

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

3. **CLI tool issues**
   - Ensure the Python virtual environment is activated
   - Verify all required Python dependencies are installed
   - Check `devagent.log` for detailed error information

## License

This project is released under the MIT License. See the [LICENSE](LICENSE) file for details.
