#!/usr/bin/env python3
"""
Context Selector for AI Development Agent

This module provides advanced context selection strategies for code generation,
considering code structure, dependencies, and relevance to the current task.
"""

import os
import sys
import ast
import logging
from typing import List, Dict, Any, Optional, Tuple, Set
import numpy as np

# Import project modules
from code_rag import CodeRAG

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("context_selector")

class ContextSelector:
    """Advanced context selection for code generation."""
    
    def __init__(self, rag_system: CodeRAG):
        """
        Initialize the context selector.
        
        Args:
            rag_system: The RAG system to use for retrieving context
        """
        self.rag = rag_system
        
    def select_context(
        self,
        query: str,
        project_id: str,
        max_contexts: int = 5,
        context_strategy: str = "balanced"
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
                
        Returns:
            List of context fragments
        """
        if context_strategy == "semantic":
            return self._semantic_context(query, project_id, max_contexts)
        elif context_strategy == "structural":
            return self._structural_context(query, project_id, max_contexts)
        elif context_strategy == "dependency":
            return self._dependency_context(query, project_id, max_contexts)
        else:  # balanced
            return self._balanced_context(query, project_id, max_contexts)
            
    def _semantic_context(
        self,
        query: str,
        project_id: str,
        max_contexts: int
    ) -> List[Dict[str, Any]]:
        """Retrieve context based on semantic similarity only."""
        return self.rag.retrieve_relevant_code(
            query=query,
            project_id=project_id,
            top_k=max_contexts
        )
        
    def _structural_context(
        self,
        query: str,
        project_id: str,
        max_contexts: int
    ) -> List[Dict[str, Any]]:
        """
        Retrieve context prioritizing structural relationships.
        Analyzes the query to identify code structures and retrieves
        related classes, functions, etc.
        """
        # First get basic semantic results
        semantic_results = self.rag.retrieve_relevant_code(
            query=query,
            project_id=project_id,
            top_k=max_contexts * 2  # Get more results to filter
        )
        
        if not semantic_results:
            return []
        
        # Extract code structures mentioned in the query
        structures = self._extract_code_structures(query)
        
        # Score results based on structural relevance
        scored_results = []
        for result in semantic_results:
            base_score = result.get('score', 0.0)
            
            # Parse code to find structures
            code_structures = self._extract_code_structures_from_code(result['text'])
            
            # Calculate structural similarity
            structural_score = self._calculate_structural_similarity(
                structures, code_structures
            )
            
            # Combine scores
            final_score = base_score * 0.7 + structural_score * 0.3
            
            scored_results.append({
                **result,
                'score': final_score,
                '_structural_score': structural_score
            })
        
        # Sort by final score and return top results
        scored_results.sort(key=lambda x: x['score'], reverse=True)
        return scored_results[:max_contexts]
    
    def _dependency_context(
        self,
        query: str,
        project_id: str,
        max_contexts: int
    ) -> List[Dict[str, Any]]:
        """
        Retrieve context prioritizing code with dependencies.
        First finds the most relevant code, then adds its dependencies.
        """
        # First get basic semantic results
        semantic_results = self.rag.retrieve_relevant_code(
            query=query,
            project_id=project_id,
            top_k=max(2, max_contexts // 2)  # Fewer direct matches
        )
        
        if not semantic_results:
            return []
        
        # Find dependencies of the retrieved code
        dependencies = self._find_dependencies(semantic_results)
        
        # Remove duplicates while preserving order
        result_set = {r['text']: r for r in semantic_results}
        for dep in dependencies:
            if dep['text'] not in result_set:
                result_set[dep['text']] = dep
        
        # Convert back to list and limit to max_contexts
        results = list(result_set.values())
        return results[:max_contexts]
    
    def _balanced_context(
        self,
        query: str,
        project_id: str,
        max_contexts: int
    ) -> List[Dict[str, Any]]:
        """
        Balanced approach combining semantic, structural and dependency contexts.
        Allocates portions of the max_contexts to each strategy.
        """
        # Allocate context slots
        semantic_count = max(1, max_contexts // 3)
        structural_count = max(1, max_contexts // 3)
        dependency_count = max_contexts - semantic_count - structural_count
        
        # Get contexts from each strategy
        semantic_results = self._semantic_context(query, project_id, semantic_count)
        structural_results = self._structural_context(query, project_id, structural_count)
        dependency_results = self._dependency_context(query, project_id, dependency_count)
        
        # Combine results, removing duplicates
        result_set = {}
        for result in semantic_results + structural_results + dependency_results:
            if result['text'] not in result_set:
                result_set[result['text']] = result
        
        # Convert back to list and limit to max_contexts
        results = list(result_set.values())
        return results[:max_contexts]
    
    def _extract_code_structures(self, text: str) -> Dict[str, List[str]]:
        """
        Extract code structures mentioned in text.
        
        Returns:
            Dictionary with keys 'classes', 'functions', 'variables'
        """
        structures = {
            'classes': [],
            'functions': [],
            'variables': []
        }
        
        # Simple extraction based on keywords and patterns
        # Class detection (UpperCamelCase)
        import re
        class_pattern = r'\b([A-Z][a-zA-Z0-9]*)\b'
        classes = re.findall(class_pattern, text)
        structures['classes'] = [c for c in classes if len(c) > 1]
        
        # Function detection (lowercase_with_underscores or camelCase)
        function_pattern = r'\b([a-z][a-z0-9_]*(_[a-z0-9_]+)+)\b|\b([a-z][a-zA-Z0-9]*[A-Z][a-zA-Z0-9]*)\b'
        functions = re.findall(function_pattern, text)
        # Flatten and clean function matches
        flat_functions = []
        for f_tuple in functions:
            for f in f_tuple:
                if f and len(f) > 2:
                    flat_functions.append(f)
        structures['functions'] = flat_functions
        
        # Variable detection (similar to functions but filtering out common words)
        variable_pattern = r'\b([a-z][a-z0-9_]*)\b'
        variables = re.findall(variable_pattern, text)
        common_words = {'the', 'and', 'for', 'with', 'this', 'that', 'from', 'have', 'has'}
        structures['variables'] = [v for v in variables if len(v) > 1 and v not in common_words]
        
        return structures
    
    def _extract_code_structures_from_code(self, code: str) -> Dict[str, List[str]]:
        """
        Extract code structures from Python code.
        
        Returns:
            Dictionary with keys 'classes', 'functions', 'variables'
        """
        structures = {
            'classes': [],
            'functions': [],
            'variables': []
        }
        
        try:
            tree = ast.parse(code)
            
            # Extract classes
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    structures['classes'].append(node.name)
                elif isinstance(node, ast.FunctionDef):
                    structures['functions'].append(node.name)
                elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
                    structures['variables'].append(node.id)
        except Exception as e:
            logger.warning(f"Failed to parse code: {e}")
        
        return structures
    
    def _calculate_structural_similarity(
        self,
        query_structures: Dict[str, List[str]],
        code_structures: Dict[str, List[str]]
    ) -> float:
        """
        Calculate structural similarity between query and code.
        
        Returns:
            Similarity score (0.0 to 1.0)
        """
        if not query_structures or not code_structures:
            return 0.0
        
        matches = 0
        total = 0
        
        # Count matches for each structure type
        for structure_type in ['classes', 'functions', 'variables']:
            query_items = set(query_structures[structure_type])
            code_items = set(code_structures[structure_type])
            
            # Count matches
            common_items = query_items.intersection(code_items)
            matches += len(common_items)
            
            # Count total items in query
            total += len(query_items)
        
        # Avoid division by zero
        if total == 0:
            return 0.0
        
        return matches / total
    
    def _find_dependencies(
        self, 
        code_fragments: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Find dependencies of the given code fragments.
        
        Args:
            code_fragments: List of code fragments to find dependencies for
            
        Returns:
            List of dependent code fragments
        """
        dependencies = []
        
        # Extract structures from all fragments
        fragment_structures = []
        for fragment in code_fragments:
            structures = self._extract_code_structures_from_code(fragment['text'])
            fragment_structures.append(structures)
        
        # Collect all defined names
        all_defined_names = set()
        for structures in fragment_structures:
            all_defined_names.update(structures['classes'])
            all_defined_names.update(structures['functions'])
        
        # For each fragment, find imports and references to extract dependencies
        for fragment in code_fragments:
            # Extract imports and references
            imports, references = self._extract_imports_and_references(fragment['text'])
            
            # Look for dependencies based on imports
            for imp in imports:
                # Search for code defining this import
                if fragment.get('metadata', {}).get('project_id'):
                    project_id = fragment['metadata']['project_id']
                    dep_results = self.rag.retrieve_relevant_code(
                        query=f"module {imp}",
                        project_id=project_id,
                        top_k=2
                    )
                    dependencies.extend(dep_results)
            
            # Look for dependencies based on references
            for ref in references:
                if ref in all_defined_names:
                    continue  # Skip if already defined in our fragments
                
                # Search for code defining this reference
                if fragment.get('metadata', {}).get('project_id'):
                    project_id = fragment['metadata']['project_id']
                    dep_results = self.rag.retrieve_relevant_code(
                        query=f"class {ref} OR function {ref}",
                        project_id=project_id,
                        top_k=2
                    )
                    dependencies.extend(dep_results)
        
        return dependencies
    
    def _extract_imports_and_references(self, code: str) -> Tuple[Set[str], Set[str]]:
        """
        Extract imports and references from Python code.
        
        Returns:
            Tuple of (imports, references)
        """
        imports = set()
        references = set()
        
        try:
            tree = ast.parse(code)
            
            # Extract imports
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for name in node.names:
                        imports.add(name.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.add(node.module)
                
                # Extract references
                elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                    references.add(node.id)
                elif isinstance(node, ast.Attribute) and isinstance(node.ctx, ast.Load):
                    if isinstance(node.value, ast.Name):
                        references.add(f"{node.value.id}.{node.attr}")
        except Exception as e:
            logger.warning(f"Failed to parse code for imports: {e}")
        
        return imports, references
    
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

if __name__ == "__main__":
    """CLI interface for context selection testing."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test context selection strategies")
    parser.add_argument("--query", required=True, help="Query to test")
    parser.add_argument("--project-id", required=True, help="Project ID to filter by")
    parser.add_argument(
        "--strategy", 
        choices=["semantic", "structural", "dependency", "balanced", "auto"],
        default="auto",
        help="Context strategy to use (default: auto)"
    )
    parser.add_argument(
        "--max-contexts", 
        type=int,
        default=5,
        help="Maximum number of context fragments (default: 5)"
    )
    
    args = parser.parse_args()
    
    # Initialize RAG system
    from code_rag import CodeRAG
    rag = CodeRAG()
    
    # Initialize context selector
    context_selector = ContextSelector(rag)
    
    # Determine strategy
    strategy = args.strategy
    if strategy == "auto":
        analysis = context_selector.analyze_query_complexity(args.query)
        strategy = analysis["optimal_strategy"]
        print(f"Auto-selected strategy: {strategy}")
        print(f"Query analysis: {analysis}")
    
    # Select context
    context = context_selector.select_context(
        query=args.query,
        project_id=args.project_id,
        max_contexts=args.max_contexts,
        context_strategy=strategy
    )
    
    # Print results
    print(f"\nRetrieved {len(context)} context fragments using {strategy} strategy:")
    for i, fragment in enumerate(context):
        score_display = f"{fragment.get('score', 0.0):.4f}" if fragment.get('score') is not None else "N/A"
        print(f"\nContext {i+1} (Score: {score_display}):")
        print(f"Filename: {fragment['metadata'].get('filename', 'unknown')}")
        print(f"Type: {fragment['metadata'].get('type', 'unknown')}")
        print(f"Name: {fragment['metadata'].get('name', 'unknown')}")
        print("First 200 chars:")
        print(fragment['text'][:200] + "..." if len(fragment['text']) > 200 else fragment['text'])
