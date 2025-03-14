#!/usr/bin/env python3
"""
Code RAG (Retrieval Augmented Generation) for AI Development Agent
This script implements a RAG system for code-related queries using LlamaIndex and Qdrant.
"""

import os
import sys
import argparse
import json
from typing import List, Dict, Any, Optional, Tuple, Set

from dotenv import load_dotenv
import requests
from sentence_transformers import SentenceTransformer
from llama_index.core import Settings, ServiceContext
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.schema import Document, QueryBundle
from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_index.core.indices.vector_store import VectorStoreIndex
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.llms.litellm import LiteLLM
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

# Import Redis cache handler
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
try:
    from litellm_utils.redis_cache import patch_litellm
except ImportError:
    patch_litellm = None
from qdrant_client import QdrantClient

# Load environment variables
load_dotenv()

# Configuration
LITELLM_HOST = os.getenv("LITELLM_HOST", "localhost")
LITELLM_PORT = os.getenv("LITELLM_PORT", "8081")
LITELLM_URL = f"http://{LITELLM_HOST}:{LITELLM_PORT}"

QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = os.getenv("QDRANT_PORT", "6333")
QDRANT_URL = f"http://{QDRANT_HOST}:{QDRANT_PORT}"

# Collection names
CODE_COLLECTION = "code_fragments"

