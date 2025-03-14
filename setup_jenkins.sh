#!/bin/bash

# Setup script for Jenkins CI/CD environment

# Set colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Setting up Jenkins CI/CD environment...${NC}"

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
check_command curl

# Print missing dependencies and suggest installation
if [ ${#MISSING_DEPS[@]} -gt 0 ]; then
    echo -e "${RED}The following required dependencies are missing:${NC}"
    for dep in "${MISSING_DEPS[@]}"; do
        echo "  - $dep"
    done
    
    echo ""
    echo "Please install them using:"
    echo "sudo apt-get update"
    echo "sudo apt-get install -y docker.io docker-compose curl"
    echo ""
    read -p "Do you want to continue anyway? (y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Create Jenkins directory structure
echo "Creating directory structure..."
mkdir -p jenkins/jenkins-config

# Create docker-compose.yml
echo "Creating docker-compose.yml..."
cat > jenkins/docker-compose.yml << 'EOL'
version: '3.8'

services:
  jenkins:
    image: jenkins/jenkins:lts-jdk17
    container_name: jenkins
    restart: unless-stopped
    user: root  # Needed to access Docker socket
    privileged: true  # Required for Docker-in-Docker capability
    ports:
      - "8090:8080"  # Jenkins web UI
      - "50000:50000"  # Jenkins agent port
    volumes:
      - jenkins_home:/var/jenkins_home
      - /var/run/docker.sock:/var/run/docker.sock  # Allow Jenkins to use host Docker
      - /usr/bin/docker:/usr/bin/docker  # Mount Docker binary
      - ./jenkins-config:/var/jenkins_config
      - ./jenkins-init.sh:/usr/local/bin/jenkins-init.sh
    environment:
      - JAVA_OPTS=-Djenkins.install.runSetupWizard=false -Dhudson.plugins.git.GitSCM.ALLOW_LOCAL_CHECKOUT=true
      - JENKINS_OPTS=--argumentsRealm.roles.user=admin --argumentsRealm.roles.admin=admin --argumentsRealm.passwd.admin=admin
      - CASC_JENKINS_CONFIG=/var/jenkins_config
    networks:
      - jenkins-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/login"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
    command: bash -c "/usr/local/bin/jenkins-init.sh && /usr/local/bin/jenkins.sh"

  sonarqube:
    image: sonarqube:latest
    container_name: sonarqube
    restart: unless-stopped
    ports:
      - "9000:9000"
    environment:
      - SONAR_ES_BOOTSTRAP_CHECKS_DISABLE=true
    volumes:
      - sonarqube_data:/opt/sonarqube/data
      - sonarqube_logs:/opt/sonarqube/logs
      - sonarqube_extensions:/opt/sonarqube/extensions
    networks:
      - jenkins-network
    depends_on:
      - jenkins

networks:
  jenkins-network:
    driver: bridge
    name: jenkins-network

volumes:
  jenkins_home:
    driver: local
  sonarqube_data:
    driver: local
  sonarqube_logs:
    driver: local
  sonarqube_extensions:
    driver: local
EOL

# Create jenkins-init.sh
echo "Creating jenkins-init.sh..."
cat > jenkins/jenkins-init.sh << 'EOL'
#!/bin/bash
# Jenkins initialization script

# Install necessary plugins
install_plugins() {
  jenkins-plugin-cli --plugins \
    git \
    workflow-aggregator \
    pipeline-stage-view \
    blueocean \
    docker-workflow \
    docker-plugin \
    docker-build-step \
    sonar \
    github \
    github-branch-source \
    python \
    performance \
    timestamper \
    ansicolor \
    warnings-ng \
    pipeline-utility-steps \
    configuration-as-code
}

# Wait for Jenkins to start up
wait_for_jenkins() {
  echo "Waiting for Jenkins to start up..."
  until curl -s -f http://localhost:8080/login > /dev/null; do
    sleep 5
  done
  echo "Jenkins started successfully!"
}

# Generate Jenkinsfile template
create_jenkinsfile_template() {
  mkdir -p /var/jenkins_home/jobTemplates
  cat > /var/jenkins_home/jobTemplates/Jenkinsfile.template << 'EOF'
pipeline {
    agent {
        docker {
            image 'python:3.10-slim'
            args '-v /var/run/docker.sock:/var/run/docker.sock -v ${WORKSPACE}:/workspace'
        }
    }
    
    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }
        
        stage('Environment Setup') {
            steps {
                sh '''
                python -m pip install --upgrade pip
                pip install -r requirements.txt
                '''
            }
        }
        
        stage('Lint & Static Analysis') {
            steps {
                sh '''
                pip install pylint
                pylint --disable=C0111,C0103 *.py || true
                '''
            }
        }
        
        stage('Unit Tests') {
            steps {
                sh '''
                pip install pytest pytest-cov
                pytest --cov=. --cov-report=xml:coverage.xml
                '''
            }
        }
        
        stage('Integration Tests') {
            steps {
                sh '''
                chmod +x test_fixes.sh
                ./test_fixes.sh
                '''
            }
        }
        
        stage('SonarQube Analysis') {
            steps {
                withSonarQubeEnv('SonarQube') {
                    sh '''
                    pip install pylint
                    pylint --output-format=parseable --reports=n --exit-zero *.py > pylint-report.txt
                    '''
                    
                    sh '''
                    sonar-scanner \
                      -Dsonar.projectKey=ai-dev-agent \
                      -Dsonar.sources=. \
                      -Dsonar.python.coverage.reportPaths=coverage.xml \
                      -Dsonar.python.pylint.reportPath=pylint-report.txt
                    '''
                }
            }
        }
        
        stage('Build Docker Images') {
            steps {
                sh 'docker-compose build'
            }
        }
        
        stage('Performance Tests') {
            steps {
                sh '''
                pip install locust
                # Run locust in headless mode if needed
                # locust -f performance/locustfile.py --headless -u 10 -r 1 --run-time 1m
                echo "Performance tests would run here"
                '''
            }
        }
    }
    
    post {
        always {
            archiveArtifacts artifacts: 'coverage.xml, pylint-report.txt', allowEmptyArchive: true
            junit 'test-reports/*.xml'
        }
    }
}
EOF
}

