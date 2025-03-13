#!/usr/bin/env python3
"""
DevAgent CLI - Command Line Interface for the Context-Extended AI Software Development Agent

This CLI tool provides a unified interface to interact with the AI Development Agent,
allowing users to manage projects, search code, generate code with context awareness,
and perform other development tasks.
"""

import os
import sys
import argparse
import logging
from typing import List, Dict, Any, Optional
import json
from datetime import datetime
from session_manager import SessionManager

# Add the current directory to the path to make imports work
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import related modules (adjust as needed based on your actual imports)
try:
    from code_rag import CodeRAG
    from qdrant_helper import check_qdrant_health, create_collections, search_similar_code
    from project_manager import ProjectManager
except ImportError as e:
    print(f"Failed to import required modules: {e}")
    print("Please ensure you're running this script from the project directory.")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("devagent.log")
    ]
)
logger = logging.getLogger("devagent")

# Helper function to add context selection arguments to parsers
def add_context_selection_args(parser):
    """Add context selection arguments to a parser."""
    parser.add_argument(
        "--context-strategy",
        choices=["semantic", "structural", "dependency", "balanced", "auto"],
        default="auto",
        help="Strategy for context selection (default: auto)"
    )
    parser.add_argument(
        "--context-count",
        type=int,
        default=5,
        help="Number of context fragments to retrieve (default: 5)"
    )

