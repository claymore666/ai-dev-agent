# Changelog

All notable changes to the Context-Extended AI Software Development Agent POC will be documented in this file.
## [0.2.2] - Unreleased

### Added
- Enhanced Context Selection system with multiple selection strategies:
  - Semantic: Pure semantic similarity-based selection
  - Structural: Code structure-aware selection prioritizing classes, functions, and variables
  - Dependency: Dependency-aware selection that includes imports and references
  - Balanced: Combined approach using all strategies
  - Auto: Intelligent strategy selection based on query analysis
- Context Analyzer for understanding code structures and dependencies
- Query complexity analysis to automatically determine optimal context strategy
- New `analyze` command for examining queries and recommending strategies
- Context strategy options for code generation and search commands
- Tracking of context strategies used in project metadata

### Changed
- Improved code generation quality through better context selection
- Enhanced search results with structure-aware ranking
- Updated CLI with additional context selection options
- Refined integration between CLI and RAG components

### Fixed
- More accurate context retrieval for complex queries
- Better handling of code dependencies during context selection
- Improved relevance of search results for code-specific terminology

## [0.2.1] - 2025-03-13

### Added
- Unified Command Line Interface (CLI) with comprehensive command set
- Project Configuration System for persistent project management
- YAML-based project storage with metadata tracking
- File tracking capabilities within projects
- Project export/import functionality
- Integration of project metadata with code generation
- Code generation history tracking
- Comprehensive test scripts for CLI and Project functionality

### Changed
- Enhanced error handling and user feedback in all components
- Improved integration between vector database and project tracking
- Updated documentation with examples of all new functionality
- Refactored code for better modularity and extensibility

### Fixed
- Package detection in status command now correctly identifies all installed components
- More robust metadata handling for code fragments
- Better validation of project IDs and file paths

## [0.2.0] - 2025-03-12

### Added
- Qdrant vector database for code context storage
- Python helper library for Qdrant management (qdrant_helper.py)
- Sentence Transformers integration for code embedding
- RAG Framework using LlamaIndex and LiteLLM
- Testing scripts for Qdrant, embedding, and RAG functionality
- Context-aware code generation capabilities
- Support for handling complex code fragments
- Test examples for data loading, processing, and model training

### Changed
- Updated Docker Compose configuration to include Qdrant
- Expanded directory structure for Phase 2 components
- Enhanced documentation for vector database usage
- Improved error handling and fallback mechanisms in API calls

### Fixed
- Compatibility issues with different embedding models
- Model name handling for Ollama integration
- API communication with LiteLLM

## [0.1.1] - 2025-03-12

### Added
- Redis caching for LiteLLM responses
- Test script (`test_cache.sh`) to verify caching functionality
- Redis monitoring script (`monitor_redis.sh`) for real-time cache statistics
- Documentation for Redis caching implementation and usage

### Changed
- Updated `litellm_config.yaml` to enable Redis caching
- Updated `litellm_simple_config.yaml` to enable Redis caching
- Improved error handling in test scripts

### Fixed
- Redis container connectivity with LiteLLM service

## [0.1.0] - Initial Release

### Added
- Docker Compose configuration with core services
- LiteLLM integration with Ollama service
- Nginx proxy configuration
- Ollama WebUI for interaction
- Basic test scripts for service validation
- Installation and setup scripts
