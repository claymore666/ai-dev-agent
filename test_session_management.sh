#!/bin/bash

# Test script for Session Management functionality

echo "Testing Session Management..."

# Ensure the scripts are executable
chmod +x devagent.py session_manager.py

echo "---------------------------------------"
echo "1. Creating a test project..."
TEST_PROJECT_ID="test-session-project"
./devagent.py project create "Test Session Project" --description "A project for testing session management" --tags python session test --id $TEST_PROJECT_ID

echo "---------------------------------------"
echo "2. Creating a test session..."
./devagent.py session create "Test Session" --description "A session for testing functionality" --project-id $TEST_PROJECT_ID --tags test

echo "---------------------------------------"
echo "3. Getting active session information..."
./devagent.py session info

echo "---------------------------------------"
echo "4. Running a command to be tracked in the session history..."
./devagent.py search "data processing" --project-id $TEST_PROJECT_ID --limit 2

echo "---------------------------------------"
echo "5. Generating code within the session context..."
./devagent.py generate "Write a simple data processing function that removes duplicates from a list" --project-id $TEST_PROJECT_ID

echo "---------------------------------------"
echo "6. Viewing session history..."
./devagent.py session history

echo "---------------------------------------"
echo "7. Exporting the session..."
EXPORT_FILE="test_session_export.json"
./devagent.py session export --output $EXPORT_FILE

echo "---------------------------------------"
echo "8. Closing the session..."
./devagent.py session close

echo "---------------------------------------"
echo "9. Listing available sessions..."
./devagent.py session list

echo "---------------------------------------"
echo "10. Loading the session back..."
# Get the session ID from the active session info (step 3) output 
# or from the list (step 9) and replace SESSION_ID with it
SESSION_ID=$(ls ~/.devagent/sessions/ | head -1 | sed 's/\.yaml//')
./devagent.py session load $SESSION_ID

echo "---------------------------------------"
echo "11. Resetting the session..."
./devagent.py session reset

echo "---------------------------------------"
echo "12. Checking history after reset..."
./devagent.py session history

echo "---------------------------------------"
echo "13. Importing a previously exported session..."
./devagent.py session import $EXPORT_FILE

echo "---------------------------------------"
echo "All tests completed!"

# Cleanup (commented out to allow inspection after test)
# echo "Cleaning up..."
# rm -f $EXPORT_FILE
# ./devagent.py session delete $SESSION_ID --confirm
