#!/bin/bash

# Test script for the Project Configuration System

echo "Testing Project Configuration System..."

# Ensure the scripts are executable
chmod +x devagent.py
chmod +x project_manager.py

# Clear any existing test projects
echo "Cleaning up any existing test projects..."
PROJECT_ID="test-project-config"
./devagent.py project delete $PROJECT_ID --confirm 2>/dev/null

echo "---------------------------------------"
echo "1. Creating a test project..."
./devagent.py project create "Test Project Config" --description "A project for testing configuration" --tags python cli test --id $PROJECT_ID

echo "---------------------------------------"
echo "2. Listing projects (should include our new project)..."
./devagent.py project list

echo "---------------------------------------"
echo "3. Getting project details..."
./devagent.py project get $PROJECT_ID

echo "---------------------------------------"
echo "4. Creating a sample Python file to add to the project..."
SAMPLE_FILE="test_sample.py"
cat > $SAMPLE_FILE << EOL
#!/usr/bin/env python3
"""
Sample Python file for testing the project configuration system.
"""

def hello_world():
    """Print a hello world message."""
    print("Hello, world!")

if __name__ == "__main__":
    hello_world()
EOL

echo "5. Adding the file to the project..."
./devagent.py project add-file $PROJECT_ID $SAMPLE_FILE --description "Sample file for testing"

echo "---------------------------------------"
echo "6. Getting project details to verify the file was added..."
./devagent.py project get $PROJECT_ID

echo "---------------------------------------"
echo "7. Adding the file to the project's code context..."
./devagent.py add $SAMPLE_FILE --project-id $PROJECT_ID --name "hello_world"

echo "---------------------------------------"
echo "8. Generating some code with the project context..."
./devagent.py generate "Write a function that extends hello_world to greet a specific person by name" --project-id $PROJECT_ID

echo "---------------------------------------"
echo "9. Exporting the project configuration..."
./devagent.py project export $PROJECT_ID --output "${PROJECT_ID}_export.json"

echo "---------------------------------------"
echo "10. Updating the project..."
./devagent.py project update $PROJECT_ID --description "Updated description" --tags python cli test updated

echo "---------------------------------------"
echo "11. Getting project details to verify the update..."
./devagent.py project get $PROJECT_ID

echo "---------------------------------------"
echo "All tests completed!"

# Optionally delete the test project
# Uncomment the following line to clean up after testing
# ./devagent.py project delete $PROJECT_ID --confirm
