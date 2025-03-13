#!/bin/bash

# Test script for SQLite-based Project Management functionality

echo "Testing SQLite-based Project Management..."

# Ensure the scripts are executable
chmod +x devagent.py project_manager.py

echo "---------------------------------------"
echo "1. Creating a test project..."
PROJECT_ID="sqlite-test-project"
./project_manager.py create "SQLite Test Project" --description "A project for testing SQLite functionality" --tags python sqlite test --id $PROJECT_ID

echo "---------------------------------------"
echo "2. Getting project details..."
./project_manager.py get $PROJECT_ID

echo "---------------------------------------"
echo "3. Creating a sample Python file to add to the project..."
SAMPLE_FILE="test_sample.py"
cat > $SAMPLE_FILE << EOL
#!/usr/bin/env python3
"""
Sample Python file for testing the SQLite project manager.
"""

def hello_world():
    """Print a hello world message."""
    print("Hello, world!")

if __name__ == "__main__":
    hello_world()
EOL

echo "4. Adding the file to the project..."
./project_manager.py add-file $PROJECT_ID $SAMPLE_FILE --description "Sample file for testing"

echo "---------------------------------------"
echo "5. Getting project details to verify the file was added..."
./project_manager.py get $PROJECT_ID

echo "---------------------------------------"
echo "6. Updating the project..."
./project_manager.py update $PROJECT_ID --description "Updated description" --tags python sqlite test updated

echo "---------------------------------------"
echo "7. Getting project details to verify the update..."
./project_manager.py get $PROJECT_ID

echo "---------------------------------------"
echo "8. Exporting the project configuration..."
./project_manager.py export $PROJECT_ID --output "${PROJECT_ID}_export.json"

echo "---------------------------------------"
echo "9. Listing all projects..."
./project_manager.py list

echo "---------------------------------------"
echo "10. Searching for projects with 'sqlite' tag..."
./project_manager.py search --tags sqlite

echo "---------------------------------------"
echo "11. Creating another test project..."
PROJECT_ID2="sqlite-test-project2"
./project_manager.py create "SQLite Test Project 2" --description "Another project for testing" --tags python sqlite --id $PROJECT_ID2

echo "---------------------------------------"
echo "12. Listing all projects again..."
./project_manager.py list

echo "---------------------------------------"
echo "13. Deleting the second test project..."
./project_manager.py delete $PROJECT_ID2

echo "---------------------------------------"
echo "14. Verifying the second project was deleted..."
./project_manager.py list

echo "---------------------------------------"
echo "All tests completed!"

# Optionally clean up
# echo "Cleaning up..."
# rm -f $SAMPLE_FILE ${PROJECT_ID}_export.json
# ./project_manager.py delete $PROJECT_ID
