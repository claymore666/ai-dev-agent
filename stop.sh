#!/bin/bash

# Stop services for AI Development Agent POC

echo "Stopping AI Development Agent services..."

# Stop docker containers
docker-compose down

echo "All services have been stopped."
