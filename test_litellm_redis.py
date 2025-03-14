#!/usr/bin/env python3
"""
Test script to verify the Redis caching for LiteLLM is working.
"""

import os
import sys
import time
import redis

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Redis configuration
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")
REDIS_DB = int(os.getenv("REDIS_DB", "0"))

try:
    from litellm_utils.redis_cache import RedisModelInfoCache
    from code_rag import CodeRAG
except ImportError as e:
    print(f"Error importing modules: {e}")
    sys.exit(1)

def check_redis_connection():
    """Check if Redis is accessible."""
    try:
        r = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            password=REDIS_PASSWORD if REDIS_PASSWORD else None,
            db=REDIS_DB,
            socket_timeout=5
        )
        
        # Test connection
        r.ping()
        print(f"✅ Connected to Redis at {REDIS_HOST}:{REDIS_PORT}")
        return True
    except Exception as e:
        print(f"❌ Failed to connect to Redis: {e}")
        return False

def check_redis_cache():
    """Check if the Redis cache has been created and populated."""
    cache = RedisModelInfoCache()
    models = cache.get_all_models()
    
    print(f"\nFound {len(models)} models in Redis cache:")
    for model_name, info in models.items():
        print(f"  - {model_name}: max_tokens={info['max_tokens']}")
    
    return len(models) > 0

def test_code_rag_initialization():
    """Test CodeRAG initialization time with Redis cache."""
    print("\nTesting CodeRAG initialization time (should be faster now)...")
    
    # First initialization might still be slow due to model loading
    start_time = time.time()
    rag = CodeRAG()
    end_time = time.time()
    first_init_time = end_time - start_time
    
    print(f"First initialization time: {first_init_time:.4f} seconds")
    
    # Second initialization should be much faster due to Redis cache
    start_time = time.time()
    rag = CodeRAG()
    end_time = time.time()
    second_init_time = end_time - start_time
    
    print(f"Second initialization time: {second_init_time:.4f} seconds")
    
    return second_init_time < first_init_time or second_init_time < 0.5

def check_redis_keys():
    """Check Redis keys related to LiteLLM caching."""
    try:
        r = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            password=REDIS_PASSWORD if REDIS_PASSWORD else None,
            db=REDIS_DB,
            socket_timeout=5
        )
        
        # Get all keys matching litellm:*
        keys = r.keys("litellm:*")
        
        # Convert bytes to strings
        keys = [key.decode('utf-8') if isinstance(key, bytes) else key for key in keys]
        
        print(f"\nFound {len(keys)} LiteLLM-related keys in Redis:")
        for key in keys:
            key_type = r.type(key).decode('utf-8')
            
            if key_type == "hash":
                size = r.hlen(key)
                print(f"  - {key}: {key_type} with {size} fields")
            elif key_type == "set":
                size = r.scard(key)
                print(f"  - {key}: {key_type} with {size} members")
            else:
                print(f"  - {key}: {key_type}")
        
        return True
    except Exception as e:
        print(f"Error checking Redis keys: {e}")
        return False

def main():
    """Main test function."""
    print("Testing Redis caching for LiteLLM...")
    
    # Test 1: Check Redis connection
    if not check_redis_connection():
        print("❌ Cannot connect to Redis.")
        return False
    
    # Test 2: Check Redis cache
    if check_redis_cache():
        print("✅ Redis cache is properly set up")
    else:
        print("❌ Redis cache setup failed")
        return False
    
    # Test 3: Examine Redis keys
    check_redis_keys()
    
    # Test 4: CodeRAG initialization time
    if test_code_rag_initialization():
        print("✅ CodeRAG initialization is faster with Redis cache")
    else:
        print("❌ CodeRAG initialization is not showing expected improvement")
        return False
    
    print("\nAll tests passed! The Redis caching for LiteLLM is working correctly.")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
