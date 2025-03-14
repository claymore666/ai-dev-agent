pipeline {
    agent {
        docker {
            image 'python:3.10-slim'
            args '-v /var/run/docker.sock:/var/run/docker.sock -v ${WORKSPACE}:/workspace'
        }
    }
    
    environment {
        PYTHONPATH = "${WORKSPACE}"
    }
    
    options {
        timeout(time: 1, unit: 'HOURS')
        ansiColor('xterm')
        timestamps()
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
                if [ -f requirements.txt ]; then
                    pip install -r requirements.txt
                else
                    echo "requirements.txt not found, installing minimal dependencies"
                    pip install pytest pytest-cov pylint
                fi
                
                # Install Docker Compose if not present
                if ! command -v docker-compose &> /dev/null; then
                    pip install docker-compose
                fi
                '''
