#!/bin/bash
set -e

# Activate Python virtual environment
source /home/jenkins/venv/bin/activate

# Pass all arguments to the jenkins-agent entrypoint
exec /usr/local/bin/jenkins-agent "$@"
