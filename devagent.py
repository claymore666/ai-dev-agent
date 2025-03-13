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
        
        return parser
    
    def _init_code_rag(self, model_name: str = "ollama-codellama") -> None:
        """Initialize the CodeRAG component if not already initialized."""
        if self.code_rag is None:
            try:
                logger.info(f"Initializing CodeRAG with model: {model_name}")
                self.code_rag = CodeRAG(llm_model_name=model_name)
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
    
    def run(self, args: List[str] = None) -> None:
        """Run the CLI with the given arguments."""
        # Parse arguments
        args = self.parser.parse_args(args)
        
        # Configure logging based on verbosity
        if args.verbose:
            logger.setLevel(logging.DEBUG)
        elif args.quiet:
            logger.setLevel(logging.ERROR)
        
        # Execute appropriate command
        try:
            if args.command == "status":
                self.handle_status(args)
            elif args.command == "search":
                self.handle_search(args)
            elif args.command == "generate":
                self.handle_generate(args)
            elif args.command == "add":
                self.handle_add(args)
            elif args.command == "analyze":
                self.handle_analyze(args)
            elif args.command == "project":
                if args.project_command == "list":
                    self.handle_project_list(args)
                elif args.project_command == "create":
                    self.handle_project_create(args)
                elif args.project_command == "get":
                    self.handle_project_get(args)
                elif args.project_command == "update":
                    self.handle_project_update(args)
                elif args.project_command == "delete":
                    self.handle_project_delete(args)
                elif args.project_command == "add-file":
                    self.handle_project_add_file(args)
                elif args.project_command == "export":
                    self.handle_project_export(args)
                elif args.project_command == "import":
                    self.handle_project_import(args)
                else:
                    print("Error: No project subcommand specified")
                    sys.exit(1)
            elif args.command == "init":
                self.handle_init(args)
            else:
                self.parser.print_help()
        except Exception as e:
            logger.error(f"Command failed: {e}")
            print(f"Error: {e}")
            if args.verbose:
                import traceback
                traceback.print_exc()
            sys.exit(1)

if __name__ == "__main__":
    cli = DevAgentCLI()
    cli.run()
