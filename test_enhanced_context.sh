#!/bin/bash

# Test script for Enhanced Context Selection functionality with Session Management
# Updated for v0.2.4 (SQLite Database Integration)

echo "Testing Enhanced Context Selection with Session Management..."

# Ensure the scripts are executable
chmod +x context_selector.py devagent.py code_rag.py session_manager.py

# Set a unique project ID for testing
TEST_PROJECT_ID="enhanced-context-test"

echo "---------------------------------------"
echo "1. Creating a test project..."
./devagent.py project create "Enhanced Context Test Project" \
  --description "A project for testing enhanced context selection with sessions" \
  --tags python context test session \
  --id $TEST_PROJECT_ID 2>/dev/null

echo "---------------------------------------"
echo "2. Creating a test session..."
./devagent.py session create "Enhanced Context Test Session" \
  --description "A session for testing context selection" \
  --project-id $TEST_PROJECT_ID

echo "---------------------------------------"
echo "3. Testing context analysis..."
./devagent.py analyze "Create a DataProcessor class that can normalize data and handle missing values" \
  --project-id $TEST_PROJECT_ID

echo "---------------------------------------"
echo "4. Adding sample code to the project context..."
# Create a simple Python file with relevant code
cat > sample_data_processor.py << 'EOL'
class DataProcessor:
    """Process and transform data for analysis and modeling."""
    
    def __init__(self, data=None):
        """Initialize with optional data."""
        self.data = data
        
    def normalize(self, columns=None, method='min-max'):
        """Normalize data using the specified method."""
        if self.data is None:
            raise ValueError("No data to process")
        
        data_copy = self.data.copy()
        
        # Implementation of normalization
        return data_copy
        
    def fill_missing(self, strategy='mean', columns=None):
        """Fill missing values using the specified strategy."""
        if self.data is None:
            raise ValueError("No data to process")
        
        # Implementation of missing value handling
        return self.data
EOL

echo "Adding code file to project..."
./devagent.py project add-file $TEST_PROJECT_ID sample_data_processor.py \
  --description "Sample data processor class"

echo "Adding code file to vector database..."
./devagent.py add sample_data_processor.py --project-id $TEST_PROJECT_ID \
  --name "DataProcessor" --file-type python

echo "---------------------------------------"
echo "5. Testing basic context strategies..."
for strategy in semantic structural dependency balanced auto
do
  echo ""
  echo "Testing strategy: $strategy"
  ./devagent.py search "Create a machine learning model trainer class" \
    --project-id $TEST_PROJECT_ID \
    --context-strategy $strategy \
    --limit 3
done

echo "---------------------------------------"
echo "6. Testing session-aware code generation..."
./devagent.py generate "Write a function to extend the DataProcessor class with a method for outlier detection" \
  --project-id $TEST_PROJECT_ID \
  --context-strategy balanced

echo "---------------------------------------"
echo "7. Testing conversation meta-query detection..."
./devagent.py generate "Can you summarize what we've done so far in this session?" \
  --project-id $TEST_PROJECT_ID \
  --context-strategy auto

echo "---------------------------------------"
echo "8. Testing conversation context strategy explicitly..."
./devagent.py search "What have we discussed about data processing?" \
  --project-id $TEST_PROJECT_ID \
  --context-strategy conversation

echo "---------------------------------------"
echo "9. Testing session history awareness..."
# First, add a specific function that we can reference later
./devagent.py generate "Create a function called process_csv that loads and processes CSV files" \
  --project-id $TEST_PROJECT_ID \
  --context-strategy balanced

# Now, reference the function in a follow-up query to test history awareness
./devagent.py generate "Extend the process_csv function to handle Excel files too" \
  --project-id $TEST_PROJECT_ID \
  --context-strategy auto

echo "---------------------------------------"
echo "10. Testing SQLite database integration..."
# Try closing and reopening the session
echo "Closing current session..."
./devagent.py session close

echo "Listing available sessions..."
./devagent.py session list

echo "Reloading the session..."
SESSION_ID=$(ls ~/.devagent/sessions/ | head -1 | sed 's/\.yaml//')
./devagent.py session load $SESSION_ID

echo "Testing context after session reload..."
./devagent.py generate "What functions have we created so far?" \
  --project-id $TEST_PROJECT_ID \
  --context-strategy auto

echo "---------------------------------------"
echo "11. Cleaning up..."
echo "Closing session..."
./devagent.py session close

echo "Would you like to delete the test project? (y/n)"
read -r DELETE_PROJECT
if [[ $DELETE_PROJECT == "y" ]]; then
  echo "Deleting test project..."
  ./devagent.py project delete $TEST_PROJECT_ID --confirm
  echo "Deleted test project: $TEST_PROJECT_ID"
else
  echo "Test project kept for reference: $TEST_PROJECT_ID"
fi

# Clean up temporary file
rm -f sample_data_processor.py

echo "---------------------------------------"
echo "All tests completed!"