# Main execution flow
main() {
  # Ensure we have execution permissions
  chmod +x /var/jenkins_home

  # Install plugins
  install_plugins
  
  # Create Jenkinsfile template
  create_jenkinsfile_template
  
  # Apply configuration
  echo "Jenkins initialization completed!"
}

# Run main function
main
EOL

# Create jenkins-config.yaml
echo "Creating jenkins-config.yaml..."
cat > jenkins/jenkins-config/jenkins.yaml << 'EOL'
jenkins:
  systemMessage: "Context-Extended AI Software Development Agent CI/CD Environment"
  securityRealm:
    local:
      allowsSignup: false
      users:
        - id: admin
          password: admin
  authorizationStrategy:
    loggedInUsersCanDoAnything:
      allowAnonymousRead: false
  remotingSecurity:
    enabled: true
  
  nodes:
    - permanent:
        name: "docker-agent"
        remoteFS: "/home/jenkins/agent"
        launcher:
          jnlp:
            workDirSettings:
              disabled: true
              failIfWorkDirIsMissing: false
              internalDir: "remoting"
        nodeProperties:
          - envVars:
              env:
                - key: "PATH"
                  value: "/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"

tool:
  git:
    installations:
      - name: "Default"
        home: "git"
  
  sonarRunnerInstallation:
    installations:
      - name: "SonarQube Scanner"
        properties:
          - installSource:
              installers:
                - sonarRunnerInstaller:
                    id: "4.7.0.2747"

jobs:
  - script: >
      folder('ai-dev-agent')
  
  - script: >
      pipelineJob('ai-dev-agent/main-pipeline') {
        definition {
          cps {
            script(readFileFromWorkspace('/var/jenkins_home/jobTemplates/Jenkinsfile.template'))
            sandbox()
          }
        }
        
        properties {
          githubProjectUrl('https://github.com/yourusername/ai-dev-agent')
        }
      }

unclassified:
  sonarGlobalConfiguration:
    buildWrapperEnabled: true
    installations:
      - name: "SonarQube"
        serverUrl: "http://sonarqube:9000"
        credentialsId: "sonarqube-token"
        webhooks:
          - name: "Jenkins webhook"
            secret: "your-secret-token"
EOL

# Make scripts executable
echo "Making scripts executable..."
chmod +x jenkins/jenkins-init.sh

# Create README.md for Jenkins setup
echo "Creating README.md for Jenkins..."
cat > jenkins/README.md << 'EOL'
# Jenkins CI/CD for AI Development Agent

This folder contains the Jenkins CI/CD setup for the Context-Extended AI Software Development Agent project.

## Getting Started

1. Start the Jenkins stack:
   ```bash
   docker-compose up -d
   ```

2. Access the Jenkins UI:
   - URL: http://localhost:8090
   - Username: admin
   - Password: admin

3. Access SonarQube:
   - URL: http://localhost:9000
   - Default credentials: admin/admin

## Customizing

- Edit `jenkins-config/jenkins.yaml` to modify Jenkins configuration
- Edit `jenkins-init.sh` to modify the initialization process and plugins

## Contents

- `docker-compose.yml` - Defines the Jenkins and SonarQube containers
- `jenkins-init.sh` - Initialization script that installs plugins and sets up templates
- `jenkins-config/jenkins.yaml` - Configuration as Code file for Jenkins

## Integration with the AI Development Agent

This Jenkins setup is configured to work with the AI Development Agent project:
- It can run the project's test scripts
- It can build Docker images
- It integrates with SonarQube for code quality analysis
EOL

echo -e "${GREEN}Jenkins CI/CD environment setup completed!${NC}"
echo ""
echo "To start Jenkins:"
echo "  cd jenkins"
echo "  docker-compose up -d"
echo ""
echo "Jenkins will be available at: http://localhost:8090"
echo "Username: admin"
echo "Password: admin"
echo ""
echo "SonarQube will be available at: http://localhost:9000"
echo "Default credentials: admin/admin"
