#!/usr/bin/env python3
"""
Performance test script for the AI Development Agent.
This script performs basic performance benchmarks for core components.
"""

import os
import sys
import time
import logging
import json
from typing import Dict, List, Any, Optional
import statistics

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("performance_tests")

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import project modules
try:
    from code_rag import CodeRAG
    from context_selector import ContextSelector
    from project_manager import ProjectManager
    from session_manager import SessionManager
except ImportError as e:
    logger.error(f"Failed to import required modules: {e}")
    logger.error("Please ensure you're running this script from the project directory.")
    sys.exit(1)

class PerformanceTester:
    """Performance tester for the AI Development Agent components."""
    
    def __init__(self, results_file: str = "reports/performance_results.json"):
        """
        Initialize the performance tester.
        
        Args:
            results_file: Path to save the results
        """
        self.results_file = results_file
        self.results = {
            "timestamp": time.time(),
            "tests": {}
        }
        
        # Create reports directory if it doesn't exist
        os.makedirs(os.path.dirname(results_file), exist_ok=True)
        
        # Initialize components
        logger.info("Initializing components for performance testing...")
        try:
            self.project_manager = ProjectManager()
            self.session_manager = SessionManager()
            self.code_rag = CodeRAG(session_manager=self.session_manager)
            
            # Get ContextSelector from CodeRAG (if available)
            if hasattr(self.code_rag, '_context_selector'):
                self.context_selector = self.code_rag._context_selector
            else:
                self.context_selector = ContextSelector(self.code_rag)
                
            logger.info("Components initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize components: {e}")
            raise
    
    def run_all_tests(self) -> Dict[str, Any]:
        """
        Run all performance tests.
        
        Returns:
            Dictionary with test results
        """
        logger.info("Running all performance tests...")
        
        # Basic tests
        self._run_test("project_creation", self.test_project_creation)
        self._run_test("session_creation", self.test_session_creation)
        self._run_test("context_selection", self.test_context_selection)
        self._run_test("query_analysis", self.test_query_analysis)
        
        # Save results
        self._save_results()
        
        return self.results
    
    def _run_test(self, test_name: str, test_func, iterations: int = 5) -> None:
        """
        Run a specific test multiple times and record results.
        
        Args:
            test_name: Name of the test
            test_func: Test function to run
            iterations: Number of iterations
        """
        logger.info(f"Running test: {test_name} ({iterations} iterations)")
        durations = []
        
        for i in range(iterations):
            start_time = time.time()
            result = test_func()
            end_time = time.time()
            duration = end_time - start_time
            durations.append(duration)
            logger.info(f"  Iteration {i+1}/{iterations}: {duration:.4f}s")
        
        # Calculate statistics
        self.results["tests"][test_name] = {
            "min": min(durations),
            "max": max(durations),
            "mean": statistics.mean(durations),
            "median": statistics.median(durations),
            "std_dev": statistics.stdev(durations) if len(durations) > 1 else 0,
            "iterations": iterations,
            "durations": durations,
        }
        
        # Log summary
        logger.info(f"Test completed: {test_name}")
        logger.info(f"  Mean: {self.results['tests'][test_name]['mean']:.4f}s")
        logger.info(f"  Median: {self.results['tests'][test_name]['median']:.4f}s")
        logger.info(f"  Min: {self.results['tests'][test_name]['min']:.4f}s")
        logger.info(f"  Max: {self.results['tests'][test_name]['max']:.4f}s")
    
    def _save_results(self) -> None:
        """Save test results to a file."""
        try:
            with open(self.results_file, 'w') as f:
                json.dump(self.results, f, indent=2)
            logger.info(f"Results saved to {self.results_file}")
        except Exception as e:
            logger.error(f"Failed to save results: {e}")
    
    def test_project_creation(self) -> Dict[str, Any]:
        """
        Test project creation performance.
        
        Returns:
            Dictionary with test data
        """
        # Create a unique project name
        project_name = f"performance-test-{int(time.time())}"
        
        # Create project
        project = self.project_manager.create_project(
            name=project_name,
            description="Performance test project",
            tags=["performance", "test"]
        )
        
        # Clean up - delete the project
        self.project_manager.delete_project(project["id"])
        
        return {
            "project_id": project["id"],
            "project_name": project_name
        }
    
    def test_session_creation(self) -> Dict[str, Any]:
        """
        Test session creation performance.
        
        Returns:
            Dictionary with test data
        """
        # Create a session
        session_name = f"performance-test-{int(time.time())}"
        
        # Create session
        session = self.session_manager.create_session(
            name=session_name,
            description="Performance test session"
        )
        
        # Close and delete the session
        self.session_manager.close_session()
        
        return {
            "session_id": session["id"],
            "session_name": session_name
        }
    
    def test_context_selection(self) -> Dict[str, Any]:
        """
        Test context selection performance.
        
        Returns:
            Dictionary with test data
        """
        query = "Implement a data processing pipeline with efficient error handling"
        
        # Test each strategy
        strategies = ["semantic", "structural", "dependency", "balanced", "auto"]
        results = {}
        
        for strategy in strategies:
            start_time = time.time()
            contexts = self.context_selector.select_context(
                query=query,
                project_id=None,
                max_contexts=5,
                context_strategy=strategy
            )
            end_time = time.time()
            
            results[strategy] = {
                "duration": end_time - start_time,
                "context_count": len(contexts)
            }
        
        return results
    
    def test_query_analysis(self) -> Dict[str, Any]:
        """
        Test query analysis performance.
        
        Returns:
            Dictionary with test data
        """
        queries = [
            "Write a simple hello world function",
            "Create a class for data processing with error handling",
            "Implement a binary search tree with insert, delete, and search methods",
            "Write a web server using Flask that connects to a database",
            "Create a multithreaded application for processing large files"
        ]
        
        results = {}
        
        for query in queries:
            start_time = time.time()
            analysis = self.context_selector.analyze_query_complexity(query)
            end_time = time.time()
            
            results[query] = {
                "duration": end_time - start_time,
                "optimal_strategy": analysis["optimal_strategy"],
                "structure_count": analysis["structure_count"]
            }
        
        return results


if __name__ == "__main__":
    """Main entry point for performance testing."""
    logger.info("Starting performance tests...")
    
    try:
        # Run performance tests
        tester = PerformanceTester()
        results = tester.run_all_tests()
        
        # Print summary
        print("\nPerformance Test Summary:")
        print("------------------------")
        for test_name, test_results in results["tests"].items():
            print(f"{test_name}:")
            print(f"  Mean: {test_results['mean']:.4f}s")
            print(f"  Median: {test_results['median']:.4f}s")
            print(f"  Min: {test_results['min']:.4f}s")
            print(f"  Max: {test_results['max']:.4f}s")
        
        print(f"\nDetailed results saved to: {tester.results_file}")
        
        logger.info("Performance tests completed successfully")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Performance tests failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
