import os
import sys
import json
import logging
import hashlib
import requests
import yaml
from typing import List, Dict, Any, Optional, Tuple, Set
import numpy as np

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("context_selector")

# Import Redis for caching
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("Redis not available for query classification caching")

# Load configuration from the same file as LiteLLM
def load_config():
    """Load configuration from LiteLLM config file"""
    config_paths = [
        os.path.join('configs', 'litellm_config.yaml'),  # Standard location in project
        os.environ.get('CONFIG_FILE_PATH', ''),          # From environment variable
        '/app/config.yaml'                               # Docker container location
    ]
    
    for path in config_paths:
        if os.path.exists(path):
            try:
                with open(path, 'r') as f:
                    config = yaml.safe_load(f)
                logger.info(f"Loaded configuration from {path}")
                return config
            except Exception as e:
                logger.warning(f"Error loading config from {path}: {e}")
    
    logger.warning("No configuration file found, using defaults")
    return {}

# Load configuration
config = load_config()

# Redis configuration (from LiteLLM settings)
litellm_settings = config.get('litellm_settings', {})
cache_params = litellm_settings.get('cache_params', {})

# Get Redis host from environment variables or config
REDIS_HOST = os.getenv("REDIS_HOST", cache_params.get('host', 'localhost'))
REDIS_PORT = int(os.getenv("REDIS_PORT", str(cache_params.get('port', 6379))))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", cache_params.get('password', ''))
REDIS_DB = int(os.getenv("REDIS_DB", str(cache_params.get('db', 0))))
REDIS_CACHE_EXPIRY = int(os.getenv("REDIS_CACHE_EXPIRY", "86400"))  # 1 day default

# Server configuration
server_config = config.get('server', {})
LITELLM_HOST = os.getenv("LITELLM_HOST", server_config.get('host', 'localhost'))
LITELLM_PORT = os.getenv("LITELLM_PORT", str(server_config.get('port', 8080)))
LITELLM_API = f"http://{LITELLM_HOST}:{LITELLM_PORT}/v1/chat/completions"

# Model configuration
model_list = config.get('model_list', [])
CLASSIFY_MODEL = None

# Find a fast model for classification
for model in model_list:
    model_name = model.get('model_name', '')
    # Prioritize smaller models like llama2 over larger ones like codellama for classification
    if 'llama2' in model_name.lower():
        CLASSIFY_MODEL = model_name
        break

# If no suitable model found, use the default model
if not CLASSIFY_MODEL:
    CLASSIFY_MODEL = litellm_settings.get('default_model', 'ollama-llama2')

logger.info(f"Using model {CLASSIFY_MODEL} for query classification")

# Try to set up Redis client
redis_client = None
if REDIS_AVAILABLE and litellm_settings.get('cache', False):
    try:
        redis_client = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            password=REDIS_PASSWORD if REDIS_PASSWORD else None,
            db=REDIS_DB,
            socket_timeout=5
        )
        # Test connection
        redis_client.ping()
        logger.info("Redis connection established for query classification caching")
    except Exception as e:
        logger.warning(f"Failed to connect to Redis: {e}")
        redis_client = None

