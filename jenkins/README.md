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
