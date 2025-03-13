# Context-Extended AI Software Development Agent POC

This project implements a proof of concept for an AI software development agent that can maintain context across large Python projects. The system uses retrieval-augmented generation (RAG) to provide AI code assistance with extended context awareness, and is designed to run with limited resources (4GB RAM, 32GB disk) while connecting to a networked Ollama service.

**Current Version: 0.2.4** - Added SQLite Database Integration

## Key Features

- **Context Awareness**: Maintains understanding across large codebases
- **Code Generation**: Creates Python code informed by existing project context
- **Semantic Search**: Retrieves relevant code fragments based on meaning
- **Project Management**: Tracks projects, files, and generation history
- **Session Management**: Maintains persistent development sessions
- **SQLite Storage**: Robust database backend for projects and sessions
- **CLI Interface**: Unified command-line tool for all agent operations
- **Docker Integration**: Runs in containers with minimal resource requirements
- **Lightweight Design**: Optimized for systems with limited resources

## What's New in v0.2.4

- **SQLite-Based Storage**: Robust database for projects and sessions
- **Relational Schema**: Proper relationships between entities
- **Transaction Support**: Better data integrity and concurrency handling
- **Enhanced Queries**: Improved search and filtering capabilities
- **Automatic Migration**: Seamless transition from YAML files
- **Persistent Sessions**: Better tracking of active sessions across commands

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

### Phase 3 (Completed)

Phase 3 focuses on improving usability and extending functionality:

1. **Unified CLI** (Completed v0.2.1)
   - Comprehensive command-line interface
   - Access to all agent functionality
   - Consistent command format and documentation

2. **Project Configuration System** (Completed v0.2.1)
   - Persistent project storage
   - File tracking within projects
   - Metadata and history tracking
   - Project export/import capabilities

3. **Enhanced Context Selection** (Completed v0.2.2)
   - Smarter context filtering
   - Weighted context selection
   - Improved relevance of retrieved code
   - Multiple selection strategies

4. **Session Management** (Completed v0.2.3)
   - Persistent development sessions
   - Command history tracking
   - Context persistence across interactions
   - Session export/import capabilities

5. **SQLite Database Integration** (Completed v0.2.4)
   - Relational database storage
   - Transaction support
   - Improved data integrity
   - Better performance for complex queries

### Phase 4 (Planned)

Phase 4 will focus on quality and performance:

1. **Code Quality Assessment**
   - Analysis of generated code
   - Quality metrics and reporting
   - Suggestions for improvement

2. **Automated Testing**
   - Test case generation
   - Integration with testing frameworks
   - Validation of generated code

3. **Performance Optimization**
   - Benchmark for large codebases
   - Optimized context selection
   - Caching strategies for improved performance

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

## Usage

### DevAgent CLI

The unified CLI provides access to all functionality:

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

# Create a development session
devagent session create "Development" --project-id my-project

# View session history
devagent session history

# Close and resume sessions
devagent session close
devagent session load <session-id>
```

### Session Management

The session management system provides persistent development state:

```bash
# Create a new development session
devagent session create "Feature Development" --project-id my-project

# View active session information
devagent session info

# All commands automatically tracked in session history
devagent generate "Create a user authentication function" --output auth.py

# View command history
devagent session history

# Export session for backup or sharing
devagent session export --output my_session.json

# Close the current session
devagent session close

# List all available sessions
devagent session list

# Load a previous session
devagent session load <session-id>

# Import a session from another system
devagent session import colleague_session.json
```

### Project Workflow Example

A typical workflow using both Project Configuration and Session Management:

1. Create a project:
   ```bash
   devagent project create "Data Processing Library" --tags data python library
   ```

2. Create a session for this project:
   ```bash
   devagent session create "Initial Development" --project-id data-processing-library
   ```

3. Add existing code:
   ```bash
   devagent add data_loader.py --project-id data-processing-library
   ```

4. Generate new code with context (tracked in session):
   ```bash
   devagent generate "Create a CSV parser that handles quoted fields" \
     --output csv_parser.py
   ```

5. Pause development by closing the session:
   ```bash
   devagent session close
   ```

6. Later, resume development:
   ```bash
   # List available sessions
   devagent session list
   
   # Load the previous session
   devagent session load <session-id>
   
   # Continue development with full context
   devagent generate "Add JSON export functionality to the CSV parser" \
     --output json_exporter.py
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
├── session_manager.py      # Session Management System
├── code_rag.py             # RAG framework for code generation
├── context_selector.py     # Enhanced context selection
├── qdrant_helper.py        # Helper library for Qdrant
├── *.sh                    # Various utility scripts
└── README.md               # This file
```

## Data Storage

- Projects and sessions are stored in an SQLite database at `~/.devagent/devagent.db`
- Vector embeddings are stored in Qdrant
- LLM response caching uses Redis
- Configuration files are stored in the `configs/` directory

## Next Steps

Future development will focus on:
- Code quality metrics and automated testing integration
- Performance optimization for large codebases
- Enhanced user experience for common workflows
- Integration with additional development tools

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