class ContextSelector:
    """Advanced context selection for code generation."""
    
    def __init__(self, rag_system: Any):
        """
        Initialize the context selector.
        
        Args:
            rag_system: The RAG system to use for retrieving context
        """
        self.rag = rag_system
    
    def is_conversation_meta_query(self, query: str) -> bool:
        """
        Determine if a query is asking about the conversation itself using LLM classification.
        
        Args:
            query: The query string to analyze
            
        Returns:
            True if the query is about the conversation, False otherwise
        """
        # Create a unique cache key based on the lowercase query
        query_hash = hashlib.md5(query.lower().encode()).hexdigest()
        cache_key = f"query_classification:{query_hash}"
        
        # Try to get result from cache if Redis is available
        if redis_client:
            try:
                cached_result = redis_client.get(cache_key)
                if cached_result:
                    is_conversation = cached_result.decode('utf-8') == 'conversation'
                    logger.debug(f"Cache hit for query classification: {query} -> {is_conversation}")
                    return is_conversation
            except Exception as e:
                logger.warning(f"Redis cache lookup failed: {e}")
        
        # If not cached or cache lookup failed, use LLM to classify
        is_conversation = self._classify_query_with_llm(query)
        
        # Cache the result if Redis is available
        if redis_client:
            try:
                cache_value = 'conversation' if is_conversation else 'code'
                redis_client.set(cache_key, cache_value, ex=REDIS_CACHE_EXPIRY)
                logger.debug(f"Cached query classification: {query} -> {cache_value}")
            except Exception as e:
                logger.warning(f"Redis cache set failed: {e}")
        
        return is_conversation
    
    def _classify_query_with_llm(self, query: str) -> bool:
        """
        Use a lightweight LLM to classify the query as conversation-related or code-related.
        
        Args:
            query: The query string to classify
            
        Returns:
            True if the query is about the conversation, False otherwise
        """
        # Construct a simple, focused prompt for classification
        prompt = {
            "model": CLASSIFY_MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a query classifier that categorizes user queries as either CONVERSATION or CODE. "
                               "CONVERSATION queries are about the chat history, summarizing previous interactions, or the discussion flow. "
                               "CODE queries are about programming, technical implementation, or software development. "
                               "Respond with only a single word: either CONVERSATION or CODE."
                },
                {
                    "role": "user",
                    "content": f"Classify this query: \"{query}\""
                }
            ],
            "max_tokens": 10,  # Keep response short for efficiency
            "temperature": 0.1  # Low temperature for more deterministic classification
        }
        
        try:
            # Make API call to LiteLLM
            response = requests.post(
                LITELLM_API,
                headers={"Content-Type": "application/json"},
                json=prompt,
                timeout=5  # Short timeout for quick classification
            )
            
            if response.status_code == 200:
                # Extract the classification from the response
                result = response.json()
                classification = result["choices"][0]["message"]["content"].strip().upper()
                
                # Determine if this is a conversation query
                is_conversation = "CONVERSATION" in classification
                logger.debug(f"LLM classified query: {query} -> {classification}")
                
                return is_conversation
            else:
                logger.warning(f"LiteLLM API error: {response.status_code} - {response.text}")
                # Default to treating as a code query if classification fails
                return False
                
        except Exception as e:
            logger.warning(f"Query classification error: {e}")
            # Default to treating as a code query if classification fails
            return False
    
    def select_context(
        self,
        query: str,
        project_id: str,
        max_contexts: int = 5,
        context_strategy: str = "balanced",
        session_manager = None
    ) -> List[Dict[str, Any]]:
        """
        Select relevant context for a query using advanced strategies.
        
        Args:
            query: The query to retrieve context for
            project_id: The project ID to filter by
            max_contexts: Maximum number of context fragments to return
            context_strategy: Strategy to use for context selection
                - "semantic": Pure semantic similarity (basic RAG)
                - "structural": Prioritize structurally related code
                - "dependency": Prioritize code with dependencies
                - "balanced": Balance between semantic and structural relevance
                - "conversation": Use session history for conversation meta-queries
                - "auto": Automatically select strategy based on query
            session_manager: Optional session manager for accessing history
                
        Returns:
            List of context fragments
        """
        # Auto-detect if this is a conversation meta-query
        if context_strategy == "auto":
            # Only use conversation strategy if we have a session manager AND an active session
            has_active_session = session_manager and session_manager.get_active_session()
            
            if self.is_conversation_meta_query(query) and has_active_session:
                logger.info(f"Detected conversation meta-query: '{query}'")
                context_strategy = "conversation"
                logger.debug(f"Selected 'conversation' context strategy for query")
            else:
                # Use the original strategy selection for code queries
                analysis = self.analyze_query_complexity(query)
                context_strategy = analysis["optimal_strategy"]
                logger.debug(f"Selected '{context_strategy}' context strategy for query")
        
        # Apply the selected strategy
        if context_strategy == "semantic":
            return self._semantic_context(query, project_id, max_contexts)
        elif context_strategy == "conversation":
            if session_manager:
                return self._conversation_context(query, project_id, max_contexts, session_manager)
            else:
                logger.warning("No session manager provided for conversation context strategy, falling back to semantic")
                return self._semantic_context(query, project_id, max_contexts)
        elif context_strategy == "structural":
            return self._structural_context(query, project_id, max_contexts)
        elif context_strategy == "dependency":
            return self._dependency_context(query, project_id, max_contexts)
        else:  # balanced
            return self._balanced_context(query, project_id, max_contexts)
    
    def _conversation_context(
        self,
        query: str,
        project_id: str,
        max_contexts: int,
        session_manager = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve context based on session history for conversation meta-queries.
        
        Args:
            query: The query to retrieve context for
            project_id: The project ID to filter by
            max_contexts: Maximum number of context fragments to return
            session_manager: Session manager instance to retrieve history
            
        Returns:
            List of context fragments based on session history
        """
        results = []
        
        # Verify session manager is provided
        if not session_manager:
            logger.warning("No session manager provided for conversation context strategy")
            return self._semantic_context(query, project_id, max_contexts)
        
        # Get active session
        active_session = session_manager.get_active_session()
        if not active_session:
            logger.warning("No active session found for conversation context strategy")
            return self._semantic_context(query, project_id, max_contexts)
        
        # Get session history
        history = session_manager.get_session_history(session_id=None, limit=20)  # Get recent history entries
        
        if not history:
            logger.warning("No session history found for conversation context strategy")
            return self._semantic_context(query, project_id, max_contexts)
        
        logger.info(f"Found {len(history)} session history entries for conversation context")
        
        # Convert history to context items
        score_base = 1.0
        for i, entry in enumerate(history):
            # Skip entries that don't have commands or are irrelevant
            if 'command' not in entry or entry.get('command') != 'generate':
                continue
            
            # Get prompt and result if available
            prompt = entry.get('args', {}).get('prompt', '')
            
            if not prompt:
                continue
            
            # Create a context item with decreasing scores for older items
            score = score_base - (i * 0.05)  # Decrease score for older items
            
            context_text = f"User asked: {prompt}\n\n"
            
            # Add result if available (might be in different formats)
            if 'result' in entry and entry['result'] == 'Success':
                # For successful commands, extract any useful information
                if 'args' in entry and 'output' in entry['args'] and entry['args']['output']:
                    output_file = entry['args']['output']
                    context_text += f"Output saved to file: {output_file}\n\n"
                else:
                    # Try to extract the generated code from command output
                    context_text += "Command executed successfully\n\n"
            
            context_item = {
                'text': context_text,
                'metadata': {
                    'type': 'conversation_history',
                    'timestamp': entry.get('timestamp', ''),
                    'command': entry.get('command', ''),
                    'project_id': project_id,
                    'name': 'Session History Item',
                    'filename': 'session_history.txt'
                },
                'score': max(0.5, score)  # Ensure score doesn't go below 0.5
            }
            
            results.append(context_item)
            logger.debug(f"Added history item to context: {prompt[:50]}...")
        
        # If we have few history items, supplement with semantic search
        if len(results) < max_contexts:
            semantic_results = self._semantic_context(
                query, 
                project_id, 
                max_contexts - len(results)
            )
            
            # Add semantic results with lower priority (lower scores)
            for result in semantic_results:
                if 'score' in result:
                    result['score'] = result['score'] * 0.2  # Significantly reduce importance of semantic results
                results.append(result)
        
        # Sort by score and limit to max_contexts
        results.sort(key=lambda x: x.get('score', 0), reverse=True)
        
        logger.info(f"Using {len(results[:max_contexts])} conversation context items for query")
        return results[:max_contexts]
    
    def _semantic_context(
        self,
        query: str,
        project_id: str,
        max_contexts: int
    ) -> List[Dict[str, Any]]:
        """
        Retrieve context based on semantic similarity.
        
        Args:
            query: The query to retrieve context for
            project_id: The project ID to filter by
            max_contexts: Maximum number of context fragments to return
            
        Returns:
            List of context fragments based on semantic similarity
        """
        # Use the RAG system's retrieve_relevant_code method
        results = self.rag.retrieve_relevant_code(
            query=query,
            project_id=project_id,
            top_k=max_contexts
        )
        
        logger.info(f"Using semantic context strategy for query with {len(results)} results")
        return results
    
    def _structural_context(
        self,
        query: str,
        project_id: str,
        max_contexts: int
    ) -> List[Dict[str, Any]]:
        """
        Retrieve context based on code structure relationships.
        
        Args:
            query: The query to retrieve context for
            project_id: The project ID to filter by
            max_contexts: Maximum number of context fragments to return
            
        Returns:
            List of context fragments based on structural relationships
        """
        # Extract code structures from the query
        structures = self._extract_code_structures(query)
        
        # Get baseline semantic results
        semantic_results = self._semantic_context(query, project_id, max_contexts * 2)
        
        # If no structures found, return semantic results
        if not structures['classes'] and not structures['functions'] and not structures['variables']:
            logger.info("No specific structures found in query, using semantic results")
            return semantic_results[:max_contexts]
        
        # Calculate structural weight for each result based on shared structures
        weighted_results = []
        for result in semantic_results:
            score = result.get('score', 0.5)
            
            # Extract structures from the result text
            try:
                result_structures = self._extract_code_structures(result['text'])
                
                # Calculate structure overlap
                class_overlap = len(set(structures['classes']).intersection(result_structures['classes']))
                function_overlap = len(set(structures['functions']).intersection(result_structures['functions']))
                variable_overlap = len(set(structures['variables']).intersection(result_structures['variables']))
                
                # Apply structural boost
                structure_boost = class_overlap * 0.2 + function_overlap * 0.15 + variable_overlap * 0.05
                adjusted_score = score * (1 + structure_boost)
                
                # Update the score
                result['score'] = min(1.0, adjusted_score)  # Cap at 1.0
                
                weighted_results.append(result)
            except Exception as e:
                logger.warning(f"Error analyzing structures in result: {e}")
                weighted_results.append(result)
        
        # Sort by adjusted score and limit to max_contexts
        weighted_results.sort(key=lambda x: x.get('score', 0), reverse=True)
        
        logger.info(f"Using structural context strategy with {len(weighted_results[:max_contexts])} results")
        return weighted_results[:max_contexts]
    
    def _dependency_context(
        self,
        query: str,
        project_id: str,
        max_contexts: int
    ) -> List[Dict[str, Any]]:
        """
        Retrieve context based on code dependencies.
        
        Args:
            query: The query to retrieve context for
            project_id: The project ID to filter by
            max_contexts: Maximum number of context fragments to return
            
        Returns:
            List of context fragments based on dependency relationships
        """
        # Get baseline structural results
        structural_results = self._structural_context(query, project_id, max_contexts)
        
        # Extract imports and dependencies from the query
        imports = self._extract_imports(query)
        
        # If no imports found, return structural results
        if not imports:
            logger.info("No specific imports found in query, using structural results")
            return structural_results
        
        # Get additional context for dependencies (import statements, etc.)
        dependency_query = " ".join(imports)
        
        # Only fetch dependency context if we have a meaningful query
        dependency_results = []
        if dependency_query:
            try:
                dependency_results = self.rag.retrieve_relevant_code(
                    query=dependency_query,
                    project_id=project_id,
                    top_k=max_contexts // 2
                )
            except Exception as e:
                logger.warning(f"Error fetching dependency context: {e}")
        
        # Combine results, prioritizing structural results
        combined_results = []
        
        # Add structural results
        for result in structural_results[:max_contexts - len(dependency_results)]:
            combined_results.append(result)
        
        # Add dependency results not already in the list
        existing_ids = {r.get('id', i) for i, r in enumerate(combined_results)}
        for result in dependency_results:
            result_id = result.get('id', None)
            if result_id not in existing_ids:
                combined_results.append(result)
                if len(combined_results) >= max_contexts:
                    break
        
        logger.info(f"Using dependency context strategy with {len(combined_results)} results")
        return combined_results
    
    def _balanced_context(
        self,
        query: str,
        project_id: str,
        max_contexts: int
    ) -> List[Dict[str, Any]]:
        """
        Retrieve context using a balanced approach of semantic, structural, and dependency strategies.
        
        Args:
            query: The query to retrieve context for
            project_id: The project ID to filter by
            max_contexts: Maximum number of context fragments to return
            
        Returns:
            List of context fragments from balanced selection
        """
        # Allocate context slots for each strategy
        semantic_slots = max_contexts // 3
        structural_slots = max_contexts // 3
        dependency_slots = max_contexts - semantic_slots - structural_slots
        
        # Get context from each strategy
        semantic_results = self._semantic_context(query, project_id, semantic_slots)
        structural_results = self._structural_context(query, project_id, structural_slots * 2)
        dependency_results = self._dependency_context(query, project_id, dependency_slots * 2)
        
        # Filter structural and dependency results to avoid duplicates with semantic results
        semantic_ids = {r.get('id', i) for i, r in enumerate(semantic_results)}
        
        filtered_structural = []
        for result in structural_results:
            result_id = result.get('id', None)
            if result_id not in semantic_ids:
                filtered_structural.append(result)
                if len(filtered_structural) >= structural_slots:
                    break
        
        # Combine semantic and filtered structural results
        combined_ids = semantic_ids.union({r.get('id', i+1000) for i, r in enumerate(filtered_structural)})
        
        filtered_dependency = []
        for result in dependency_results:
            result_id = result.get('id', None)
            if result_id not in combined_ids:
                filtered_dependency.append(result)
                if len(filtered_dependency) >= dependency_slots:
                    break
        
        # Combine all results
        combined_results = semantic_results + filtered_structural + filtered_dependency
        
        # Sort by score
        combined_results.sort(key=lambda x: x.get('score', 0), reverse=True)
        
        logger.info(f"Using balanced context strategy with {len(combined_results)} results")
        return combined_results[:max_contexts]
    
    def _extract_code_structures(self, text: str) -> Dict[str, List[str]]:
        """
        Extract code structures (classes, functions, variables) from text.
        
        Args:
            text: The text to extract structures from
            
        Returns:
            Dictionary with lists of classes, functions, and variables
        """
        structures = {
            'classes': [],
            'functions': [],
            'variables': []
        }
        
        # Simple regex-based extraction for basic cases
        import re
        
        # Extract classes
        class_pattern = r'class\s+([A-Za-z_][A-Za-z0-9_]*)'
        class_matches = re.findall(class_pattern, text)
        structures['classes'] = list(set(class_matches))
        
        # Extract functions
        function_pattern = r'def\s+([A-Za-z_][A-Za-z0-9_]*)'
        function_matches = re.findall(function_pattern, text)
        structures['functions'] = list(set(function_matches))
        
        # Extract variables (simple cases only)
        variable_pattern = r'([A-Za-z_][A-Za-z0-9_]*)\s*='
        variable_matches = re.findall(variable_pattern, text)
        
        # Filter out common keywords
        keywords = {'True', 'False', 'None', 'if', 'else', 'elif', 'for', 'while', 'class', 'def'}
        variables = [v for v in variable_matches if v not in keywords]
        structures['variables'] = list(set(variables))
        
        # Try to use ast for more accurate extraction if possible
        try:
            import ast
            
            tree = ast.parse(text)
            
            # Reset lists to use ast results instead
            structures['classes'] = []
            structures['functions'] = []
            structures['variables'] = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    structures['classes'].append(node.name)
                elif isinstance(node, ast.FunctionDef):
                    structures['functions'].append(node.name)
                elif isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            structures['variables'].append(target.id)
        except Exception as e:
            logger.warning(f"Failed to parse code: {e}")
            # Fall back to regex results
        
        return structures
    
    def _extract_imports(self, text: str) -> List[str]:
        """
        Extract import statements and module names from text.
        
        Args:
            text: The text to extract imports from
            
        Returns:
            List of import statements and module names
        """
        imports = []
        
        # Simple regex-based extraction
        import re
        
        # Extract import statements
        import_pattern = r'(?:from|import)\s+([A-Za-z0-9_.]+)'
        import_matches = re.findall(import_pattern, text)
        imports = list(set(import_matches))
        
        # Try to use ast for more accurate extraction if possible
        try:
            import ast
            
            tree = ast.parse(text)
            
            # Reset list to use ast results instead
            imports = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for name in node.names:
                        imports.append(name.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.append(node.module)
        except Exception as e:
            logger.warning(f"Failed to parse code for imports: {e}")
            # Fall back to regex results
        
        return imports
    
    def analyze_query_complexity(self, query: str) -> Dict[str, Any]:
        """
        Analyze the complexity of a query to determine the optimal context strategy.
        
        Args:
            query: The query to analyze
            
        Returns:
            Dictionary with analysis results
        """
        # Extract code structures
        structures = self._extract_code_structures(query)
        
        # Calculate complexity metrics
        word_count = len(query.split())
        structure_count = (
            0 if not structures else
            len(structures['classes']) + 
            len(structures['functions']) + 
            len(structures['variables'])
        )
        
        # Determine optimal strategy based on complexity
        if structure_count > 5:
            optimal_strategy = "structural"
        elif word_count > 50:
            optimal_strategy = "balanced"
        elif "import" in query.lower() or "from" in query.lower():
            optimal_strategy = "dependency"
        else:
            optimal_strategy = "semantic"
        
        return {
            "word_count": word_count,
            "structure_count": structure_count,
            "structures": structures,
            "optimal_strategy": optimal_strategy
        }


# Add these lines at the end of the file for testing
if __name__ == "__main__":
    # Test the LLM classification
    from pprint import pprint
    
    # Create a simple mock RAG system for testing
    class MockRAG:
        pass
    
    rag = MockRAG()
    selector = ContextSelector(rag)
    
    # Test various queries
    test_queries = [
        "Can you summarize our conversation?",
        "What have we talked about so far?",
        "Write a function to add two numbers",
        "How do I implement a binary search tree?",
        "Let's review what we've discussed",
        "Generate a Python class for data processing"
    ]
    
    for query in test_queries:
        result = selector.is_conversation_meta_query(query)
        print(f"Query: '{query}' -> {'CONVERSATION' if result else 'CODE'}")
