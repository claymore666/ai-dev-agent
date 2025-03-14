FROM jenkins/agent:latest

USER root

# Install Python and essential tools
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    curl \
    git \
    jq \
    wget \
    sudo \
    && rm -rf /var/lib/apt/lists/*

# Install Docker
RUN curl -fsSL https://get.docker.com -o get-docker.sh && \
    sh get-docker.sh && \
    rm get-docker.sh

# Install Docker Compose
RUN curl -L "https://github.com/docker/compose/releases/download/v2.20.3/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose && \
    chmod +x /usr/local/bin/docker-compose

# Install SonarQube Scanner
RUN mkdir -p /opt/sonar-scanner && \
    wget https://binaries.sonarsource.com/Distribution/sonar-scanner-cli/sonar-scanner-cli-4.7.0.2747-linux.zip -O /tmp/sonar-scanner.zip && \
    unzip /tmp/sonar-scanner.zip -d /opt/sonar-scanner && \
    rm /tmp/sonar-scanner.zip && \
    mv /opt/sonar-scanner/sonar-scanner-4.7.0.2747-linux /opt/sonar-scanner/current && \
    ln -s /opt/sonar-scanner/current/bin/sonar-scanner /usr/local/bin/sonar-scanner

# Update pip to latest version
RUN python3 -m pip install --upgrade pip

# Install common Python packages for AI development
RUN python3 -m pip install \
    pytest \
    pytest-cov \
    pylint \
    black \
    mypy \
    flake8 \
    numpy \
    pandas \
    scikit-learn \
    requests \
    pyyaml \
    tqdm

# Install Python packaging tools
RUN python3 -m pip install \
    wheel \
    setuptools \
    twine \
    build

# Add jenkins user to docker group
RUN usermod -aG docker jenkins

# Make sure jenkins user can use sudo
RUN echo "jenkins ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers

USER jenkins

# Set up Python environment for jenkins user
RUN python3 -m venv /home/jenkins/venv

# Add Python venv to PATH
ENV PATH="/home/jenkins/venv/bin:${PATH}"

# Custom entrypoint for environment setup
COPY entrypoint.sh /home/jenkins/entrypoint.sh
USER root
RUN chmod +x /home/jenkins/entrypoint.sh
USER jenkins

ENTRYPOINT ["/home/jenkins/entrypoint.sh"]
