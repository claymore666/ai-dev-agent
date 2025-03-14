#!/bin/bash

# Script to configure SonarQube for the AI Development Agent

# Set colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Configuring SonarQube for AI Development Agent...${NC}"

# Check if SonarQube is running
echo "Checking SonarQube status..."
SONAR_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:9100)

if [ "$SONAR_STATUS" != "200" ]; then
    echo -e "${RED}SonarQube is not running. Please start SonarQube first.${NC}"
    echo "You can start it with: cd jenkins && docker-compose up -d"
    exit 1
fi

echo "SonarQube is running. Waiting for it to be fully initialized..."
# Wait for SonarQube to be fully initialized
sleep 10

# Login to SonarQube
echo "Logging in to SonarQube with default credentials (admin/admin)..."
TOKEN_RESPONSE=$(curl -s -X POST -u admin:admin "http://localhost:9100/api/user_tokens/generate" \
  -d "name=jenkins-token" \
  -d "login=admin")

# Extract token
TOKEN=$(echo $TOKEN_RESPONSE | grep -o '"token":"[^"]*"' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
    echo -e "${RED}Failed to generate SonarQube token.${NC}"
    echo "Please check SonarQube logs and make sure it is properly initialized."
    exit 1
fi

echo -e "${GREEN}Successfully generated SonarQube token.${NC}"

# Create project
echo "Creating AI Development Agent project in SonarQube..."
PROJECT_KEY="ai-dev-agent"
PROJECT_NAME="AI Development Agent"

curl -s -X POST -u $TOKEN: "http://localhost:9100/api/projects/create" \
  -d "name=$PROJECT_NAME" \
  -d "project=$PROJECT_KEY"

echo -e "${GREEN}Project created successfully.${NC}"

# Configure quality profiles
echo "Configuring Python quality profile..."
PROFILE_KEY=$(curl -s -u $TOKEN: "http://localhost:9100/api/qualityprofiles/search?language=py" | \
  grep -o '"key":"[^"]*"' | head -1 | cut -d'"' -f4)

if [ -n "$PROFILE_KEY" ]; then
    echo "Setting $PROFILE_KEY as default for Python projects..."
    curl -s -X POST -u $TOKEN: "http://localhost:9100/api/qualityprofiles/set_default" \
      -d "qualityProfile=Sonar%20way" \
      -d "language=py"
fi

# Configure quality gate
echo "Configuring quality gate..."
GATE_ID=$(curl -s -u $TOKEN: "http://localhost:9100/api/qualitygates/list" | \
  grep -o '"id":[0-9]*,"name":"Sonar way"' | grep -o '[0-9]*')

if [ -n "$GATE_ID" ]; then
    echo "Setting 'Sonar way' as default quality gate..."
    curl -s -X POST -u $TOKEN: "http://localhost:9100/api/qualitygates/set_as_default" \
      -d "id=$GATE_ID"
fi

# Save token to a file for Jenkins
echo "Saving SonarQube token for Jenkins configuration..."
TOKEN_FILE="jenkins/sonarqube-token.txt"
echo "$TOKEN" > $TOKEN_FILE
chmod 600 $TOKEN_FILE

echo -e "${GREEN}SonarQube configuration completed!${NC}"
echo -e "The SonarQube token has been saved to: ${YELLOW}$TOKEN_FILE${NC}"
echo "Please update the Jenkins credentials with this token."
echo ""
echo "SonarQube is configured and ready to analyze the AI Development Agent code."
echo "You can access SonarQube at: http://localhost:9100"
echo "Use Jenkins pipeline with SonarQube Scanner to analyze code quality."
