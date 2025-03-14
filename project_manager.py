#!/usr/bin/env python3
"""
Project Manager for AI Development Agent

This module provides functionality for managing projects, including
creating, updating, listing, and retrieving project configurations.
Projects are stored in a SQLite database for persistence and efficiency.
"""

import os
import sys
import yaml
import json
import sqlite3
import logging
import datetime
import uuid
from typing import Dict, List, Any, Optional, Union

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("project_manager")

# Default paths
DEFAULT_CONFIG_DIR = os.path.expanduser("~/.devagent")
DEFAULT_DB_PATH = os.path.join(DEFAULT_CONFIG_DIR, "devagent.db")

def init_project_db(db_path: str) -> None:
    """Initialize the project database."""
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create the projects table if it doesn't exist
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS projects (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        description TEXT,
        created_at TEXT,
        updated_at TEXT,
        metadata TEXT
    )
    ''')
    
    # Create the project_tags table if it doesn't exist
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS project_tags (
        project_id TEXT,
        tag TEXT,
        PRIMARY KEY (project_id, tag),
        FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
    )
    ''')
    
    # Create the project_files table if it doesn't exist
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS project_files (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id TEXT,
        path TEXT,
        type TEXT,
        description TEXT,
        added_at TEXT,
        FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
    )
    ''')
    
    conn.commit()
    conn.close()
    
    logger.debug(f"Initialized project database: {db_path}")

class ProjectManager:
    """Manager for AI Development Agent projects."""
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize the project manager.
        
        Args:
            db_path: Path to the database file. If None, uses the default.
        """
        self.db_path = db_path or DEFAULT_DB_PATH
        
        # Ensure database exists and has the correct schema
        self._ensure_db_exists()
        
        # Load projects from YAML file for migration if needed
        self._migrate_from_yaml_if_needed()
    
    def _ensure_db_exists(self) -> None:
        """Ensure the database exists and has the correct schema."""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        init_project_db(self.db_path)
    
    def _migrate_from_yaml_if_needed(self) -> None:
        """Migrate projects from YAML file if it exists and database is empty."""
        yaml_path = os.path.join(DEFAULT_CONFIG_DIR, "projects.yaml")
        
        if not os.path.exists(yaml_path):
            return
        
        # Check if database is empty
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM projects")
        count = cursor.fetchone()[0]
        conn.close()
        
        if count > 0:
            # Database already has projects, no need to migrate
            return
        
        # Load projects from YAML
        try:
            with open(yaml_path, 'r') as f:
                projects = yaml.safe_load(f) or {}
            
            # Migrate each project to the database
            for project_id, project_data in projects.items():
                self.create_project(
                    name=project_data.get('name', ''),
                    description=project_data.get('description', ''),
                    tags=project_data.get('tags', []),
                    project_id=project_id,
                    created_at=project_data.get('created_at'),
                    metadata=project_data.get('metadata', {})
                )
                
                # Migrate project files
                for file_data in project_data.get('files', []):
                    self.add_file_to_project(
                        project_id=project_id,
                        file_path=file_data.get('path', ''),
                        file_type=file_data.get('type', ''),
                        description=file_data.get('description', '')
                    )
            
            logger.info(f"Migrated {len(projects)} projects from YAML to SQLite")
            
            # Rename the original YAML file as a backup
            backup_path = f"{yaml_path}.bak"
            os.rename(yaml_path, backup_path)
            logger.info(f"Renamed original YAML file to {backup_path}")
        except Exception as e:
            logger.error(f"Error migrating projects from YAML: {e}")
    
    def list_projects(self) -> List[Dict[str, Any]]:
        """
        List all projects.
        
        Returns:
            List of project dictionaries.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # This enables accessing columns by name
            cursor = conn.cursor()
            
            cursor.execute('''
            SELECT id, name, description, created_at, updated_at, metadata
            FROM projects
            ORDER BY updated_at DESC
            ''')
            
            projects = []
            for row in cursor.fetchall():
                project = dict(row)
                
                # Load metadata from JSON
                if project['metadata']:
                    project['metadata'] = json.loads(project['metadata'])
                else:
                    project['metadata'] = {}
                
                # Get tags for this project
                cursor.execute('''
                SELECT tag FROM project_tags WHERE project_id = ?
                ''', (project['id'],))
                
                tags = [tag[0] for tag in cursor.fetchall()]
                project['tags'] = tags
                
                # Get files for this project
                cursor.execute('''
                SELECT path, type, description, added_at
                FROM project_files
                WHERE project_id = ?
                ''', (project['id'],))
                
                files = []
                for file_row in cursor.fetchall():
                    files.append({
                        'path': file_row[0],
                        'type': file_row[1],
                        'description': file_row[2],
                        'added_at': file_row[3]
                    })
                
                project['files'] = files
                projects.append(project)
            
            conn.close()
            return projects
        except Exception as e:
            logger.error(f"Error listing projects: {e}")
            return []
    
    def get_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a project by its ID.
        
        Args:
            project_id: ID of the project to retrieve.
            
        Returns:
            Project dictionary or None if not found.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
            SELECT id, name, description, created_at, updated_at, metadata
            FROM projects
            WHERE id = ?
            ''', (project_id,))
            
            row = cursor.fetchone()
            if not row:
                conn.close()
                return None
            
            project = dict(row)
            
            # Load metadata from JSON
            if project['metadata']:
                project['metadata'] = json.loads(project['metadata'])
            else:
                project['metadata'] = {}
            
            # Get tags for this project
            cursor.execute('''
            SELECT tag FROM project_tags WHERE project_id = ?
            ''', (project_id,))
            
            tags = [tag[0] for tag in cursor.fetchall()]
            project['tags'] = tags
            
            # Get files for this project
            cursor.execute('''
            SELECT path, type, description, added_at
            FROM project_files
            WHERE project_id = ?
            ''', (project_id,))
            
            files = []
            for file_row in cursor.fetchall():
                files.append({
                    'path': file_row[0],
                    'type': file_row[1],
                    'description': file_row[2],
                    'added_at': file_row[3]
                })
            
            project['files'] = files
            
            conn.close()
            logger.debug(f"Retrieved project: {project_id}")
            return project
        except Exception as e:
            logger.error(f"Error getting project {project_id}: {e}")
            return None
    
    def create_project(
        self, 
        name: str, 
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        project_id: Optional[str] = None,
        created_at: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a new project.
        
        Args:
            name: Name of the project.
            description: Optional description of the project.
            tags: Optional list of tags for the project.
            project_id: Optional project ID. If None, generates an ID based on the name.
            created_at: Optional creation timestamp. If None, uses current time.
            metadata: Optional additional metadata for the project.
            
        Returns:
            The created project dictionary.
        """
        # Generate project ID if not provided
        if project_id is None:
            project_id = name.lower().replace(" ", "-")
            
            # Add random suffix to ensure uniqueness if the ID already exists
            if self.get_project(project_id) is not None:
                random_suffix = uuid.uuid4().hex[:6]
                project_id = f"{project_id}-{random_suffix}"
        
        # Use current time if created_at is not provided
        if created_at is None:
            created_at = datetime.datetime.now().isoformat()
        
        # Use current time for updated_at
        updated_at = datetime.datetime.now().isoformat()
        
        # Initialize metadata
        if metadata is None:
            metadata = {}
        
        # Initialize tags
        if tags is None:
            tags = []
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Insert project into database
            cursor.execute('''
            INSERT INTO projects (id, name, description, created_at, updated_at, metadata)
            VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                project_id,
                name,
                description or "",
                created_at,
                updated_at,
                json.dumps(metadata)
            ))
            
            # Insert tags
            for tag in tags:
                cursor.execute('''
                INSERT INTO project_tags (project_id, tag)
                VALUES (?, ?)
                ''', (project_id, tag))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Created project: {project_id}")
            
            # Return project with ID
            return {
                'id': project_id,
                'name': name,
                'description': description or "",
                'tags': tags,
                'created_at': created_at,
                'updated_at': updated_at,
                'files': [],
                'metadata': metadata
            }
        except Exception as e:
            logger.error(f"Error creating project: {e}")
            raise
    
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
        # Get current project data
        project = self.get_project(project_id)
        if not project:
            logger.error(f"Project not found for update: {project_id}")
            return None
        
        # Update timestamp
        updated_at = datetime.datetime.now().isoformat()
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Build the update query dynamically based on which fields are provided
            update_fields = []
            update_values = []
            
            if name is not None:
                update_fields.append("name = ?")
                update_values.append(name)
            
            if description is not None:
                update_fields.append("description = ?")
                update_values.append(description)
            
            # Always update the updated_at timestamp
            update_fields.append("updated_at = ?")
            update_values.append(updated_at)
            
            # Update metadata if provided
            if metadata is not None:
                # Merge with existing metadata
                new_metadata = {**project.get('metadata', {}), **metadata}
                update_fields.append("metadata = ?")
                update_values.append(json.dumps(new_metadata))
            else:
                new_metadata = project.get('metadata', {})
            
            # Update the project record
            if update_fields:
                query = f"UPDATE projects SET {', '.join(update_fields)} WHERE id = ?"
                update_values.append(project_id)
                cursor.execute(query, update_values)
            
            # Update tags if provided
            if tags is not None:
                # Delete existing tags
                cursor.execute("DELETE FROM project_tags WHERE project_id = ?", (project_id,))
                
                # Insert new tags
                for tag in tags:
                    cursor.execute('''
                    INSERT INTO project_tags (project_id, tag)
                    VALUES (?, ?)
                    ''', (project_id, tag))
                
                # Update tags in the project dictionary
                project['tags'] = tags
            
            conn.commit()
            conn.close()
            
            logger.info(f"Updated project: {project_id}")
            
            # Update the project dictionary with the new values
            if name is not None:
                project['name'] = name
            
            if description is not None:
                project['description'] = description
            
            project['updated_at'] = updated_at
            project['metadata'] = new_metadata
            
            return project
        except Exception as e:
            logger.error(f"Error updating project: {e}")
            return None
    
    def delete_project(self, project_id: str) -> bool:
        """
        Delete a project.
        
        Args:
            project_id: ID of the project to delete.
            
        Returns:
            True if the project was deleted, False otherwise.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute("PRAGMA foreign_keys = ON")  # Enable foreign key constraints
            cursor = conn.cursor()
            
            # Begin a transaction to ensure atomicity
            conn.execute("BEGIN TRANSACTION")
            
            try:
                # First explicitly delete any associated tags
                cursor.execute("DELETE FROM project_tags WHERE project_id = ?", (project_id,))
                logger.debug(f"Deleted {cursor.rowcount} tags for project: {project_id}")
                
                # Delete any associated files
                cursor.execute("DELETE FROM project_files WHERE project_id = ?", (project_id,))
                logger.debug(f"Deleted {cursor.rowcount} files for project: {project_id}")
                
                # Now delete the project itself
                cursor.execute("DELETE FROM projects WHERE id = ?", (project_id,))
                
                # Check if any rows were affected
                rows_affected = cursor.rowcount
                
                if rows_affected > 0:
                    # Commit the transaction if the project was found and deleted
                    conn.commit()
                    logger.info(f"Deleted project: {project_id}")
                    result = True
                else:
                    # Rollback if the project wasn't found
                    conn.rollback()
                    logger.error(f"Project not found for deletion: {project_id}")
                    result = False
            except Exception as inner_error:
                # Rollback on any error
                conn.rollback()
                logger.error(f"Transaction error deleting project: {inner_error}")
                result = False
            finally:
                # Always close the connection
                conn.close()
            
            return result
        except Exception as e:
            logger.error(f"Error deleting project: {e}")
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
        # Check if project exists
        if not self.get_project(project_id):
            logger.error(f"Project not found for adding file: {project_id}")
            return False
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Insert file
            cursor.execute('''
            INSERT INTO project_files (project_id, path, type, description, added_at)
            VALUES (?, ?, ?, ?, ?)
            ''', (
                project_id,
                file_path,
                file_type or self._guess_file_type(file_path),
                description or "",
                datetime.datetime.now().isoformat()
            ))
            
            # Update project updated_at timestamp
            cursor.execute('''
            UPDATE projects
            SET updated_at = ?
            WHERE id = ?
            ''', (datetime.datetime.now().isoformat(), project_id))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Added file to project: {file_path} -> {project_id}")
            return True
        except Exception as e:
            logger.error(f"Error adding file to project: {e}")
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
        # Get the project
        project = self.get_project(project_id)
        if not project:
            logger.error(f"Project not found for export: {project_id}")
            return None
        
        # Determine output file
        if output_file is None:
            output_file = f"{project_id}.json"
        
        try:
            with open(output_file, 'w') as f:
                json.dump(project, f, indent=2)
            
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
            
            project_id = project_data['id']
            
            # Check if project already exists
            existing_project = self.get_project(project_id)
            if existing_project and not override_existing:
                logger.error(f"Project already exists: {project_id}")
                return None
            
            # Extract project attributes
            name = project_data.get('name', '')
            description = project_data.get('description', '')
            tags = project_data.get('tags', [])
            metadata = project_data.get('metadata', {})
            files = project_data.get('files', [])
            
            # Create or update the project
            if existing_project and override_existing:
                # Update the project
                project = self.update_project(
                    project_id=project_id,
                    name=name,
                    description=description,
                    tags=tags,
                    metadata=metadata
                )
                
                # Delete existing files
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute("DELETE FROM project_files WHERE project_id = ?", (project_id,))
                conn.commit()
                conn.close()
            else:
                # Create a new project
                project = self.create_project(
                    name=name,
                    description=description,
                    tags=tags,
                    project_id=project_id,
                    metadata=metadata
                )
            
            # Add files
            for file_data in files:
                self.add_file_to_project(
                    project_id=project_id,
                    file_path=file_data.get('path', ''),
                    file_type=file_data.get('type', ''),
                    description=file_data.get('description', '')
                )
            
            logger.info(f"Imported project: {project_id}")
            return project
        except Exception as e:
            logger.error(f"Failed to import project: {e}")
            return None
    
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
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Build the query based on the provided criteria
            sql_conditions = []
            sql_params = []
            
            if query:
                sql_conditions.append("(name LIKE ? OR description LIKE ?)")
                sql_params.extend([f"%{query}%", f"%{query}%"])
            
            if created_after:
                sql_conditions.append("created_at >= ?")
                sql_params.append(created_after)
            
            if created_before:
                sql_conditions.append("created_at <= ?")
                sql_params.append(created_before)
            
            # If we have tags, we need to use a different approach with a subquery
            if tags:
                tag_placeholders = ", ".join(["?"] * len(tags))
                tag_condition = f'''
                id IN (
                    SELECT project_id
                    FROM project_tags
                    WHERE tag IN ({tag_placeholders})
                    GROUP BY project_id
                )
                '''
                sql_conditions.append(tag_condition)
                sql_params.extend(tags)
            
            # Build the final query
            sql_query = '''
            SELECT id, name, description, created_at, updated_at, metadata
            FROM projects
            '''
            
            if sql_conditions:
                sql_query += f" WHERE {' AND '.join(sql_conditions)}"
            
            sql_query += " ORDER BY updated_at DESC"
            
            cursor.execute(sql_query, sql_params)
            
            # Process the results
            projects = []
            for row in cursor.fetchall():
                project = dict(row)
                
                # Load metadata from JSON
                if project['metadata']:
                    project['metadata'] = json.loads(project['metadata'])
                else:
                    project['metadata'] = {}
                
                # Get tags for this project
                cursor.execute('''
                SELECT tag FROM project_tags WHERE project_id = ?
                ''', (project['id'],))
                
                project_tags = [tag[0] for tag in cursor.fetchall()]
                project['tags'] = project_tags
                
                # Get files for this project
                cursor.execute('''
                SELECT path, type, description, added_at
                FROM project_files
                WHERE project_id = ?
                ''', (project['id'],))
                
                files = []
                for file_row in cursor.fetchall():
                    files.append({
                        'path': file_row[0],
                        'type': file_row[1],
                        'description': file_row[2],
                        'added_at': file_row[3]
                    })
                
                project['files'] = files
                projects.append(project)
            
            conn.close()
            
            logger.info(f"Search found {len(projects)} projects")
            return projects
        except Exception as e:
            logger.error(f"Error searching projects: {e}")
            return []
    
    def get_project_files(self, project_id: str) -> List[Dict[str, Any]]:
        """
        Get files associated with a project.
        
        Args:
            project_id: ID of the project.
            
        Returns:
            List of file dictionaries.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
            SELECT path, type, description, added_at
            FROM project_files
            WHERE project_id = ?
            ORDER BY added_at DESC
            ''', (project_id,))
            
            files = []
            for row in cursor.fetchall():
                files.append({
                    'path': row[0],
                    'type': row[1],
                    'description': row[2],
                    'added_at': row[3]
                })
            
            conn.close()
            return files
        except Exception as e:
            logger.error(f"Error getting project files: {e}")
            return []


if __name__ == "__main__":
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
            print(json.dumps(project, indent=2))
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
