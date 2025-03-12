#!/bin/bash

# Script to install Portainer CE as a standalone container

echo "Installing Portainer CE as a standalone container..."

# Stop and remove existing Portainer container if it exists
docker stop portainer 2>/dev/null
docker rm portainer 2>/dev/null

# Create a persistent volume for Portainer data
docker volume create portainer_data

# Run Portainer container
docker run -d \
  --name=portainer \
  --restart=always \
  -p 8000:8000 \
  -p 9000:9000 \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v portainer_data:/data \
  portainer/portainer-ce:latest

echo "Portainer CE is now running and accessible at:"
echo "http://$(hostname -I | awk '{print $1}'):9000"
echo ""
echo "This installation is independent of docker-compose and will continue"
echo "running even if you run 'docker-compose down' on your project."
