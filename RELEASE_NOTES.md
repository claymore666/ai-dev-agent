# Release Notes: v0.2.1 - CLI & Project Management

## Overview

Version 0.2.1 enhances the Context-Extended AI Software Development Agent with a unified command-line interface and a comprehensive project management system. These additions mark the first milestone of Phase 3, focusing on usability and structured project organization. The new features maintain compatibility with the vector database and RAG capabilities from v0.2.0.

## Key Features

### Unified Command Line Interface
- A comprehensive CLI tool (`devagent.py`) for all agent operations
- Consistent command structure with extensive help documentation
- Status monitoring for all system components
- Unified access to code search, generation, and project management
- Flexible output options for both interactive and script-based usage

### Project Configuration System
- Persistent YAML-based project storage
- Complete metadata tracking for projects and files
- Support for tagging, descriptions, and other organization metadata
- File tracking within project contexts
- Code generation history recording
- JSON export/import for project configurations

### Integration Improvements
- Seamless interaction between projects and the vector database
- Automatic updating of project metadata during code operations
- Improved error handling and user feedback
- Better validation of inputs and operations

## Detailed Changes

### New Scripts & Components
- `devagent.py`: Main CLI tool for all operations
- `project_manager.py`: Core component for project management
- `install_cli.sh`: Installation script for the CLI tool
- `test_project_config.sh`: Test script for project management features
- `CLI_README.md`: Comprehensive documentation for CLI usage

### Enhanced Workflows
- Create and manage projects with persistent metadata
- Track files associated with projects
- Add code to both project tracking and vector database in one step
- Generate code with awareness of project context
- Export and import project configurations for backup or sharing

## Installation & Upgrade

Current users can upgrade with:

```bash
git pull
chmod +x install_cli.sh
./install_cli.sh
```

The CLI tool can be tested with:

```bash
./test_project_config.sh
```

## Example Usage

```bash
# Create a new project
devagent project create "Data API" --tags python api web

# Add existing code to the project
devagent add api.py --project-id data-api

# Generate new code with context awareness
devagent generate "Create a rate limiting middleware" --project-id data-api --output rate_limiter.py

# List all projects
devagent project list

# Export a project configuration
devagent project export data-api --output data-api-config.json
```

## What's Next

Upcoming development will focus on:
- Enhanced context selection for more relevant code retrieval
- Session management for persistent development sessions
- Code quality metrics and automated testing integration
- Iterative refinement of generated code

## Notes

- All existing functionality from v0.2.0 remains fully compatible
- Projects are stored in `~/.devagent/projects.yaml` by default
- For complete documentation, see the updated README.md and CLI_README.md
