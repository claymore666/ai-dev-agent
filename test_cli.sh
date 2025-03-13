#!/bin/bash

# Test script for the DevAgent CLI tool

echo "Testing DevAgent CLI tool..."

# Ensure the script is executable
chmod +x devagent.py

# Run various test commands
echo "---------------------------------------"
echo "Testing 'status' command..."
./devagent.py status

echo "---------------------------------------"
echo "Testing 'project create' command..."
./devagent.py project create "Test Project" -d "A project for testing the CLI"

echo "---------------------------------------"
echo "Testing 'project list' command..."
./devagent.py project list

echo "---------------------------------------"
echo "Testing 'init' command..."
./devagent.py init

echo "---------------------------------------"
echo "All tests completed!"
