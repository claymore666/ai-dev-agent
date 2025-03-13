#!/usr/bin/env python3
"""
Project Manager for AI Development Agent

This module provides functionality for managing projects, including
creating, updating, listing, and retrieving project configurations.
Projects are stored in a YAML file and can be accessed via their ID.
"""

import os
import sys
import yaml
import json
import uuid
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Union

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("project_manager")

# Default paths
DEFAULT_CONFIG_DIR = os.path.expanduser("~/.devagent")
DEFAULT_PROJECTS_FILE = os.path.join(DEFAULT_CONFIG_DIR, "projects.yaml")

class ProjectManager:
    """Manager for AI Development Agent projects."""
    
    def __init__(self, projects_file: Optional[str] = None):
        """
        Initialize the project manager.
        
        Args:
            projects_file: Path to the projects file. If None, uses the default.
        """
        self.projects_file = projects_file or DEFAULT_PROJECTS_FILE
        self.ensure_config_dir()
        self.projects = self.load_projects()
    
    def ensure_config_dir(self) -> None:
        """Ensure the configuration directory exists."""
        config_dir = os.path.dirname(self.projects_file)
        if not os.path.exists(config_dir):
            try:
                os.makedirs(config_dir)
                logger.info(f"Created configuration directory: {config_dir}")
            except OSError as e:
                logger.error(f"Failed to create configuration directory: {e}")
                raise
    
    def load_projects(self) -> Dict[str, Dict[str, Any]]:
        """
        Load projects from the projects file.
        
        Returns:
            Dictionary of projects indexed by their ID.
        """
        if not os.path.exists(self.projects_file):
            logger.info(f"Projects file not found: {self.projects_file}. Creating new file.")
            return {}
        
        try:
            with open(self.projects_file, 'r') as f:
                projects = yaml.safe_load(f) or {}
            logger.info(f"Loaded {len(projects)} projects from {self.projects_file}")
            return projects
        except Exception as e:
            logger.error(f"Failed to load projects: {e}")
            return {}
    
    def save_projects(self) -> bool:
        """
        Save projects to the projects file.
        
        Returns:
            True if successful, False otherwise.
        """
        try:
            with open(self.projects_file, 'w') as f:
                yaml.dump(self.projects, f, default_flow_style=False)
            logger.info(f"Saved {len(self.projects)} projects to {self.projects_file}")
            return True
        except Exception as e:
            logger.error(f"Failed to save projects: {e}")
            return False
    
    def get_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a project by its ID.
        
        Args:
            project_id: ID of the project to retrieve.
            
        Returns:
            Project dictionary or None if not found.
        """
        project = self.projects.get(project_id)
        if project:
            logger.debug(f"Retrieved project: {project_id}")
        else:
            logger.debug(f"Project not found: {project_id}")
        return project
    
    def list_projects(self) -> List[Dict[str, Any]]:
        """
        List all projects.
        
        Returns:
            List of project dictionaries.
        """
        projects_list = []
        for project_id, project in self.projects.items():
            # Create a copy of the project with ID included
            project_with_id = project.copy()
            project_with_id['id'] = project_id
            projects_list.append(project_with_id)
        
        # Sort by creation date, newest first
        projects_list.sort(key=lambda p: p.get('created_at', ''), reverse=True)
        
        logger.info(f"Listed {len(projects_list)} projects")
        return projects_list
    
    def create_project(
        self, 
        name: str, 
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        project_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new project.
        
        Args:
            name: Name of the project.
            description: Optional description of the project.
            tags: Optional list of tags for the project.
            project_id: Optional project ID. If None, generates an ID based on the name.
            
        Returns:
            The created project dictionary.
        """
        # Generate project ID if not provided
        if project_id is None:
            project_id = name.lower().replace(" ", "-")
            
            # Add random suffix to ensure uniqueness if the ID already exists
            if project_id in self.projects:
                random_suffix = uuid.uuid4().hex[:6]
                project_id = f"{project_id}-{random_suffix}"
        
        # Create project
        project = {
            'name': name,
            'description': description or "",
            'tags': tags or [],
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'files': [],  # List of files associated with the project
            'metadata': {},  # Additional metadata
        }
        
        # Add to projects dictionary
        self.projects[project_id] = project
        
        # Save projects
        if self.save_projects():
            logger.info(f"Created project: {project_id}")
        else:
            logger.error(f"Project created but not saved: {project_id}")
        
        # Return project with ID
        project_with_id = project.copy()
        project_with_id['id'] = project_id
        return project_with_id
    
    def update_project(
        self,
        project_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Update an existing project.
        
        Args:
            project_id: ID of the project to update.
            name: Optional new name for the project.
            description: Optional new description for the project.
            tags: Optional new tags for the project.
            metadata: Optional metadata to update or add.
            
        Returns:
            The updated project dictionary or None if the project was not found.
        """
        project = self.get_project(project_id)
        if not project:
            logger.error(f"Project not found for update: {project_id}")
            return None
        
        # Update fields
        if name is not None:
            project['name'] = name
        
        if description is not None:
            project['description'] = description
        
        if tags is not None:
            project['tags'] = tags
        
        if metadata is not None:
            if 'metadata' not in project:
                project['metadata'] = {}
            project['metadata'].update(metadata)
        
        # Update timestamp
        project['updated_at'] = datetime.now().isoformat()
        
        # Save projects
        if self.save_projects():
            logger.info(f"Updated project: {project_id}")
        else:
            logger.error(f"Project updated but not saved: {project_id}")
        
        # Return project with ID
        project_with_id = project.copy()
        project_with_id['id'] = project_id
        return project_with_id
    
    def delete_project(self, project_id: str) -> bool:
        """
        Delete a project.
        
        Args:
            project_id: ID of the project to delete.
            
        Returns:
            True if the project was deleted, False otherwise.
        """
        if project_id not in self.projects:
            logger.error(f"Project not found for deletion: {project_id}")
            return False
        
        # Remove project
        del self.projects[project_id]
        
        # Save projects
        if self.save_projects():
            logger.info(f"Deleted project: {project_id}")
            return True
        else:
            logger.error(f"Project deletion not saved: {project_id}")
            return False
    
    def add_file_to_project(
        self,
        project_id: str,
        file_path: str,
        file_type: Optional[str] = None,
        description: Optional[str] = None
    ) -> bool:
        """
        Add a file to a project.
        
        Args:
            project_id: ID of the project to add the file to.
            file_path: Path to the file.
            file_type: Optional type of the file.
            description: Optional description of the file.
            
        Returns:
            True if the file was added, False otherwise.
        """
        project = self.get_project(project_id)
        if not project:
            logger.error(f"Project not found for adding file: {project_id}")
            return False
        
        # Ensure files list exists
        if 'files' not in project:
            project['files'] = []
        
        # Create file entry
        file_entry = {
            'path': file_path,
            'type': file_type or self._guess_file_type(file_path),
            'description': description or "",
            'added_at': datetime.now().isoformat(),
        }
        
        # Add file to project
        project['files'].append(file_entry)
        
        # Update timestamp
        project['updated_at'] = datetime.now().isoformat()
        
        # Save projects
        if self.save_projects():
            logger.info(f"Added file to project: {file_path} -> {project_id}")
            return True
        else:
            logger.error(f"File addition not saved: {file_path} -> {project_id}")
            return False
    
    def _guess_file_type(self, file_path: str) -> str:
        """
        Guess the type of a file based on its extension.
        
        Args:
            file_path: Path to the file.
            
        Returns:
            Guessed file type.
        """
        ext = os.path.splitext(file_path)[1].lower()
        
        file_types = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.java': 'java',
            '.c': 'c',
            '.cpp': 'cpp',
            '.cs': 'csharp',
            '.go': 'go',
            '.rs': 'rust',
            '.rb': 'ruby',
            '.php': 'php',
            '.swift': 'swift',
            '.kt': 'kotlin',
            '.scala': 'scala',
            '.html': 'html',
            '.css': 'css',
            '.json': 'json',
            '.xml': 'xml',
            '.yaml': 'yaml',
            '.yml': 'yaml',
            '.md': 'markdown',
            '.txt': 'text',
        }
        
        return file_types.get(ext, 'unknown')
    
    def export_project(self, project_id: str, output_file: Optional[str] = None) -> Optional[str]:
        """
        Export a project to a JSON file.
        
        Args:
            project_id: ID of the project to export.
            output_file: Optional path to the output file. If None, uses <project_id>.json.
            
        Returns:
            Path to the exported file or None if the export failed.
        """
        project = self.get_project(project_id)
        if not project:
            logger.error(f"Project not found for export: {project_id}")
            return None
        
        # Determine output file
        if output_file is None:
            output_file = f"{project_id}.json"
        
        # Create a copy with ID included
        project_with_id = project.copy()
        project_with_id['id'] = project_id
        
        try:
            with open(output_file, 'w') as f:
                json.dump(project_with_id, f, indent=2)
            logger.info(f"Exported project to: {output_file}")
            return output_file
        except Exception as e:
            logger.error(f"Failed to export project: {e}")
            return None
    
    def import_project(self, input_file: str, override_existing: bool = False) -> Optional[Dict[str, Any]]:
        """
        Import a project from a JSON file.
        
        Args:
            input_file: Path to the input file.
            override_existing: Whether to override an existing project with the same ID.
            
        Returns:
            The imported project dictionary or None if the import failed.
        """
        try:
            with open(input_file, 'r') as f:
                project_data = json.load(f)
            
            # Ensure project has an ID
            if 'id' not in project_data:
                logger.error("Project file does not contain an ID")
                return None
            
            project_id = project_data.pop('id')  # Remove ID from data
            
            # Check if project already exists
            if project_id in self.projects and not override_existing:
                logger.error(f"Project already exists: {project_id}")
                return None
            
            # Add project
            self.projects[project_id] = project_data
            
            # Save projects
            if self.save_projects():
                logger.info(f"Imported project: {project_id}")
            else:
                logger.error(f"Project imported but not saved: {project_id}")
            
            # Return project with ID
            project_with_id = project_data.copy()
            project_with_id['id'] = project_id
            return project_with_id
            
        except Exception as e:
            logger.error(f"Failed to import project: {e}")
            return None
    
    def get_project_files(self, project_id: str) -> List[Dict[str, Any]]:
        """
        Get files associated with a project.
        
        Args:
            project_id: ID of the project.
            
        Returns:
            List of file dictionaries.
        """
        project = self.get_project(project_id)
        if not project:
            logger.error(f"Project not found for getting files: {project_id}")
            return []
        
        return project.get('files', [])
    
    def search_projects(
        self,
        query: Optional[str] = None,
        tags: Optional[List[str]] = None,
        created_after: Optional[str] = None,
        created_before: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for projects based on criteria.
        
        Args:
            query: Optional query string to search in name and description.
            tags: Optional list of tags to filter by (any match).
            created_after: Optional ISO format date string to filter by creation date.
            created_before: Optional ISO format date string to filter by creation date.
            
        Returns:
            List of matching project dictionaries.
        """
        results = []
        
        for project_id, project in self.projects.items():
            # Create a copy with ID included
            project_with_id = project.copy()
            project_with_id['id'] = project_id
            
            # Apply filters
            if query:
                query_lower = query.lower()
                name = project.get('name', '').lower()
                description = project.get('description', '').lower()
                
                if query_lower not in name and query_lower not in description:
                    continue
            
            if tags:
                project_tags = set(project.get('tags', []))
                if not any(tag in project_tags for tag in tags):
                    continue
            
            if created_after:
                created_at = project.get('created_at', '')
                if created_at < created_after:
                    continue
            
            if created_before:
                created_at = project.get('created_at', '')
                if created_at > created_before:
                    continue
            
            results.append(project_with_id)
        
        # Sort by creation date, newest first
        results.sort(key=lambda p: p.get('created_at', ''), reverse=True)
        
        logger.info(f"Search found {len(results)} projects")
        return results

def main():
    """Command line interface for project manager."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Project Manager for AI Development Agent")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Create project command
    create_parser = subparsers.add_parser("create", help="Create a new project")
    create_parser.add_argument("name", help="Project name")
    create_parser.add_argument("--description", "-d", help="Project description")
    create_parser.add_argument("--tags", "-t", nargs="+", help="Project tags")
    create_parser.add_argument("--id", help="Custom project ID")
    
    # List projects command
    list_parser = subparsers.add_parser("list", help="List projects")
    
    # Get project command
    get_parser = subparsers.add_parser("get", help="Get a project by ID")
    get_parser.add_argument("id", help="Project ID")
    
    # Update project command
    update_parser = subparsers.add_parser("update", help="Update a project")
    update_parser.add_argument("id", help="Project ID")
    update_parser.add_argument("--name", "-n", help="New project name")
    update_parser.add_argument("--description", "-d", help="New project description")
    update_parser.add_argument("--tags", "-t", nargs="+", help="New project tags")
    
    # Delete project command
    delete_parser = subparsers.add_parser("delete", help="Delete a project")
    delete_parser.add_argument("id", help="Project ID")
    
    # Export project command
    export_parser = subparsers.add_parser("export", help="Export a project to a file")
    export_parser.add_argument("id", help="Project ID")
    export_parser.add_argument("--output", "-o", help="Output file path")
    
    # Import project command
    import_parser = subparsers.add_parser("import", help="Import a project from a file")
    import_parser.add_argument("file", help="Input file path")
    import_parser.add_argument("--override", "-o", action="store_true", help="Override existing project")
    
    # Search projects command
    search_parser = subparsers.add_parser("search", help="Search for projects")
    search_parser.add_argument("--query", "-q", help="Search query")
    search_parser.add_argument("--tags", "-t", nargs="+", help="Filter by tags")
    search_parser.add_argument("--after", help="Filter by creation date (ISO format)")
    search_parser.add_argument("--before", help="Filter by creation date (ISO format)")
    
    # Add file command
    add_file_parser = subparsers.add_parser("add-file", help="Add a file to a project")
    add_file_parser.add_argument("id", help="Project ID")
    add_file_parser.add_argument("file", help="File path")
    add_file_parser.add_argument("--type", "-t", help="File type")
    add_file_parser.add_argument("--description", "-d", help="File description")
    
    # Parse arguments
    args = parser.parse_args()
    
    # Initialize project manager
    manager = ProjectManager()
    
    # Execute command
    if args.command == "create":
        project = manager.create_project(
            name=args.name,
            description=args.description,
            tags=args.tags,
            project_id=args.id
        )
        print(json.dumps(project, indent=2))
    
    elif args.command == "list":
        projects = manager.list_projects()
        if projects:
            print(json.dumps(projects, indent=2))
        else:
            print("No projects found")
    
    elif args.command == "get":
        project = manager.get_project(args.id)
        if project:
            project_with_id = project.copy()
            project_with_id['id'] = args.id
            print(json.dumps(project_with_id, indent=2))
        else:
            print(f"Project not found: {args.id}")
            sys.exit(1)
    
    elif args.command == "update":
        project = manager.update_project(
            project_id=args.id,
            name=args.name,
            description=args.description,
            tags=args.tags
        )
        if project:
            print(json.dumps(project, indent=2))
        else:
            print(f"Project not found: {args.id}")
            sys.exit(1)
    
    elif args.command == "delete":
        success = manager.delete_project(args.id)
        if success:
            print(f"Project deleted: {args.id}")
        else:
            print(f"Failed to delete project: {args.id}")
            sys.exit(1)
    
    elif args.command == "export":
        output_file = manager.export_project(args.id, args.output)
        if output_file:
            print(f"Project exported to: {output_file}")
        else:
            print(f"Failed to export project: {args.id}")
            sys.exit(1)
    
    elif args.command == "import":
        project = manager.import_project(args.file, args.override)
        if project:
            print(f"Project imported: {project['id']}")
            print(json.dumps(project, indent=2))
        else:
            print(f"Failed to import project from: {args.file}")
            sys.exit(1)
    
    elif args.command == "search":
        projects = manager.search_projects(
            query=args.query,
            tags=args.tags,
            created_after=args.after,
            created_before=args.before
        )
        if projects:
            print(json.dumps(projects, indent=2))
        else:
            print("No projects found matching the criteria")
    
    elif args.command == "add-file":
        success = manager.add_file_to_project(
            project_id=args.id,
            file_path=args.file,
            file_type=args.type,
            description=args.description
        )
        if success:
            print(f"File added to project: {args.file} -> {args.id}")
        else:
            print(f"Failed to add file to project: {args.file} -> {args.id}")
            sys.exit(1)
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