class CodeRAG:
    """RAG system for code-related queries."""
    
    def __init__(
        self,
        embedding_model_name: str = "all-MiniLM-L6-v2",
        session_manager = None,
        llm_model_name: str = "ollama-codellama",
        max_input_size: int = 4096,
        num_output: int = 1024,
        max_chunk_overlap: int = 20,
        chunk_size: int = 512,
    ):
        """
        Initialize the CodeRAG system.
        
        Args:
            embedding_model_name: Name of the embedding model to use
            llm_model_name: Name of the LLM model to use via LiteLLM
            max_input_size: Maximum input size for the LLM
            num_output: Maximum output size from the LLM
            max_chunk_overlap: Maximum overlap between chunks when splitting text
            chunk_size: Size of chunks when splitting text
        """
        self.embedding_model_name = embedding_model_name

        # Apply Redis cache patch to LiteLLM if available
        if patch_litellm:
            patch_successful = patch_litellm()
            if patch_successful:
                print("LiteLLM successfully patched to use Redis cache")
            else:
                print("Warning: Failed to patch LiteLLM with Redis cache")
        self.llm_model_name = llm_model_name
        self.session_manager = session_manager
        
        # Load embedding model
        print(f"Loading embedding model: {embedding_model_name}")
        self.embed_model = HuggingFaceEmbedding(model_name=embedding_model_name)
        
        # Initialize LLM client
        print(f"Initializing LLM client with model: {llm_model_name}")
        self.llm = LiteLLM(
            model_name=llm_model_name,
            api_base=LITELLM_URL,
            api_key="NOT_NEEDED",  # Add a dummy API key
            temperature=0.1,
            max_tokens=num_output,
            additional_kwargs={
                "engine": llm_model_name,  # Ensure model name is passed correctly
                "complete_response": True,  # Return complete response
                "api_type": "local",        # Specify we're using a local API
                "request_timeout": 120,     # Increase timeout for local models
            }
        )
        
        # Configure LlamaIndex settings
        Settings.llm = self.llm
        Settings.embed_model = self.embed_model
        
        # Initialize node parser for code chunking
        self.node_parser = SentenceSplitter(
            chunk_size=chunk_size,
            chunk_overlap=max_chunk_overlap,
            paragraph_separator="\n\n",
        )
        
        # Initialize Qdrant vector store
        qdrant_client = QdrantClient(url=QDRANT_URL)
        self.vector_store = QdrantVectorStore(
            client=qdrant_client,
            collection_name=CODE_COLLECTION,
        )
        
        # Create vector store index
        self.index = VectorStoreIndex.from_vector_store(self.vector_store)
        
        # Configure retriever
        self.retriever = VectorIndexRetriever(
            index=self.index,
            similarity_top_k=5,  # Retrieve top 5 most similar code fragments
        )
    
    def add_code_to_index(
        self, 
        code: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Add code to the index.
        
        Args:
            code: The code to add
            metadata: Additional metadata about the code
            
        Returns:
            ID of the added document
        """
        if metadata is None:
            metadata = {}
        
        # Create document
        doc = Document(text=code, metadata=metadata)
        
        # Split into nodes
        nodes = self.node_parser.get_nodes_from_documents([doc])
        
        # Add to index
        self.index.insert_nodes(nodes)
        
        return nodes[0].id_ if nodes else ""
    
    def retrieve_relevant_code(
        self,
        query: str,
        project_id: Optional[str] = None,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant code fragments for a query.
        
        Args:
            query: The query to search for
            project_id: Optional project ID to filter by
            top_k: Number of results to return
            
        Returns:
            List of relevant code fragments with metadata
        """
        # Create query bundle
        query_bundle = QueryBundle(query_str=query)
        
        # Set filter if project_id is provided
        if project_id:
            self.retriever.filters = {"project_id": project_id}
        else:
            self.retriever.filters = None
        
        # Update top_k
        self.retriever.similarity_top_k = top_k
        
        # Retrieve nodes
        nodes = self.retriever.retrieve(query_bundle)
        
        # Format results
        results = []
        for node in nodes:
            results.append({
                "text": node.text,
                "metadata": node.metadata,
                "score": node.score if hasattr(node, "score") else None,
            })
        
        return results
    
    def retrieve_relevant_code_enhanced(
        self,
        query: str,
        project_id: Optional[str] = None,
        top_k: int = 5,
        context_strategy: str = "balanced"
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant code fragments for a query using advanced context selection.
        
        Args:
            query: The query to search for
            project_id: Optional project ID to filter by
            top_k: Number of results to return
            context_strategy: Strategy to use for context selection
                - "semantic": Pure semantic similarity (basic RAG)
                - "structural": Prioritize structurally related code
                - "dependency": Prioritize code with dependencies
                - "balanced": Balance between semantic and structural relevance
                - "auto": Automatically select the best strategy based on query
            
        Returns:
            List of relevant code fragments with metadata
        """
        # Import here to avoid circular imports
        from context_selector import ContextSelector
        
        # Lazy initialize the context selector
        if not hasattr(self, '_context_selector'):
            self._context_selector = ContextSelector(self)
        
        if context_strategy == "auto":
            # Auto-select strategy based on query complexity
            analysis = self._context_selector.analyze_query_complexity(query)
            context_strategy = analysis["optimal_strategy"]
        
        # Use the context selector to get enhanced results
        return self._context_selector.select_context(
            query=query,
            project_id=project_id,
            max_contexts=top_k,
            context_strategy=context_strategy,
            session_manager=self.session_manager
        )
    
    def generate_with_context(
        self,
        query: str,
        project_id: Optional[str] = None,
        context_results: Optional[List[Dict[str, Any]]] = None,
        system_prompt: Optional[str] = None
    ) -> str:
        """
        Generate a response with context from retrieved code.
        
        Args:
            query: The query to answer
            project_id: Optional project ID to filter by
            context_results: Optional pre-retrieved context
            system_prompt: Optional system prompt
            
        Returns:
            Generated response
        """
        # Retrieve context if not provided
        if context_results is None:
            context_results = self.retrieve_relevant_code(query, project_id)
        
        # Default system prompt for code tasks
        if system_prompt is None:
            system_prompt = """
            You are an expert software developer specializing in Python.
            You help write, explain, and improve code based on the provided context.
            You prioritize writing maintainable, efficient code that follows best practices.
            Always consider the context of existing code when generating new code.
            """
        
        # Format context
        context_text = "\n\n".join([
            f"```python\n{result['text']}\n```\n" +
            f"Filename: {result['metadata'].get('filename', 'unknown')}\n" +
            f"Type: {result['metadata'].get('type', 'unknown')}\n" +
            f"Name: {result['metadata'].get('name', 'unknown')}\n"
            for result in context_results
        ])
        
        # Create prompt with context
        prompt = f"""
        Based on the following code context:
        
        {context_text}
        
        {query}
        """
        
        # Direct call to LiteLLM API using the known model name
        try:
            # Create a combined prompt with the system prompt and user query
            combined_prompt = f"""{system_prompt}

Based on the following code context:

{context_text}

{query}
"""
            
            payload = {
                "model": self.llm_model_name,  # Now has the correct name with prefix
                "messages": [
                    {"role": "user", "content": combined_prompt}
                ]
            }
            
            print(f"Sending request to LiteLLM API with model: {self.llm_model_name}")
            response = requests.post(
                f"{LITELLM_URL}/v1/chat/completions",
                headers={"Content-Type": "application/json"},
                json=payload
            )
            
            if response.status_code == 200:
                result = response.json()
                return result["choices"][0]["message"]["content"]
            else:
                error_message = f"LiteLLM API error: Status code {response.status_code}. Details: {response.text}"
                print(error_message)
                return f"Error: {error_message}"
                
        except Exception as e:
            error_message = f"Error generating response: {str(e)}"
            print(error_message)
            return f"Error: {error_message}"

    def generate_with_enhanced_context(
        self,
        query: str,
        project_id: Optional[str] = None,
        context_strategy: str = "auto",
        top_k: int = 5,
        system_prompt: Optional[str] = None,
    ) -> str:
        """
        Generate a response with enhanced context selection.
        
        Args:
            query: The query to answer
            project_id: Optional project ID to filter by
            context_strategy: Strategy for context selection
            top_k: Number of context fragments to retrieve
            system_prompt: Optional system prompt
            
        Returns:
            Generated response
        """
        # Retrieve context with enhanced selection
        context_results = self.retrieve_relevant_code_enhanced(
            query=query, 
            project_id=project_id,
            top_k=top_k,
            context_strategy=context_strategy
        )
        
        # Use the existing generation method with the enhanced context
        return self.generate_with_context(
            query=query,
            project_id=project_id,
            context_results=context_results,
            system_prompt=system_prompt
        )

def main():
    """Command-line interface for CodeRAG."""
    parser = argparse.ArgumentParser(description="Code RAG for AI Development Agent")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Add code command
    add_parser = subparsers.add_parser("add", help="Add code to the index")
    add_parser.add_argument("--code", required=True, help="Code to add or path to code file")
    add_parser.add_argument("--filename", required=True, help="Filename for the code")
    add_parser.add_argument("--project-id", required=True, help="Project ID")
    add_parser.add_argument("--type", help="Type of code (function, class, module)")
    add_parser.add_argument("--name", help="Name of the code entity")
    add_parser.add_argument("--description", help="Description of the code")
    
    # Search command
    search_parser = subparsers.add_parser("search", help="Search for relevant code")
    search_parser.add_argument("--query", required=True, help="Query to search for")
    search_parser.add_argument("--project-id", help="Optional project ID to filter by")
    search_parser.add_argument("--top-k", type=int, default=5, help="Number of results to return")
    search_parser.add_argument(
        "--strategy",
        choices=["semantic", "structural", "dependency", "balanced", "auto"],
        default="auto",
        help="Context strategy to use (default: auto)"
    )
    
    # Generate command
    generate_parser = subparsers.add_parser("generate", help="Generate code with context")
    generate_parser.add_argument("--query", required=True, help="Query for code generation")
    generate_parser.add_argument("--project-id", help="Optional project ID to filter by")
    generate_parser.add_argument("--system-prompt", help="Optional system prompt")
    generate_parser.add_argument(
        "--strategy",
        choices=["semantic", "structural", "dependency", "balanced", "auto"],
        default="auto",
        help="Context strategy to use (default: auto)"
    )
    
    args = parser.parse_args()
    
    # Initialize CodeRAG
    rag = CodeRAG()
    
    # Execute commands
    if args.command == "add":
        # Check if code is a file path or direct code
        code = args.code
        if os.path.isfile(code):
            with open(code, "r") as f:
                code = f.read()
        
        # Prepare metadata
        metadata = {
            "filename": args.filename,
            "project_id": args.project_id,
        }
        
        if args.type:
            metadata["type"] = args.type
        if args.name:
            metadata["name"] = args.name
        if args.description:
            metadata["description"] = args.description
        
        # Add code to index
        doc_id = rag.add_code_to_index(code, metadata)
        print(f"Added code to index with ID: {doc_id}")
    
    elif args.command == "search":
        # Search for relevant code
        if hasattr(args, 'strategy') and args.strategy:
            print(f"Using enhanced context selection with strategy: {args.strategy}")
            results = rag.retrieve_relevant_code_enhanced(
                query=args.query,
                project_id=args.project_id,
                top_k=args.top_k,
                context_strategy=args.strategy
            )
        else:
            # Use the original method
            results = rag.retrieve_relevant_code(
                query=args.query,
                project_id=args.project_id,
                top_k=args.top_k
            )
        
        # Print results
        print(f"Found {len(results)} relevant code fragments:")
        for i, result in enumerate(results):
            print(f"\nResult {i+1}:")
            print(f"Score: {result['score']}")
            print(f"Filename: {result['metadata'].get('filename', 'unknown')}")
            print(f"Type: {result['metadata'].get('type', 'unknown')}")
            print(f"Name: {result['metadata'].get('name', 'unknown')}")
            print("Code snippet:")
            print(f"```python\n{result['text']}\n```")
    
    elif args.command == "generate":
        # Generate code with context
        if hasattr(args, 'strategy') and args.strategy:
            print(f"Using enhanced context selection with strategy: {args.strategy}")
            response = rag.generate_with_enhanced_context(
                query=args.query,
                project_id=args.project_id,
                context_strategy=args.strategy,
                top_k=args.top_k,
                system_prompt=args.system_prompt
            )
        else:
            # Use the original method
            response = rag.generate_with_context(
                query=args.query,
                project_id=args.project_id,
                system_prompt=args.system_prompt
            )
        
        print("\nGenerated Response:")
        print("===================")
        print(response)
    
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
