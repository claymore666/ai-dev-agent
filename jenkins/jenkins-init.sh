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
