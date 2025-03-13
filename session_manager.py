#!/usr/bin/env python3
"""
Session Manager for AI Development Agent

This module provides functionality for managing development sessions, including
creating, restoring, and tracking session state. Sessions allow users to maintain
context across multiple interactions with the agent.
"""

import os
import sys
import json
import yaml
import logging
import datetime
import uuid
from typing import Dict, List, Any, Optional, Union

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("session_manager")

# Default paths
DEFAULT_CONFIG_DIR = os.path.expanduser("~/.devagent")
DEFAULT_SESSIONS_DIR = os.path.join(DEFAULT_CONFIG_DIR, "sessions")

class SessionManager:
    """Manager for AI Development Agent sessions."""
    
    def __init__(self, sessions_dir: Optional[str] = None):
        """
        Initialize the session manager.
        
        Args:
            sessions_dir: Path to the sessions directory. If None, uses the default.
        """
        self.sessions_dir = sessions_dir or DEFAULT_SESSIONS_DIR
        self.ensure_sessions_dir()
        self.active_session = None
        self.session_data = {}
    
    def ensure_sessions_dir(self) -> None:
        """Ensure the sessions directory exists."""
        if not os.path.exists(self.sessions_dir):
            try:
                os.makedirs(self.sessions_dir)
                logger.info(f"Created sessions directory: {self.sessions_dir}")
            except OSError as e:
                logger.error(f"Failed to create sessions directory: {e}")
                raise
    
    def list_sessions(self) -> List[Dict[str, Any]]:
        """
        List all available sessions.
        
        Returns:
            List of session metadata dictionaries.
        """
        sessions = []
        
        try:
            for filename in os.listdir(self.sessions_dir):
                if filename.endswith(".yaml") or filename.endswith(".yml"):
                    session_id = filename.rsplit(".", 1)[0]
                    session_path = os.path.join(self.sessions_dir, filename)
                    
                    try:
                        with open(session_path, 'r') as f:
                            session_data = yaml.safe_load(f)
                            
                        # Add session ID to metadata
                        session_meta = session_data.get("metadata", {})
                        session_meta["id"] = session_id
                        
                        # Calculate session duration if possible
                        if "start_time" in session_meta and "last_activity" in session_meta:
                            start = datetime.datetime.fromisoformat(session_meta["start_time"])
                            last = datetime.datetime.fromisoformat(session_meta["last_activity"])
                            duration = last - start
                            session_meta["duration"] = str(duration)
                        
                        sessions.append(session_meta)
                    except Exception as e:
                        logger.warning(f"Error reading session file {filename}: {e}")
            
            # Sort sessions by last activity time (newest first)
            sessions.sort(
                key=lambda s: s.get("last_activity", ""),
                reverse=True
            )
            
            return sessions
        except Exception as e:
            logger.error(f"Error listing sessions: {e}")
            return []
    
    def create_session(
        self,
        name: str,
        description: Optional[str] = None,
        project_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new development session.
        
        Args:
            name: Name of the session
            description: Optional description of the session
            project_id: Optional project ID to associate with the session
            tags: Optional tags for categorizing the session
            session_id: Optional custom session ID. If None, generates one.
            
        Returns:
            Session metadata dictionary
        """
        # Generate session ID if not provided
        if session_id is None:
            # Use a combination of timestamp and UUID to ensure uniqueness
            timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
            random_suffix = uuid.uuid4().hex[:6]
            session_id = f"session-{timestamp}-{random_suffix}"
        
        # Create session metadata
        metadata = {
            "name": name,
            "description": description or "",
            "project_id": project_id,
            "tags": tags or [],
            "start_time": datetime.datetime.now().isoformat(),
            "last_activity": datetime.datetime.now().isoformat(),
            "status": "active"
        }
        
        # Initialize session data
        self.session_data = {
            "metadata": metadata,
            "history": [],
            "context": {
                "current_project": project_id,
                "current_directory": os.getcwd(),
                "environment": {
                    "python_version": sys.version,
                    "platform": sys.platform
                }
            },
            "state": {
                "last_command": None,
                "last_result": None,
                "variables": {}
            }
        }
        
        # Save session data
        self._save_session(session_id)
        
        # Set as active session
        self.active_session = session_id
        
        logger.info(f"Created new session: {session_id}")
        return {**metadata, "id": session_id}
    
    def load_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Load an existing session.
        
        Args:
            session_id: ID of the session to load
            
        Returns:
            Session metadata if successful, None otherwise
        """
        session_path = os.path.join(self.sessions_dir, f"{session_id}.yaml")
        
        if not os.path.exists(session_path):
            logger.error(f"Session not found: {session_id}")
            return None
        
        try:
            with open(session_path, 'r') as f:
                self.session_data = yaml.safe_load(f)
            
            # Update last activity time
            if "metadata" in self.session_data:
                self.session_data["metadata"]["last_activity"] = datetime.datetime.now().isoformat()
                self.session_data["metadata"]["status"] = "active"
                
                # Save updated session data
                self._save_session(session_id)
            
            # Set as active session
            self.active_session = session_id
            
            logger.info(f"Loaded session: {session_id}")
            return {**self.session_data.get("metadata", {}), "id": session_id}
        except Exception as e:
            logger.error(f"Error loading session {session_id}: {e}")
            return None
    
    def get_active_session(self) -> Optional[Dict[str, Any]]:
        """
        Get the currently active session.
        
        Returns:
            Active session metadata or None if no active session
        """
        if not self.active_session or not self.session_data:
            return None
        
        return {**self.session_data.get("metadata", {}), "id": self.active_session}
    
    def close_session(self, session_id: Optional[str] = None) -> bool:
        """
        Close a session, marking it as completed.
        
        Args:
            session_id: ID of the session to close. If None, closes the active session.
            
        Returns:
            True if successful, False otherwise
        """
        # If no session ID provided, use the active session
        if session_id is None:
            if not self.active_session:
                logger.error("No active session to close")
                return False
            session_id = self.active_session
        
        # If closing the active session, load it first if not already loaded
        if session_id == self.active_session and not self.session_data:
            if not self.load_session(session_id):
                return False
        
        # If closing a different session, load it first
        if session_id != self.active_session:
            session_path = os.path.join(self.sessions_dir, f"{session_id}.yaml")
            if not os.path.exists(session_path):
                logger.error(f"Session not found: {session_id}")
                return False
                
            try:
                with open(session_path, 'r') as f:
                    session_data = yaml.safe_load(f)
            except Exception as e:
                logger.error(f"Error loading session to close: {e}")
                return False
        else:
            session_data = self.session_data
        
        # Update session metadata
        if "metadata" in session_data:
            session_data["metadata"]["status"] = "completed"
            session_data["metadata"]["end_time"] = datetime.datetime.now().isoformat()
            
            # Calculate duration
            if "start_time" in session_data["metadata"]:
                start = datetime.datetime.fromisoformat(session_data["metadata"]["start_time"])
                end = datetime.datetime.fromisoformat(session_data["metadata"]["end_time"])
                duration = end - start
                session_data["metadata"]["duration"] = str(duration)
        
        # Save updated session data
        session_path = os.path.join(self.sessions_dir, f"{session_id}.yaml")
        try:
            with open(session_path, 'w') as f:
                yaml.dump(session_data, f, default_flow_style=False)
            
            logger.info(f"Closed session: {session_id}")
            
            # If closing the active session, clear it
            if session_id == self.active_session:
                self.active_session = None
                self.session_data = {}
            
            return True
        except Exception as e:
            logger.error(f"Error saving session while closing: {e}")
            return False
    
    def add_to_history(
        self,
        command: str,
        args: Optional[Dict[str, Any]] = None,
        result: Optional[Any] = None,
        error: Optional[str] = None
    ) -> bool:
        """
        Add a command and its result to the session history.
        
        Args:
            command: The command that was executed
            args: Optional arguments that were passed to the command
            result: Optional result of the command
            error: Optional error message if the command failed
            
        Returns:
            True if successful, False otherwise
        """
        if not self.active_session:
            logger.warning("No active session to add history to")
            return False
        
        # Create history entry
        entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "command": command,
            "args": args or {},
            "working_directory": os.getcwd()
        }
        
        if result is not None:
            entry["result"] = result
        
        if error is not None:
            entry["error"] = error
        
        # Add to history
        if "history" not in self.session_data:
            self.session_data["history"] = []
        
        self.session_data["history"].append(entry)
        
        # Update state
        if "state" not in self.session_data:
            self.session_data["state"] = {}
        
        self.session_data["state"]["last_command"] = command
        
        if result is not None:
            self.session_data["state"]["last_result"] = result
        
        # Update last activity time
        if "metadata" in self.session_data:
            self.session_data["metadata"]["last_activity"] = datetime.datetime.now().isoformat()
        
        # Save session data
        return self._save_session(self.active_session)
    
    def set_context_value(self, key: str, value: Any) -> bool:
        """
        Set a value in the session context.
        
        Args:
            key: Context key
            value: Value to set
            
        Returns:
            True if successful, False otherwise
        """
        if not self.active_session:
            logger.warning("No active session to set context in")
            return False
        
        # Ensure context exists
        if "context" not in self.session_data:
            self.session_data["context"] = {}
        
        # Set context value
        self.session_data["context"][key] = value
        
        # Update last activity time
        if "metadata" in self.session_data:
            self.session_data["metadata"]["last_activity"] = datetime.datetime.now().isoformat()
        
        # Save session data
        return self._save_session(self.active_session)
    
    def get_context_value(self, key: str, default: Any = None) -> Any:
        """
        Get a value from the session context.
        
        Args:
            key: Context key
            default: Default value to return if key doesn't exist
            
        Returns:
            Context value or default
        """
        if not self.active_session:
            logger.warning("No active session to get context from")
            return default
        
        # Get context value
        context = self.session_data.get("context", {})
        return context.get(key, default)
    
    def set_state_variable(self, name: str, value: Any) -> bool:
        """
        Set a variable in the session state.
        
        Args:
            name: Variable name
            value: Variable value
            
        Returns:
            True if successful, False otherwise
        """
        if not self.active_session:
            logger.warning("No active session to set state in")
            return False
        
        # Ensure state exists
        if "state" not in self.session_data:
            self.session_data["state"] = {}
        
        # Ensure variables dictionary exists
        if "variables" not in self.session_data["state"]:
            self.session_data["state"]["variables"] = {}
        
        # Set variable
        self.session_data["state"]["variables"][name] = value
        
        # Update last activity time
        if "metadata" in self.session_data:
            self.session_data["metadata"]["last_activity"] = datetime.datetime.now().isoformat()
        
        # Save session data
        return self._save_session(self.active_session)
    
    def get_state_variable(self, name: str, default: Any = None) -> Any:
        """
        Get a variable from the session state.
        
        Args:
            name: Variable name
            default: Default value to return if variable doesn't exist
            
        Returns:
            Variable value or default
        """
        if not self.active_session:
            logger.warning("No active session to get state from")
            return default
        
        # Get variable
        state = self.session_data.get("state", {})
        variables = state.get("variables", {})
        return variables.get(name, default)
    
    def get_session_history(
        self,
        session_id: Optional[str] = None,
        limit: Optional[int] = None,
        command_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get the command history for a session.
        
        Args:
            session_id: ID of the session to get history for. If None, uses active session.
            limit: Optional maximum number of history entries to return
            command_filter: Optional filter to only include commands containing this string
            
        Returns:
            List of history entries
        """
        # If no session ID provided, use the active session
        if session_id is None:
            if not self.active_session:
                logger.warning("No active session to get history from")
                return []
            session_id = self.active_session
        
        # If getting history for the active session, use the loaded data
        if session_id == self.active_session and self.session_data:
            history = self.session_data.get("history", [])
        else:
            # Otherwise, load the session data
            session_path = os.path.join(self.sessions_dir, f"{session_id}.yaml")
            if not os.path.exists(session_path):
                logger.error(f"Session not found: {session_id}")
                return []
                
            try:
                with open(session_path, 'r') as f:
                    session_data = yaml.safe_load(f)
                    history = session_data.get("history", [])
            except Exception as e:
                logger.error(f"Error loading session history: {e}")
                return []
        
        # Apply command filter if provided
        if command_filter:
            history = [
                entry for entry in history
                if command_filter.lower() in entry.get("command", "").lower()
            ]
        
        # Apply limit if provided
        if limit and limit > 0:
            history = history[-limit:]
        
        return history
    
    def export_session(
        self,
        session_id: Optional[str] = None,
        output_file: Optional[str] = None
    ) -> Optional[str]:
        """
        Export a session to a JSON file.
        
        Args:
            session_id: ID of the session to export. If None, uses active session.
            output_file: Path to output file. If None, uses <session_id>.json.
            
        Returns:
            Path to the exported file if successful, None otherwise
        """
        # If no session ID provided, use the active session
        if session_id is None:
            if not self.active_session:
                logger.error("No active session to export")
                return None
            session_id = self.active_session
        
        # If exporting the active session, use the loaded data
        if session_id == self.active_session and self.session_data:
            session_data = self.session_data
        else:
            # Otherwise, load the session data
            session_path = os.path.join(self.sessions_dir, f"{session_id}.yaml")
            if not os.path.exists(session_path):
                logger.error(f"Session not found: {session_id}")
                return None
                
            try:
                with open(session_path, 'r') as f:
                    session_data = yaml.safe_load(f)
            except Exception as e:
                logger.error(f"Error loading session for export: {e}")
                return None
        
        # Determine output file
        if output_file is None:
            output_file = f"{session_id}.json"
        
        # Add session ID to data
        export_data = session_data.copy()
        if "metadata" in export_data:
            export_data["metadata"]["id"] = session_id
        
        # Export to JSON
        try:
            with open(output_file, 'w') as f:
                json.dump(export_data, f, indent=2)
            
            logger.info(f"Exported session to: {output_file}")
            return output_file
        except Exception as e:
            logger.error(f"Error exporting session: {e}")
            return None
    
    def import_session(
        self,
        input_file: str,
        session_id: Optional[str] = None,
        overwrite: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        Import a session from a JSON file.
        
        Args:
            input_file: Path to input file
            session_id: Optional custom session ID. If None, uses ID from file or generates one.
            overwrite: Whether to overwrite an existing session with the same ID
            
        Returns:
            Session metadata if successful, None otherwise
        """
        try:
            # Read input file
            with open(input_file, 'r') as f:
                if input_file.endswith(".json"):
                    session_data = json.load(f)
                elif input_file.endswith(".yaml") or input_file.endswith(".yml"):
                    session_data = yaml.safe_load(f)
                else:
                    logger.error(f"Unsupported file format: {input_file}")
                    return None
            
            # Extract or generate session ID
            if session_id is None:
                if "metadata" in session_data and "id" in session_data["metadata"]:
                    session_id = session_data["metadata"]["id"]
                else:
                    # Generate new session ID
                    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
                    random_suffix = uuid.uuid4().hex[:6]
                    session_id = f"session-{timestamp}-{random_suffix}"
            
            # Check if session already exists
            session_path = os.path.join(self.sessions_dir, f"{session_id}.yaml")
            if os.path.exists(session_path) and not overwrite:
                logger.error(f"Session already exists: {session_id}")
                return None
            
            # Update metadata
            if "metadata" in session_data:
                session_data["metadata"]["imported_from"] = input_file
                session_data["metadata"]["import_time"] = datetime.datetime.now().isoformat()
                
                # Remove id from metadata if present to avoid confusion
                if "id" in session_data["metadata"]:
                    del session_data["metadata"]["id"]
            
            # Save session data
            try:
                with open(session_path, 'w') as f:
                    yaml.dump(session_data, f, default_flow_style=False)
                
                logger.info(f"Imported session as: {session_id}")
                
                # Return metadata with ID
                metadata = session_data.get("metadata", {})
                return {**metadata, "id": session_id}
            except Exception as e:
                logger.error(f"Error saving imported session: {e}")
                return None
        except Exception as e:
            logger.error(f"Error importing session: {e}")
            return None
    
    def reset_session(self, session_id: Optional[str] = None) -> bool:
        """
        Reset a session, clearing its history and state but keeping metadata.
        
        Args:
            session_id: ID of the session to reset. If None, uses active session.
            
        Returns:
            True if successful, False otherwise
        """
        # If no session ID provided, use the active session
        if session_id is None:
            if not self.active_session:
                logger.error("No active session to reset")
                return False
            session_id = self.active_session
        
        # If resetting the active session, use the loaded data
        if session_id == self.active_session and self.session_data:
            # Keep metadata but reset history and state
            metadata = self.session_data.get("metadata", {})
            metadata["reset_time"] = datetime.datetime.now().isoformat()
            metadata["last_activity"] = datetime.datetime.now().isoformat()
            
            # Keep context but clear history and state
            context = self.session_data.get("context", {})
            
            # Reset session data
            self.session_data = {
                "metadata": metadata,
                "context": context,
                "history": [],
                "state": {
                    "variables": {}
                }
            }
            
            # Save session data
            return self._save_session(session_id)
        else:
            # Otherwise, load the session data first
            session_path = os.path.join(self.sessions_dir, f"{session_id}.yaml")
            if not os.path.exists(session_path):
                logger.error(f"Session not found: {session_id}")
                return False
                
            try:
                with open(session_path, 'r') as f:
                    session_data = yaml.safe_load(f)
                
                # Keep metadata but reset history and state
                metadata = session_data.get("metadata", {})
                metadata["reset_time"] = datetime.datetime.now().isoformat()
                metadata["last_activity"] = datetime.datetime.now().isoformat()
                
                # Keep context but clear history and state
                context = session_data.get("context", {})
                
                # Reset session data
                session_data = {
                    "metadata": metadata,
                    "context": context,
                    "history": [],
                    "state": {
                        "variables": {}
                    }
                }
                
                # Save session data
                with open(session_path, 'w') as f:
                    yaml.dump(session_data, f, default_flow_style=False)
                
                logger.info(f"Reset session: {session_id}")
                return True
            except Exception as e:
                logger.error(f"Error resetting session: {e}")
                return False
    
    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session.
        
        Args:
            session_id: ID of the session to delete
            
        Returns:
            True if successful, False otherwise
        """
        session_path = os.path.join(self.sessions_dir, f"{session_id}.yaml")
        
        if not os.path.exists(session_path):
            logger.error(f"Session not found: {session_id}")
            return False
        
        try:
            os.remove(session_path)
            
            logger.info(f"Deleted session: {session_id}")
            
            # If deleting the active session, clear it
            if session_id == self.active_session:
                self.active_session = None
                self.session_data = {}
            
            return True
        except Exception as e:
            logger.error(f"Error deleting session: {e}")
            return False
    
    def _save_session(self, session_id: str) -> bool:
        """
        Save the current session data to disk.
        
        Args:
            session_id: ID of the session to save
            
        Returns:
            True if successful, False otherwise
        """
        session_path = os.path.join(self.sessions_dir, f"{session_id}.yaml")
        
        try:
            with open(session_path, 'w') as f:
                yaml.dump(self.session_data, f, default_flow_style=False)
            
            logger.debug(f"Saved session: {session_id}")
            return True
        except Exception as e:
            logger.error(f"Error saving session: {e}")
            return False


if __name__ == "__main__":
    """Command-line interface for session manager."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Session Manager for AI Development Agent")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # List sessions command
    list_parser = subparsers.add_parser("list", help="List available sessions")
    
    # Create session command
    create_parser = subparsers.add_parser("create", help="Create a new session")
    create_parser.add_argument("name", help="Session name")
    create_parser.add_argument("--description", "-d", help="Session description")
    create_parser.add_argument("--project-id", "-p", help="Associated project ID")
    create_parser.add_argument("--tags", "-t", nargs="+", help="Session tags")
    create_parser.add_argument("--id", help="Custom session ID")
    
    # Load session command
    load_parser = subparsers.add_parser("load", help="Load a session")
    load_parser.add_argument("id", help="Session ID")
    
    # Get active session command
    active_parser = subparsers.add_parser("active", help="Get active session")
    
    # Close session command
    close_parser = subparsers.add_parser("close", help="Close a session")
    close_parser.add_argument("--id", help="Session ID (default: active session)")
    
    # Export session command
    export_parser = subparsers.add_parser("export", help="Export a session")
    export_parser.add_argument("--id", help="Session ID (default: active session)")
    export_parser.add_argument("--output", "-o", help="Output file path")
    
    # Import session command
    import_parser = subparsers.add_parser("import", help="Import a session")
    import_parser.add_argument("file", help="Input file path")
    import_parser.add_argument("--id", help="Custom session ID")
    import_parser.add_argument("--overwrite", action="store_true", help="Overwrite existing session")
    
    # Reset session command
    reset_parser = subparsers.add_parser("reset", help="Reset a session")
    reset_parser.add_argument("--id", help="Session ID (default: active session)")
    
    # Delete session command
    delete_parser = subparsers.add_parser("delete", help="Delete a session")
    delete_parser.add_argument("id", help="Session ID")
    
    # Get session history command
    history_parser = subparsers.add_parser("history", help="Get session command history")
    history_parser.add_argument("--id", help="Session ID (default: active session)")
    history_parser.add_argument("--limit", "-l", type=int, help="Maximum number of entries")
    history_parser.add_argument("--filter", "-f", help="Filter commands containing this string")
    
    args = parser.parse_args()
    
    # Initialize session manager
    session_manager = SessionManager()
    
    # Execute command
    if args.command == "list":
        sessions = session_manager.list_sessions()
        if sessions:
            print(f"Found {len(sessions)} sessions:")
            for session in sessions:
                print(f"\nID: {session.get('id', 'unknown')}")
                print(f"Name: {session.get('name', 'unnamed')}")
                
                if "description" in session and session["description"]:
                    print(f"Description: {session['description']}")
                
                if "project_id" in session and session["project_id"]:
                    print(f"Project: {session['project_id']}")
                
                if "status" in session:
                    print(f"Status: {session['status']}")
                
                if "start_time" in session:
                    print(f"Started: {session['start_time']}")
                
                if "last_activity" in session:
                    print(f"Last activity: {session['last_activity']}")
                
                if "duration" in session:
                    print(f"Duration: {session['duration']}")
        else:
            print("No sessions found")
    
    elif args.command == "create":
        session = session_manager.create_session(
            name=args.name,
            description=args.description,
            project_id=args.project_id,
            tags=args.tags,
            session_id=args.id
        )
        print(f"Created session: {session.get('id')}")
        print(f"Name: {session.get('name')}")
        print(f"Started: {session.get('start_time')}")
    
    elif args.command == "load":
        session = session_manager.load_session(args.id)
        if session:
            print(f"Loaded session: {session.get('id')}")
            print(f"Name: {session.get('name')}")
            print(f"Project: {session.get('project_id', 'none')}")
        else:
            print(f"Failed to load session: {args.id}")
            sys.exit(1)
    
    elif args.command == "active":
        session = session_manager.get_active_session()
        if session:
            print(f"Active session: {session.get('id')}")
            print(f"Name: {session.get('name')}")
            print(f"Project: {session.get('project_id', 'none')}")
            print(f"Started: {session.get('start_time')}")
            print(f"Last activity: {session.get('last_activity')}")
        else:
            print("No active session")
    
    elif args.command == "close":
        session_id = args.id  # May be None, which will close the active session
        success = session_manager.close_session(session_id)
        if success:
            print(f"Closed session: {session_id or 'active session'}")
        else:
            print(f"Failed to close session: {session_id or 'active session'}")
            sys.exit(1)
    
    elif args.command == "export":
        output_file = session_manager.export_session(args.id, args.output)
        if output_file:
            print(f"Exported session to: {output_file}")
        else:
            print("Failed to export session")
            sys.exit(1)
    
    elif args.command == "import":
        session = session_manager.import_session(args.file, args.id, args.overwrite)
        if session:
            print(f"Imported session: {session.get('id')}")
            print(f"Name: {session.get('name')}")
        else:
            print(f"Failed to import session from: {args.file}")
            sys.exit(1)
    
    elif args.command == "reset":
        success = session_manager.reset_session(args.id)
        if success:
            print(f"Reset session: {args.id or 'active session'}")
        else:
            print(f"Failed to reset session: {args.id or 'active session'}")
            sys.exit(1)
    
    elif args.command == "delete":
        success = session_manager.delete_session(args.id)
        if success:
            print(f"Deleted session: {args.id}")
        else:
            print(f"Failed to delete session: {args.id}")
            sys.exit(1)
    
    elif args.command == "history":
        history = session_manager.get_session_history(args.id, args.limit, args.filter)
        if history:
            print(f"Session history ({len(history)} entries):")
            for i, entry in enumerate(history):
                print(f"\n{i+1}. {entry.get('command', 'unknown')} - {entry.get('timestamp', 'unknown')}")
                if "args" in entry and entry["args"]:
                    args_str = ", ".join(f"{k}={v}" for k, v in entry["args"].items())
                    print(f"   Args: {args_str}")
                if "working_directory" in entry:
                    print(f"   Directory: {entry['working_directory']}")
                if "result" in entry:
                    result_str = str(entry["result"])
                    if len(result_str) > 100:
                        result_str = result_str[:100] + "..."
                    print(f"   Result: {result_str}")
                if "error" in entry:
                    print(f"   Error: {entry['error']}")
        else:
            print("No history found")
    
    else:
        parser.print_help()
