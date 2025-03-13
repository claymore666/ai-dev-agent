#!/bin/bash

# Installation script for the DevAgent CLI tool

echo "Installing DevAgent CLI tool..."

# Make the script executable
chmod +x devagent.py

# Create a symlink in /usr/local/bin if the user has permission
if [ -d "/usr/local/bin" ] && [ -w "/usr/local/bin" ]; then
    echo "Creating symlink in /usr/local/bin..."
    ln -sf "$(pwd)/devagent.py" /usr/local/bin/devagent
    echo "DevAgent CLI installed successfully! You can run it using 'devagent' from anywhere."
else
    echo "Cannot create symlink in /usr/local/bin (permission denied)."
    echo "You can run the DevAgent CLI using './devagent.py' from this directory."
    echo "Or add this directory to your PATH to run it from anywhere."
fi

# Check if the virtual environment exists
if [ -d "python-env" ]; then
    echo "Found Python virtual environment."
    echo "Remember to activate it before using DevAgent CLI:"
    echo "  source python-env/bin/activate"
else
    echo "Warning: Python virtual environment not found."
    echo "Make sure to run setup_phase2.sh first to set up the environment."
fi

# Display usage examples
echo ""
echo "Usage examples:"
echo "  devagent status                # Check system status"
echo "  devagent search 'csv parser'   # Search for code related to CSV parsing"
echo "  devagent generate 'Write a function to parse CSV files' -p your-project-id   # Generate code with context"
echo "  devagent add path/to/your/file.py -p your-project-id   # Add code to the context database"
echo "  devagent project create 'My New Project'   # Create a new project"
echo ""
