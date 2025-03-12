#!/bin/bash

# Script to monitor Redis cache usage and statistics

echo "Monitoring Redis cache for LiteLLM"
echo "Press Ctrl+C to exit"
echo ""

# Function to display Redis info
show_redis_info() {
    echo "===== Redis Statistics at $(date) ====="
    
    # Check if Redis container is running
    if ! docker ps | grep -q redis; then
        echo "Redis container is not running!"
        return 1
    fi
    
    # Get memory usage
    used_memory=$(docker exec redis redis-cli INFO | grep used_memory_human | cut -d':' -f2 | tr -d '\r')
    echo "Memory usage: $used_memory"
    
    # Get key count
    key_count=$(docker exec redis redis-cli DBSIZE)
    echo "Total keys: $key_count"
    
    # Get hit/miss ratio
    hits=$(docker exec redis redis-cli INFO | grep keyspace_hits | cut -d':' -f2 | tr -d '\r')
    misses=$(docker exec redis redis-cli INFO | grep keyspace_misses | cut -d':' -f2 | tr -d '\r')
    
    if [ "$hits" != "" ] && [ "$misses" != "" ]; then
        total=$((hits + misses))
        if [ "$total" -gt 0 ]; then
            hit_ratio=$(echo "scale=2; ($hits * 100) / $total" | bc)
            echo "Cache hit ratio: $hit_ratio% ($hits hits, $misses misses)"
        else
            echo "No cache activity yet"
        fi
    fi
    
    # Sample some keys (if any exist)
    if [ "$key_count" -gt 0 ]; then
        echo ""
        echo "Sample keys (up to 5):"
        docker exec redis redis-cli --raw KEYS "*" | head -5
        
        # Get TTL of a sample key
        sample_key=$(docker exec redis redis-cli --raw KEYS "*" | head -1)
        if [ ! -z "$sample_key" ]; then
            ttl=$(docker exec redis redis-cli TTL "$sample_key")
            echo ""
            echo "TTL of sample key '$sample_key': $ttl seconds"
        fi
    fi
    
    echo "========================================"
    echo ""
}

# Monitor loop
while true; do
    show_redis_info
    sleep 10
done
