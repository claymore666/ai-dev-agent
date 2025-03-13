#!/bin/bash
# Script to reset all databases (SQLite and Qdrant vector database)
# This will clear all saved data, use with caution!

echo "========================================"
echo "WARNING: This will reset ALL databases!"
echo "This includes:"
echo "  - Project database (SQLite)"
echo "  - Session database (SQLite)"
echo "  - Vector database (Qdrant)"
echo "========================================"
echo "All existing data will be lost!"
echo -n "Are you sure you want to continue? (y/N): "
read confirmation

if [[ ! "$confirmation" =~ ^[Yy]$ ]]; then
    echo "Operation cancelled."
    exit 0
fi

echo -e "\nResetting databases...\n"

# 1. Clean project database
echo "Resetting project database (SQLite)..."
sqlite3 ~/.devagent/devagent.db << 'EOF'
DELETE FROM projects;
DELETE FROM project_tags;
DELETE FROM project_files;
VACUUM;
EOF
echo "✅ Project database reset"

# 2. Clean sessions database
echo "Resetting session database (SQLite)..."
sqlite3 ~/.devagent/sessions.db << 'EOF'
DELETE FROM sessions;
DELETE FROM active_session;
VACUUM;
EOF
echo "✅ Session database reset"

# 3. Clear Qdrant vector database
echo "Resetting vector database (Qdrant)..."

# Check if Qdrant is running
if ! curl -s http://localhost:6333/readyz > /dev/null; then
    echo "❌ Qdrant is not running. Unable to reset vector database."
    echo "Please start Qdrant service first or manually delete the data/qdrant directory."
else
    # Check if code_fragments collection exists
    code_fragments_exists=$(curl -s "http://localhost:6333/collections/code_fragments/exists" | grep -c "true")
    
    if [ "$code_fragments_exists" -eq 1 ]; then
        echo "Found existing code_fragments collection"
        
        # Delete all points in the collection instead of recreating it
        echo "Removing all vectors from code_fragments collection..."
        delete_response=$(curl -s -X POST -H "Content-Type: application/json" -d '{
            "filter": {}
        }' "http://localhost:6333/collections/code_fragments/points/delete")
        
        if echo "$delete_response" | grep -q "result.*true"; then
            echo "✅ All vectors deleted from code_fragments collection"
        else
            echo "⚠️ Attempted to delete vectors but got unexpected response"
            echo "Response: $delete_response"
        fi
    else
        echo "Creating code_fragments collection..."
        create_response=$(curl -s -X PUT -H "Content-Type: application/json" -d '{
            "vectors": {
                "size": 384,
                "distance": "Cosine"
            }
        }' http://localhost:6333/collections/code_fragments)
        
        if echo "$create_response" | grep -q "result.*true"; then
            echo "✅ Created code_fragments collection"
        else
            echo "⚠️ Unexpected response when creating collection"
            echo "Response: $create_response"
        fi
    fi
    
    echo "✅ Vector database reset"
fi

echo -e "\nAll databases have been reset."
echo "You should now restart the application to reinitialize the databases."
