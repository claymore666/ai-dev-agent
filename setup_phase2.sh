#!/bin/bash

# Setup script for AI Development Agent POC - Phase 2
# This script sets up Qdrant and the embedding environment

# Check for required dependencies
echo "Checking for required dependencies..."
MISSING_DEPS=()

# Function to check if a command exists
check_command() {
    if ! command -v $1 &> /dev/null; then
        MISSING_DEPS+=($1)
        return 1
    fi
    return 0
}

# Check for required commands
check_command docker
check_command docker-compose
check_command python3
check_command pip3 || check_command pip
check_command git
check_command curl
check_command bc
check_command jq

# Check for python3-venv package
if ! python3 -m venv --help &> /dev/null; then
    MISSING_DEPS+=("python3-venv")
fi

# Print missing dependencies and suggest installation
if [ ${#MISSING_DEPS[@]} -gt 0 ]; then
    echo "The following required dependencies are missing:"
    for dep in "${MISSING_DEPS[@]}"; do
        echo "  - $dep"
    done
    
    echo ""
    echo "Please install them using:"
    echo "sudo apt-get update"
    echo "sudo apt-get install -y docker.io docker-compose python3-pip python3-venv git curl bc jq"
    echo ""
    read -p "Do you want to continue anyway? (y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Create directory structure
mkdir -p configs data/yacht data/redis data/qdrant logs python-env

# Check if Docker and Docker Compose are installed
if ! command -v docker &> /dev/null; then
    echo "Docker could not be found, please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "Docker Compose could not be found, please install Docker Compose first."
    exit 1
fi

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "Python 3 could not be found, please install Python 3 first."
    exit 1
fi

# Check if pip is installed
if ! command -v pip3 &> /dev/null && ! command -v pip &> /dev/null; then
    echo "pip could not be found, please install pip first."
    exit 1
fi

# Determine pip command
PIP_CMD="pip3"
if ! command -v pip3 &> /dev/null; then
    PIP_CMD="pip"
fi

# Set up Python virtual environment
echo "Setting up Python virtual environment..."
if ! python3 -m venv &> /dev/null; then
    echo "Python venv module not found. Installing..."
    $PIP_CMD install virtualenv
    python3 -m virtualenv python-env
else
    python3 -m venv python-env
fi

# Activate virtual environment and install dependencies
echo "Installing Python dependencies..."
source python-env/bin/activate
$PIP_CMD install -r requirements.txt

# Check if litellm_config.yaml exists, if not create it
if [ ! -f configs/litellm_config.yaml ]; then
    echo "Creating LiteLLM configuration file..."
    cp configs/litellm_config.yaml.template configs/litellm_config.yaml
    echo "Please update configs/litellm_config.yaml with your Ollama server IP address."
fi

# Set executable permissions for scripts
chmod +x *.sh
chmod +x *.py

# Create a sample .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating sample .env file..."
    cat > .env << EOL
# Environment variables for AI Development Agent

# Qdrant configuration
QDRANT_HOST=localhost
QDRANT_PORT=6333

# Embedding model configuration
EMBEDDING_MODEL=all-MiniLM-L6-v2
EMBEDDING_DIMENSION=384

# LiteLLM configuration
LITELLM_HOST=localhost
LITELLM_PORT=8081
EOL
    echo ".env file created. Please update with your configuration."
fi

echo "Setup completed successfully!"
echo "Next steps:"
echo "1. Update configs/litellm_config.yaml with your Ollama server IP address"
echo "2. Run './start.sh' to start the services"
echo "3. Run './test_qdrant.sh' to verify Qdrant is working properly"
echo "4. Run 'source python-env/bin/activate && python3 test_embedding.py' to test the embedding functionality"
