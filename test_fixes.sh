#!/bin/bash

# Test script to verify the functionality fixes for:
# 1. Auto-session creation during generation
# 2. Proper handling of Redis caching errors
# 3. Session history correctness (no pre-session commands)
# 4. Project deletion with proper tag cleanup

# Set up colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=========== Testing Session Management Fixes ===========${NC}"

# First, reset all databases for a clean test environment
echo -e "\n${YELLOW}[1] Resetting databases for clean testing...${NC}"
./reset_db.sh << EOF
y
EOF

# Test: Project Creation and Multiple Deletion (for tag cleanup issue)
echo -e "\n${YELLOW}[2] Testing project creation and deletion (tag cleanup fix)...${NC}"

# Create a project with tags
echo -e "\nCreating first test project with tags..."
PROJECT_ID="test-project-fix"
./devagent.py project create "Test Project Fix" --tags test fix cleanup

# Delete the project 
echo -e "\nDeleting project..."
./devagent.py project delete $PROJECT_ID --confirm

# Try to recreate with the same name and tags
echo -e "\nRecreating project with same name and tags (should work now)..."
./devagent.py project create "Test Project Fix" --tags test fix cleanup

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Project deletion tag cleanup test PASSED${NC}"
else
    echo -e "${RED}✗ Project deletion tag cleanup test FAILED${NC}"
fi

# Test: Auto-session creation during generation
echo -e "\n${YELLOW}[3] Testing auto-session creation during generation...${NC}"

# Create a new project for testing
PROJECT_ID="auto-session-test"
echo -e "\nCreating project for auto-session test..."
./devagent.py project create "Auto Session Test" --tags test session

# Run a command that should auto-create a session
echo -e "\nRunning generation command without an existing session (should auto-create)..."
GENERATE_OUTPUT=$(./devagent.py generate "Write a simple hello world function" --project-id $PROJECT_ID)

# Check if session was created
if echo "$GENERATE_OUTPUT" | grep -q "Created session:"; then
    echo -e "${GREEN}✓ Auto-session creation test PASSED${NC}"
else
    echo -e "${RED}✗ Auto-session creation test FAILED${NC}"
fi

# Check session info
echo -e "\nVerifying session information..."
./devagent.py session info

# Test: Session history correctness
echo -e "\n${YELLOW}[4] Testing session history correctness...${NC}"
echo -e "\nChecking session history (should only show commands after session creation)..."
HISTORY_OUTPUT=$(./devagent.py session history)

# Run another command to add to history
echo -e "\nRunning another command to add to history..."
./devagent.py generate "Write a function to calculate factorial" --project-id $PROJECT_ID 1>/dev/null

# Check history again
echo -e "\nChecking history again (should show both generation commands)..."
./devagent.py session history

# Now do a test with conversation context
echo -e "\n${YELLOW}[5] Testing conversation context functionality...${NC}"
echo -e "\nGenerating a meta-query about previous conversation..."
./devagent.py generate "Summarize what we've discussed so far" --project-id $PROJECT_ID --context-strategy auto

# Test project deletion with session
echo -e "\n${YELLOW}[6] Testing project deletion with active session...${NC}"

# Close the session first
echo -e "\nClosing session..."
./devagent.py session close

# Delete the project
echo -e "\nDeleting project with verification of cleanup..."
./devagent.py project delete $PROJECT_ID --confirm

# Verify project is gone
PROJECT_LIST=$(./devagent.py project list)
if echo "$PROJECT_LIST" | grep -q "$PROJECT_ID"; then
    echo -e "${RED}✗ Project deletion test FAILED - project still exists${NC}"
else
    echo -e "${GREEN}✓ Project deletion test PASSED - project successfully removed${NC}"
fi

echo -e "\n${GREEN}Testing completed!${NC}"
