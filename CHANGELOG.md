# Changelog

All notable changes to the Context-Extended AI Software Development Agent POC will be documented in this file.

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
