#!/bin/bash

# Test script for Enhanced Context Selection functionality

echo "Testing Enhanced Context Selection..."

# Ensure the scripts are executable
chmod +x context_selector.py devagent.py code_rag.py

echo "---------------------------------------"
echo "1. Testing context analysis..."
./devagent.py analyze "Create a DataProcessor class that can normalize data and handle missing values" --project-id test-project

echo "---------------------------------------"
echo "2. Testing enhanced code search..."
./devagent.py search "Implement a function to load CSV data" --project-id test-project --context-strategy balanced

echo "---------------------------------------"
echo "3. Testing enhanced code generation..."
./devagent.py generate "Write a function to combine data loading and processing capabilities" --project-id test-project --context-strategy dependency

echo "---------------------------------------"
echo "4. Creating a test project..."
# Create a test project if it doesn't exist
./devagent.py project create "Context Test Project" --description "A project for testing enhanced context selection" --tags python context test --id context-test-project 2>/dev/null

# Test the analyze command
./devagent.py analyze "Create a data processing pipeline with normalization and missing value handling" --project-id context-test-project

echo "---------------------------------------"
echo "5. Testing different context strategies..."
for strategy in semantic structural dependency balanced auto
do
  echo ""
  echo "Testing strategy: $strategy"
  ./devagent.py search "Create a machine learning model trainer class" --context-strategy $strategy --limit 3
done

echo "---------------------------------------"
echo "All tests completed!"
