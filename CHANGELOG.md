# Changelog

## v0.1.0 - Initial Release (2025-03-12)

### Added
- Core docker-compose infrastructure with all essential services
- LiteLLM integration with Ollama models
- Ollama WebUI for interactive chat with models
- Nginx proxy with path mapping to connect WebUI to Ollama API
- Redis service included but caching currently disabled
- Optional Portainer installation script
- Comprehensive test and troubleshooting scripts
- Updated documentation with architecture details and usage instructions

### Working Features
- Ollama WebUI chat functionality
- Model switching and parameter configuration
- LiteLLM API for programmatic access to models
- Docker environment with resource constraints (4GB RAM, 32GB disk)
- Nginx proxy with proper path mapping between WebUI and Ollama API

### Known Issues
- File upload functionality returns 500 error
- Microphone access (speech-to-text) not working correctly
- Redis caching currently disabled in LiteLLM configuration

### Coming in Future Releases
- Enable Redis caching for LiteLLM responses
- Fix file upload and microphone functionality
- Vector database integration (Chroma DB or Qdrant)
- Text embedding service for document indexing
- Retrieval-augmented generation (RAG) implementation
- Code parsing and analysis system
- Task planning and execution framework
- CLI tool for context-aware operations