class DevAgentCLI:
    """Command Line Interface for the AI Development Agent."""
    
    def __init__(self):
        """Initialize the CLI with required components."""
        self.parser = self._create_parser()
        self.code_rag = None  # Lazily initialized when needed
        self.project_manager = ProjectManager()  # Initialize project manager
        self.session_manager = SessionManager()  # Initialize session manager
    
    def _create_parser(self) -> argparse.ArgumentParser:
        """Create the argument parser with all supported commands."""
        parser = argparse.ArgumentParser(
            description="DevAgent CLI - Command Line Interface for the Context-Extended AI Software Development Agent",
            formatter_class=argparse.RawDescriptionHelpFormatter
        )
        
        # Add global arguments
        parser.add_argument(
            "--verbose", "-v", 
            action="store_true", 
            help="Enable verbose output"
        )
        parser.add_argument(
            "--quiet", "-q", 
            action="store_true", 
            help="Suppress output except for errors"
        )
        
        # Add subparsers for different commands
        subparsers = parser.add_subparsers(dest="command", help="Command to execute")
        
        # Status command
        status_parser = subparsers.add_parser("status", help="Check the status of the AI Development Agent")
        
        # Search command
        search_parser = subparsers.add_parser("search", help="Search for code fragments")
        search_parser.add_argument("query", help="Search query")
        search_parser.add_argument(
            "--project-id", "-p", 
            help="Project ID to filter search results"
        )
        search_parser.add_argument(
            "--limit", "-l", 
            type=int, 
            default=5, 
            help="Maximum number of results to return"
        )
        # Add context selection args to search parser
        add_context_selection_args(search_parser)
        
        # Generate command
        generate_parser = subparsers.add_parser("generate", help="Generate code with context")
        generate_parser.add_argument("prompt", help="The code generation prompt")
        generate_parser.add_argument(
            "--project-id", "-p", 
            help="Project ID to provide context from"
        )
        generate_parser.add_argument(
            "--output", "-o", 
            help="Output file to save the generated code"
        )
        generate_parser.add_argument(
            "--model", "-m", 
            default="ollama-codellama", 
            help="Model to use for generation (default: ollama-codellama)"
        )
        # Add context selection args to generate parser
        add_context_selection_args(generate_parser)
        
        # Add command
        add_parser = subparsers.add_parser("add", help="Add code to the context database")
        add_parser.add_argument("file", help="File path or code string to add")
        add_parser.add_argument(
            "--project-id", "-p", 
            required=True, 
            help="Project ID to associate with the code"
        )
        add_parser.add_argument(
            "--file-type", "-t", 
            choices=["python", "javascript", "typescript", "java", "c", "cpp", "csharp", "go", "rust", "other"],
            default="python", 
            help="Type of the file (default: python)"
        )
        add_parser.add_argument(
            "--name", "-n", 
            help="Name of the code entity (function, class, etc.)"
        )
        
        # Project command
        project_parser = subparsers.add_parser("project", help="Manage projects")
        project_subparsers = project_parser.add_subparsers(dest="project_command", help="Project subcommand")
        
        # Project list command
        project_list_parser = project_subparsers.add_parser("list", help="List projects")
        project_list_parser.add_argument(
            "--query", "-q",
            help="Optional search query to filter projects"
        )
        project_list_parser.add_argument(
            "--tags", "-t",
            nargs="+",
            help="Optional tags to filter projects"
        )
        
        # Project create command
        project_create_parser = project_subparsers.add_parser("create", help="Create a new project")
        project_create_parser.add_argument("name", help="Project name")
        project_create_parser.add_argument(
            "--description", "-d", 
            help="Project description"
        )
        project_create_parser.add_argument(
            "--tags", "-t",
            nargs="+",
            help="Tags for the project"
        )
        project_create_parser.add_argument(
            "--id",
            help="Custom project ID (default: generated from name)"
        )
        
        # Project get command
        project_get_parser = project_subparsers.add_parser("get", help="Get details of a project")
        project_get_parser.add_argument("id", help="Project ID")
        
        # Project update command
        project_update_parser = project_subparsers.add_parser("update", help="Update a project")
        project_update_parser.add_argument("id", help="Project ID")
        project_update_parser.add_argument(
            "--name", "-n",
            help="New project name"
        )
        project_update_parser.add_argument(
            "--description", "-d",
            help="New project description"
        )
        project_update_parser.add_argument(
            "--tags", "-t",
            nargs="+",
            help="New tags for the project"
        )
        
        # Project delete command
        project_delete_parser = project_subparsers.add_parser("delete", help="Delete a project")
        project_delete_parser.add_argument("id", help="Project ID")
        project_delete_parser.add_argument(
            "--confirm",
            action="store_true",
            help="Confirm deletion without prompting"
        )
        
        # Project add-file command
        project_add_file_parser = project_subparsers.add_parser("add-file", help="Add a file to a project")
        project_add_file_parser.add_argument("id", help="Project ID")
        project_add_file_parser.add_argument("file", help="Path to the file")
        project_add_file_parser.add_argument(
            "--type", "-t",
            help="File type (default: auto-detected)"
        )
        project_add_file_parser.add_argument(
            "--description", "-d",
            help="File description"
        )
        
        # Project export command
        project_export_parser = project_subparsers.add_parser("export", help="Export a project to a file")
        project_export_parser.add_argument("id", help="Project ID")
        project_export_parser.add_argument(
            "--output", "-o",
            help="Output file path (default: <project_id>.json)"
        )
        
        # Project import command
        project_import_parser = project_subparsers.add_parser("import", help="Import a project from a file")
        project_import_parser.add_argument("file", help="Path to the project file")
        project_import_parser.add_argument(
            "--override", "-o",
            action="store_true",
            help="Override existing project if it exists"
        )
        
        # Init command
        init_parser = subparsers.add_parser("init", help="Initialize or update the DevAgent environment")
        
        # Analyze command
        analyze_parser = subparsers.add_parser("analyze", help="Analyze a query for context selection")
        analyze_parser.add_argument("query", help="The query to analyze")
        analyze_parser.add_argument(
            "--project-id", "-p", 
            help="Project ID to check context against"
        )
        add_context_selection_args(analyze_parser)
        
                # Session command
        session_parser = subparsers.add_parser("session", help="Manage development sessions")
        session_subparsers = session_parser.add_subparsers(dest="session_command", help="Session subcommand")

        # Session list command
        session_list_parser = session_subparsers.add_parser("list", help="List available sessions")

        # Session create command
        session_create_parser = session_subparsers.add_parser("create", help="Create a new session")
        session_create_parser.add_argument("name", help="Session name")
        session_create_parser.add_argument(
            "--description", "-d", 
            help="Session description"
        )
        session_create_parser.add_argument(
            "--project-id", "-p", 
            help="Associated project ID"
        )
        session_create_parser.add_argument(
            "--tags", "-t", 
            nargs="+", 
            help="Session tags"
        )

        # Session load command
        session_load_parser = session_subparsers.add_parser("load", help="Load a session")
        session_load_parser.add_argument("id", help="Session ID")

        # Session info command (active)
        session_info_parser = session_subparsers.add_parser("info", help="Get information about the active session")

        # Session close command
        session_close_parser = session_subparsers.add_parser("close", help="Close the active session")

        # Session reset command
        session_reset_parser = session_subparsers.add_parser("reset", help="Reset the active session")

        # Session export command
        session_export_parser = session_subparsers.add_parser("export", help="Export a session")
        session_export_parser.add_argument(
            "--id", 
            help="Session ID (default: active session)"
        )
        session_export_parser.add_argument(
            "--output", "-o", 
            help="Output file path"
        )

        # Session import command
        session_import_parser = session_subparsers.add_parser("import", help="Import a session")
        session_import_parser.add_argument("file", help="Input file path")
        session_import_parser.add_argument(
            "--overwrite", 
            action="store_true", 
            help="Overwrite existing session"
        )

        # Session delete command
        session_delete_parser = session_subparsers.add_parser("delete", help="Delete a session")
        session_delete_parser.add_argument("id", help="Session ID")
        session_delete_parser.add_argument(
            "--confirm", 
            action="store_true", 
            help="Confirm deletion without prompting"
        )

        # Session history command
        session_history_parser = session_subparsers.add_parser("history", help="Show session command history")
        session_history_parser.add_argument(
            "--limit", "-l", 
            type=int, 
            default=10, 
            help="Maximum number of entries to display"
        )
        session_history_parser.add_argument(
            "--filter", "-f", 
            help="Filter commands containing this string"
        )
        
        return parser
    
    def _init_code_rag(self, model_name: str = "ollama-codellama") -> None:
        """Initialize the CodeRAG component if not already initialized."""
        if self.code_rag is None:
            try:
                logger.info(f"Initializing CodeRAG with model: {model_name}")
                # Pass session manager to CodeRAG
                self.code_rag = CodeRAG(llm_model_name=model_name, session_manager=self.session_manager)
                logger.info("CodeRAG initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize CodeRAG: {e}")
                print(f"Error: Failed to initialize code generation system: {e}")
                sys.exit(1)
    
    def handle_status(self, args: argparse.Namespace) -> None:
        """Handle the status command."""
        print("Checking AI Development Agent status...")
        
        # Check if Qdrant is healthy
        qdrant_healthy = check_qdrant_health()
        print(f"Qdrant vector database: {'HEALTHY' if qdrant_healthy else 'UNHEALTHY'}")
        
        # Check LiteLLM connection by attempting to initialize CodeRAG
        try:
            self._init_code_rag()
            print("LiteLLM connection: HEALTHY")
        except Exception:
            print("LiteLLM connection: UNHEALTHY")
        
        # Print environment information
        print("\nEnvironment Information:")
        print(f"Python version: {sys.version.split()[0]}")
        print(f"Working directory: {os.getcwd()}")
        print(f"Script location: {os.path.abspath(__file__)}")
        
        # Check for installed packages using pip
        print("\nInstalled Packages:")
        try:
            import subprocess
            result = subprocess.run(
                [sys.executable, "-m", "pip", "list"], 
                capture_output=True, 
                text=True
            )
            packages = result.stdout.strip().split('\n')
            
            # Look for specific packages
            relevant_packages = [
                'qdrant-client', 'sentence-transformers', 
                'llama-index', 'llama-index-core', 
                'llama-index-vector-stores-qdrant',
                'llama-index-llms-litellm'
            ]
            
            found_packages = []
            for pkg in packages:
                for rel_pkg in relevant_packages:
                    if rel_pkg in pkg.lower():
                        found_packages.append(pkg.strip())
            
            if found_packages:
                for pkg in found_packages:
                    print(f"  {pkg}")
            else:
                print("  No relevant packages found in pip list")
        except Exception as e:
            print(f"  Error checking installed packages: {e}")
        
        # Print component versions if available
        try:
            import qdrant_client
            # Some packages use __version__, others use VERSION
            version = getattr(qdrant_client, "__version__", None)
            if version is None:
                version = getattr(qdrant_client, "VERSION", "unknown")
            print(f"Qdrant client version: {version}")
        except (ImportError, AttributeError):
            print("Qdrant client: NOT FOUND")
        
        try:
            import sentence_transformers
            print(f"Sentence-Transformers version: {sentence_transformers.__version__}")
        except (ImportError, AttributeError):
            print("Sentence-Transformers: NOT FOUND")
        
        try:
            from llama_index.core import __version__ as llama_index_version
            print(f"LlamaIndex version: {llama_index_version}")
        except (ImportError, AttributeError):
            try:
                # Fall back to older import style
                import llama_index
                version = getattr(llama_index, "__version__", "unknown")
                print(f"LlamaIndex version: {version}")
            except (ImportError, AttributeError):
                print("LlamaIndex: NOT FOUND")
    
    def handle_search(self, args: argparse.Namespace) -> None:
        """Handle the search command."""
        try:
            print(f"Searching for: '{args.query}'")
            if args.project_id:
                print(f"Filtered to project: {args.project_id}")
            
            # Initialize CodeRAG
            self._init_code_rag()
            
            # Perform the search with enhanced context if strategy is provided
            if hasattr(args, 'context_strategy') and args.context_strategy:
                print(f"Using context strategy: {args.context_strategy}")
                print(f"Using context count: {args.context_count}")
                
                # Perform the search with enhanced context
                results = self.code_rag.retrieve_relevant_code_enhanced(
                    query=args.query,
                    project_id=args.project_id,
                    top_k=args.limit,
                    context_strategy=args.context_strategy
                )
            else:
                # Use the original method
                results = self.code_rag.retrieve_relevant_code(
                    query=args.query,
                    project_id=args.project_id,
                    top_k=args.limit
                )
            
            # Display results
            print(f"\nFound {len(results)} relevant code fragments:")
            for i, result in enumerate(results):
                score_display = f"{result['score']:.4f}" if result['score'] is not None else "N/A"
                print(f"\nResult {i+1} (Score: {score_display}):")
                print(f"Filename: {result['metadata'].get('filename', 'unknown')}")
                print(f"Type: {result['metadata'].get('type', 'unknown')}")
                print(f"Name: {result['metadata'].get('name', 'unknown')}")
                print("Code snippet:")
                print(f"```python\n{result['text']}\n```")
        except Exception as e:
            logger.error(f"Search failed: {e}")
            print(f"Error: Search operation failed: {e}")
            sys.exit(1)
    
    def handle_generate(self, args: argparse.Namespace) -> None:
        """Handle the generate command."""
        try:
            print(f"Generating code for prompt: '{args.prompt}'")
            
            if args.project_id:
                # Verify that the project exists
                project = self.project_manager.get_project(args.project_id)
                if not project:
                    print(f"Error: Project not found: {args.project_id}")
                    sys.exit(1)
                
                print(f"Using context from project: {args.project_id} ({project['name']})")
                
                # Log the generation request in project metadata
                generation_history = project.get('metadata', {}).get('generation_history', [])
                if not generation_history:
                    generation_history = []
                
                generation_entry = {
                    'timestamp': datetime.now().isoformat(),
                    'prompt': args.prompt,
                    'model': args.model
                }
                
                if args.output:
                    generation_entry['output_file'] = args.output
                
                generation_history.append(generation_entry)
                
                # Update project metadata
                self.project_manager.update_project(
                    project_id=args.project_id,
                    metadata={
                        'last_generation': datetime.now().isoformat(),
                        'generation_history': generation_history
                    }
                )
            
            # Initialize CodeRAG with the specified model
            self._init_code_rag(model_name=args.model)
            
            # Generate code with enhanced context if strategy is provided
            if hasattr(args, 'context_strategy') and args.context_strategy:
                print(f"Using context strategy: {args.context_strategy}")
                print(f"Using context count: {args.context_count}")
                
                # Generate code with enhanced context
                response = self.code_rag.generate_with_enhanced_context(
                    query=args.prompt,
                    project_id=args.project_id,
                    context_strategy=args.context_strategy,
                    top_k=args.context_count,
                    system_prompt=None  # You can add a system_prompt arg if needed
                )
                
                # Update project metadata if applicable
                if args.project_id:
                    self.project_manager.update_project(
                        project_id=args.project_id,
                        metadata={
                            "last_context_strategy": args.context_strategy,
                            "last_context_count": args.context_count
                        }
                    )
            else:
                # Use the original method
                response = self.code_rag.generate_with_context(
                    query=args.prompt,
                    project_id=args.project_id
                )
            
            # Process and display the response
            if args.output:
                # Write to file
                with open(args.output, 'w') as f:
                    f.write(response)
                print(f"Generated code saved to: {args.output}")
                
                # If we have a project, add the generated file to it
                if args.project_id:
                    output_path = os.path.abspath(args.output)
                    self.project_manager.add_file_to_project(
                        project_id=args.project_id,
                        file_path=output_path,
                        file_type=self.project_manager._guess_file_type(output_path),
                        description=f"Generated from prompt: {args.prompt[:50]}..."
                    )
                    print(f"Added generated file to project: {args.project_id}")
            else:
                # Print to console
                print("\nGenerated Code:\n")
                print(response)
        except Exception as e:
            logger.error(f"Code generation failed: {e}")
            print(f"Error: Code generation failed: {e}")
            sys.exit(1)
    
    def handle_add(self, args: argparse.Namespace) -> None:
        """Handle the add command."""
        try:
            # Verify that the project exists
            project = self.project_manager.get_project(args.project_id)
            if not project:
                print(f"Error: Project not found: {args.project_id}")
                sys.exit(1)
            
            # Check if the input is a file path or a code string
            code = args.file
            if os.path.isfile(code):
                print(f"Reading code from file: {code}")
                filename = os.path.basename(code)
                with open(code, 'r') as f:
                    code = f.read()
                
                # Add file to project management
                self.project_manager.add_file_to_project(
                    project_id=args.project_id,
                    file_path=args.file,
                    file_type=args.file_type,
                    description="Added via CLI"
                )
                print(f"File added to project management: {args.file}")
            else:
                print("Adding code directly from command line")
                filename = f"cli_input_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py"
            
            # Initialize CodeRAG
            self._init_code_rag()
            
            # Prepare metadata
            metadata = {
                "filename": filename,
                "type": args.file_type,
            }
            
            if args.name:
                metadata["name"] = args.name
            
            # Add code to the index
            print(f"Adding code to vector database for project: {args.project_id}")
            doc_id = self.code_rag.add_code_to_index(
                code=code,
                metadata={
                    **metadata,
                    "project_id": args.project_id
                }
            )
            
            if doc_id:
                print(f"Successfully added code with ID: {doc_id}")
                
                # Update project metadata to track vector database entry
                self.project_manager.update_project(
                    project_id=args.project_id,
                    metadata={
                        "last_code_add": datetime.now().isoformat(),
                        "last_file_added": filename
                    }
                )
            else:
                print("Failed to add code to the index")
        except Exception as e:
            logger.error(f"Add operation failed: {e}")
            print(f"Error: Failed to add code: {e}")
            sys.exit(1)
    
    def handle_analyze(self, args: argparse.Namespace) -> None:
        """Handle the analyze command."""
        try:
            print(f"Analyzing query: '{args.query}'")
            
            # Initialize CodeRAG and context selector
            self._init_code_rag()
            
            # Get the context selector from code_rag
            if not hasattr(self.code_rag, '_context_selector'):
                from context_selector import ContextSelector
                self.code_rag._context_selector = ContextSelector(self.code_rag)
            
            context_selector = self.code_rag._context_selector
            
            # Analyze the query
            analysis = context_selector.analyze_query_complexity(args.query)
            
            # Print analysis results
            print("\nQuery Analysis:")
            print(f"Word count: {analysis['word_count']}")
            print(f"Structure count: {analysis['structure_count']}")
            
            print("\nDetected structures:")
            for structure_type, items in analysis['structures'].items():
                if items:
                    print(f"  {structure_type.capitalize()}: {', '.join(items)}")
                else:
                    print(f"  {structure_type.capitalize()}: None")
            
            print(f"\nRecommended context strategy: {analysis['optimal_strategy']}")
            
            # If args has project_id, demonstrate context selection with different strategies
            if args.project_id:
                print("\nDemonstrating context selection with different strategies:")
                strategies = ["semantic", "structural", "dependency", "balanced"]
                
                for strategy in strategies:
                    print(f"\n--- Strategy: {strategy} ---")
                    contexts = context_selector.select_context(
                        query=args.query,
                        project_id=args.project_id,
                        max_contexts=args.context_count,
                        context_strategy=strategy
                    )
                    print(f"Retrieved {len(contexts)} context fragments")
                    
                    # Show a brief summary of each context
                    for i, context in enumerate(contexts):
                        score = context.get('score', 0)
                        print(f"  {i+1}. {context['metadata'].get('name', 'unnamed')} "
                              f"({context['metadata'].get('type', 'unknown')}) - "
                              f"Score: {score:.4f}")
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            print(f"Error: Analysis operation failed: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
    
    def handle_project_list(self, args: argparse.Namespace) -> None:
        """Handle the project list command."""
        print("Listing projects...")
        
        # Get projects with optional filtering
        projects = self.project_manager.search_projects(
            query=args.query if hasattr(args, 'query') else None,
            tags=args.tags if hasattr(args, 'tags') else None
        )
        
        # Print projects
        if projects:
            print(f"Found {len(projects)} projects:")
            for project in projects:
                print(f"\nID: {project['id']}")
                print(f"Name: {project['name']}")
                
                if 'description' in project and project['description']:
                    print(f"Description: {project['description']}")
                
                if 'tags' in project and project['tags']:
                    print(f"Tags: {', '.join(project['tags'])}")
                
                if 'created_at' in project:
                    print(f"Created: {project['created_at']}")
                
                if 'files' in project and project['files']:
                    print(f"Files: {len(project['files'])}")
        else:
            print("No projects found")
    
    def handle_project_create(self, args: argparse.Namespace) -> None:
        """Handle the project create command."""
        print(f"Creating project: {args.name}")
        
        # Create the project
        project = self.project_manager.create_project(
            name=args.name,
            description=args.description,
            tags=args.tags,
            project_id=args.id if hasattr(args, 'id') else None
        )
        
        # Print result
        print(f"Project created successfully with ID: {project['id']}")
        print(f"Name: {project['name']}")
        
        if project['description']:
            print(f"Description: {project['description']}")
        
        if project['tags']:
            print(f"Tags: {', '.join(project['tags'])}")
    
    def handle_project_get(self, args: argparse.Namespace) -> None:
        """Handle the project get command."""
        project_id = args.id
        print(f"Getting project details: {project_id}")
        
        # Get the project
        project = self.project_manager.get_project(project_id)
        
        if project:
            # Add ID to the project data
            project_with_id = project.copy()
            project_with_id['id'] = project_id
            
            # Print project details
            print(f"Project ID: {project_id}")
            print(f"Name: {project['name']}")
            
            if 'description' in project and project['description']:
                print(f"Description: {project['description']}")
            
            if 'tags' in project and project['tags']:
                print(f"Tags: {', '.join(project['tags'])}")
            
            if 'created_at' in project:
                print(f"Created: {project['created_at']}")
            
            if 'updated_at' in project:
                print(f"Last updated: {project['updated_at']}")
            
            # Print files
            files = project.get('files', [])
            if files:
                print(f"\nFiles ({len(files)}):")
                for i, file in enumerate(files):
                    print(f"  {i+1}. {file['path']} ({file.get('type', 'unknown')})")
                    if 'description' in file and file['description']:
                        print(f"     Description: {file['description']}")
        else:
            print(f"Project not found: {project_id}")
            sys.exit(1)
    
    def handle_project_update(self, args: argparse.Namespace) -> None:
        """Handle the project update command."""
        project_id = args.id
        print(f"Updating project: {project_id}")
        
        # Update the project
        project = self.project_manager.update_project(
            project_id=project_id,
            name=args.name,
            description=args.description,
            tags=args.tags
        )
        
        if project:
            print(f"Project updated successfully: {project_id}")
            
            # Print updated fields
            if args.name:
                print(f"Name: {project['name']}")
                
            if args.description:
                print(f"Description: {project['description']}")
                
            if args.tags:
                print(f"Tags: {', '.join(project['tags'])}")
        else:
            print(f"Project not found: {project_id}")
            sys.exit(1)
    
    def handle_project_delete(self, args: argparse.Namespace) -> None:
        """Handle the project delete command."""
        project_id = args.id
        
        # Get confirmation unless --confirm flag is used
        if not args.confirm:
            confirmation = input(f"Are you sure you want to delete project '{project_id}'? (y/N): ")
            if confirmation.lower() not in ['y', 'yes']:
                print("Deletion cancelled.")
                return
        
        print(f"Deleting project: {project_id}")
        
        # Delete the project
        success = self.project_manager.delete_project(project_id)
        
        if success:
            print(f"Project deleted successfully: {project_id}")
        else:
            print(f"Failed to delete project: {project_id}")
            sys.exit(1)
    
    def handle_project_add_file(self, args: argparse.Namespace) -> None:
        """Handle the project add-file command."""
        project_id = args.id
        file_path = args.file
        
        print(f"Adding file to project: {file_path} -> {project_id}")
        
        # Add file to project
        success = self.project_manager.add_file_to_project(
            project_id=project_id,
            file_path=file_path,
            file_type=args.type,
            description=args.description
        )
        
        if success:
            print(f"File added successfully: {file_path}")
        else:
            print(f"Failed to add file to project")
            sys.exit(1)
    
    def handle_project_export(self, args: argparse.Namespace) -> None:
        """Handle the project export command."""
        project_id = args.id
        
        print(f"Exporting project: {project_id}")
        
        # Export the project
        output_file = self.project_manager.export_project(
            project_id=project_id,
            output_file=args.output
        )
        
        if output_file:
            print(f"Project exported successfully to: {output_file}")
        else:
            print(f"Failed to export project: {project_id}")
            sys.exit(1)
    
    def handle_project_import(self, args: argparse.Namespace) -> None:
        """Handle the project import command."""
        file_path = args.file
        
        print(f"Importing project from: {file_path}")
        
        # Import the project
        project = self.project_manager.import_project(
            input_file=file_path,
            override_existing=args.override
        )
        
        if project:
            print(f"Project imported successfully: {project['id']}")
            print(f"Name: {project['name']}")
            
            if 'description' in project and project['description']:
                print(f"Description: {project['description']}")
                
            if 'tags' in project and project['tags']:
                print(f"Tags: {', '.join(project['tags'])}")
        else:
            print(f"Failed to import project from: {file_path}")
            sys.exit(1)
    
    def handle_init(self, args: argparse.Namespace) -> None:
        """Handle the init command."""
        print("Initializing DevAgent environment...")
        
        # Check if Qdrant is running
        if not check_qdrant_health():
            print("Qdrant is not healthy. Please start the services first.")
            sys.exit(1)
        
        # Create collections if they don't exist
        print("Creating Qdrant collections...")
        result = create_collections()
        
        if all(result.values()):
            print("Initialization successful!")
        else:
            print("Some collections failed to initialize. Check the logs for details.")
    
    def handle_session_list(self, args: argparse.Namespace) -> None:
        """Handle the session list command."""
        print("Listing available sessions...")
        
        sessions = self.session_manager.list_sessions()
        
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
                
                if "last_activity" in session:
                    print(f"Last activity: {session['last_activity']}")
        else:
            print("No sessions found")

    def handle_session_create(self, args: argparse.Namespace) -> None:
        """Handle the session create command."""
        print(f"Creating session: {args.name}")
        
        # If a project ID is provided, verify it exists
        if args.project_id:
            project = self.project_manager.get_project(args.project_id)
            if not project:
                print(f"Error: Project not found: {args.project_id}")
                sys.exit(1)
            
            print(f"Associated with project: {args.project_id} ({project['name']})")
        
        # Create the session
        session = self.session_manager.create_session(
            name=args.name,
            description=args.description,
            project_id=args.project_id,
            tags=args.tags
        )
        
        # Print result
        print(f"Session created successfully with ID: {session['id']}")
        print(f"Name: {session['name']}")
        
        if session.get('description'):
            print(f"Description: {session['description']}")
        
        if session.get('tags'):
            print(f"Tags: {', '.join(session['tags'])}")
        
        print(f"Started: {session['start_time']}")

    def handle_session_load(self, args: argparse.Namespace) -> None:
        """Handle the session load command."""
        session_id = args.id
        print(f"Loading session: {session_id}")
        
        # Load the session
        session = self.session_manager.load_session(session_id)
        
        if session:
            print(f"Session loaded successfully: {session['id']}")
            print(f"Name: {session['name']}")
            
            if session.get('project_id'):
                print(f"Project: {session['project_id']}")
                
                # Set up environment for project if needed
                # For example, load related data from project into context
                project = self.project_manager.get_project(session['project_id'])
                if project:
                    print(f"Associated project: {project['name']}")
                    
                    # Add project info to session context
                    self.session_manager.set_context_value('project_name', project['name'])
                    self.session_manager.set_context_value('project_files', project.get('files', []))
        else:
            print(f"Failed to load session: {session_id}")
            sys.exit(1)

    def handle_session_info(self, args: argparse.Namespace) -> None:
        """Handle the session info command."""
        print("Getting active session information...")
        
        session = self.session_manager.get_active_session()
        
        if session:
            print(f"Active session: {session['id']}")
            print(f"Name: {session['name']}")
            
            if session.get('description'):
                print(f"Description: {session['description']}")
            
            if session.get('project_id'):
                print(f"Project: {session['project_id']}")
            
            print(f"Started: {session['start_time']}")
            print(f"Last activity: {session['last_activity']}")
            print(f"Status: {session.get('status', 'unknown')}")
            
            # Get context information
            context = self.session_manager.session_data.get('context', {})
            if context:
                print("\nSession context:")
                for key, value in context.items():
                    if isinstance(value, dict) and len(value) > 5:
                        print(f"  {key}: {type(value).__name__} with {len(value)} items")
                    elif isinstance(value, list) and len(value) > 5:
                        print(f"  {key}: List with {len(value)} items")
                    else:
                        # Truncate long values
                        value_str = str(value)
                        if len(value_str) > 50:
                            value_str = value_str[:50] + "..."
                        print(f"  {key}: {value_str}")
            
            # Get history information
            history = self.session_manager.session_data.get('history', [])
            if history:
                print(f"\nCommand history: {len(history)} entries")
                print(f"Last command: {self.session_manager.session_data.get('state', {}).get('last_command', 'none')}")
        else:
            print("No active session")
            print("Use 'devagent session create' to create a new session or 'devagent session load' to load an existing one.")

    def handle_session_close(self, args: argparse.Namespace) -> None:
        """Handle the session close command."""
        print("Closing active session...")
        
        session = self.session_manager.get_active_session()
        
        if session:
            session_id = session['id']
            success = self.session_manager.close_session()
            
            if success:
                print(f"Session closed successfully: {session_id}")
            else:
                print("Failed to close session")
                sys.exit(1)
        else:
            print("No active session to close")

    def handle_session_reset(self, args: argparse.Namespace) -> None:
        """Handle the session reset command."""
        print("Resetting active session...")
        
        session = self.session_manager.get_active_session()
        
        if session:
            session_id = session['id']
            success = self.session_manager.reset_session()
            
            if success:
                print(f"Session reset successfully: {session_id}")
                print("History and state have been cleared, but context is preserved.")
            else:
                print("Failed to reset session")
                sys.exit(1)
        else:
            print("No active session to reset")

    def handle_session_export(self, args: argparse.Namespace) -> None:
        """Handle the session export command."""
        session_id = args.id
        
        if not session_id:
            session = self.session_manager.get_active_session()
            if not session:
                print("No active session to export")
                print("Please provide a session ID or load a session first")
                sys.exit(1)
            session_id = session['id']
        
        print(f"Exporting session: {session_id}")
        
        # Export the session
        output_file = self.session_manager.export_session(session_id, args.output)
        
        if output_file:
            print(f"Session exported successfully to: {output_file}")
        else:
            print(f"Failed to export session: {session_id}")
            sys.exit(1)

    def handle_session_import(self, args: argparse.Namespace) -> None:
        """Handle the session import command."""
        file_path = args.file
        
        print(f"Importing session from: {file_path}")
        
        # Import the session
        session = self.session_manager.import_session(
            input_file=file_path,
            overwrite=args.overwrite
        )
        
        if session:
            print(f"Session imported successfully with ID: {session['id']}")
            print(f"Name: {session['name']}")
            
            if session.get('description'):
                print(f"Description: {session['description']}")
            
            if session.get('project_id'):
                print(f"Project: {session['project_id']}")
                
                # Verify the project exists
                project = self.project_manager.get_project(session['project_id'])
                if not project:
                    print(f"Warning: Associated project not found: {session['project_id']}")
                    print("You may need to import the project as well.")
        else:
            print(f"Failed to import session from: {file_path}")
            sys.exit(1)

    def handle_session_delete(self, args: argparse.Namespace) -> None:
        """Handle the session delete command."""
        session_id = args.id
        
        # Get confirmation unless --confirm flag is used
        if not args.confirm:
            confirmation = input(f"Are you sure you want to delete session '{session_id}'? (y/N): ")
            if confirmation.lower() not in ['y', 'yes']:
                print("Deletion cancelled.")
                return
        
        print(f"Deleting session: {session_id}")
        
        # Delete the session
        success = self.session_manager.delete_session(session_id)
        
        if success:
            print(f"Session deleted successfully: {session_id}")
        else:
            print(f"Failed to delete session: {session_id}")
            sys.exit(1)

    def handle_session_history(self, args: argparse.Namespace) -> None:
        """Handle the session history command."""
        print("Getting session command history...")
        
        history = self.session_manager.get_session_history(
            limit=args.limit,
            command_filter=args.filter
        )
        
        if history:
            print(f"Command history ({len(history)} entries):")
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
            print("Check if you have an active session or try loading one first.")
    
    def run(self, args: List[str] = None) -> None:
        """Run the CLI with the given arguments."""
        # Parse arguments 
        args_namespace = self.parser.parse_args(args)

        # Get active session to track history
        active_session = self.session_manager.get_active_session()

        # Record command in history if we have an active session
        if active_session and args_namespace.command != "session":
            self.session_manager.add_to_history(
                command=args_namespace.command,
                args=vars(args_namespace)
            )
        
        # Configure logging based on verbosity
        if args_namespace.verbose:
            logger.setLevel(logging.DEBUG)
        elif args_namespace.quiet:
            logger.setLevel(logging.ERROR)
        
        # Execute appropriate command
        try:
            if args_namespace.command == "status":
                self.handle_status(args_namespace)
            elif args_namespace.command == "search":
                self.handle_search(args_namespace)
            elif args_namespace.command == "generate":
                self.handle_generate(args_namespace)
            elif args_namespace.command == "add":
                self.handle_add(args_namespace)
            elif args_namespace.command == "analyze":
                self.handle_analyze(args_namespace)
            elif args_namespace.command == "project":
                if args_namespace.project_command == "list":
                    self.handle_project_list(args_namespace)
                elif args_namespace.project_command == "create":
                    self.handle_project_create(args_namespace)
                elif args_namespace.project_command == "get":
                    self.handle_project_get(args_namespace)
                elif args_namespace.project_command == "update":
                    self.handle_project_update(args_namespace)
                elif args_namespace.project_command == "delete":
                    self.handle_project_delete(args_namespace)
                elif args_namespace.project_command == "add-file":
                    self.handle_project_add_file(args_namespace)
                elif args_namespace.project_command == "export":
                    self.handle_project_export(args_namespace)
                elif args_namespace.project_command == "import":
                    self.handle_project_import(args_namespace)
                else:
                    print("Error: No project subcommand specified")
                    sys.exit(1)
            elif args_namespace.command == "session":
                if args_namespace.session_command == "list":
                    self.handle_session_list(args_namespace)
                elif args_namespace.session_command == "create":
                    self.handle_session_create(args_namespace)
                elif args_namespace.session_command == "load":
                    self.handle_session_load(args_namespace)
                elif args_namespace.session_command == "info":
                    self.handle_session_info(args_namespace)
                elif args_namespace.session_command == "close":
                    self.handle_session_close(args_namespace)
                elif args_namespace.session_command == "reset":
                    self.handle_session_reset(args_namespace)
                elif args_namespace.session_command == "export":
                    self.handle_session_export(args_namespace)
                elif args_namespace.session_command == "import":
                    self.handle_session_import(args_namespace)
                elif args_namespace.session_command == "delete":
                    self.handle_session_delete(args_namespace)
                elif args_namespace.session_command == "history":
                    self.handle_session_history(args_namespace)
                else:
                    print("Error: No session subcommand specified")
                    sys.exit(1)
            elif args_namespace.command == "init":
                self.handle_init(args_namespace)
            else:
                self.parser.print_help()
        except Exception as e:
            # Record error in session history if we have an active session
            if active_session:
                self.session_manager.add_to_history(
                    command=args_namespace.command if hasattr(args_namespace, 'command') else "unknown",
                    args=vars(args_namespace) if hasattr(args_namespace, 'command') else {},
                    error=str(e)
                )

            logger.error(f"Command failed: {e}")
            print(f"Error: {e}")
            if args_namespace.verbose:
                import traceback
                traceback.print_exc()
            sys.exit(1)

        # Record success in session history if applicable
        if active_session and args_namespace.command != "session":
            self.session_manager.add_to_history(
                command=args_namespace.command,
                args=vars(args_namespace),
                result="Success"
            )

if __name__ == "__main__":
    cli = DevAgentCLI()
    cli.run()
