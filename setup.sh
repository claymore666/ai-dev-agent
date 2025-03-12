#!/bin/bash

# Setup script for AI Development Agent POC
# This script creates necessary directories and configuration files

# Create directory structure
mkdir -p configs data/yacht data/redis logs

# Check if Docker and Docker Compose are installed
if ! command -v docker &> /dev/null; then
    echo "Docker could not be found, please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "Docker Compose could not be found, please install Docker Compose first."
    exit 1
fi

# Check if litellm_config.yaml exists, if not create it
if [ ! -f configs/litellm_config.yaml ]; then
    echo "Creating LiteLLM configuration file..."
    cp configs/litellm_config.yaml.template configs/litellm_config.yaml
    echo "Please update configs/litellm_config.yaml with your Ollama server IP address."
fi

# Set executable permissions
chmod +x start.sh
chmod +x stop.sh

echo "Setup completed successfully. Please configure your Ollama IP in configs/litellm_config.yaml"
echo "Then run ./start.sh to start the services."
