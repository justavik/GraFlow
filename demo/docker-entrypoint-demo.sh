#!/bin/bash
set -e

echo "🚀 GraphRAG Demo Pipeline Starting..."
echo "====================================="

# Validate environment
if [ -z "$GROQ_API_KEY" ] || [ -z "$OPENAI_API_KEY" ]; then
    echo "❌ Error: Missing API keys"
    echo "Required: GROQ_API_KEY and OPENAI_API_KEY"
    exit 1
fi

# Create environment file
cat > .env << EOF
GRAPHRAG_API_KEY="$OPENAI_API_KEY"
OPENAI_API_KEY="$OPENAI_API_KEY"
GROQ_API_KEY="$GROQ_API_KEY"
STIRLING_PDF_URL=http://stirling-pdf-service:8080
CHUNK_SIZE=1200
CHUNK_OVERLAP=100
EOF

echo "✅ Environment configured"

# Wait for Stirling PDF service
echo "⏳ Waiting for Stirling PDF service..."
timeout=60
count=0
while ! curl -sf http://stirling-pdf-service:8080/api/v1/info >/dev/null 2>&1; do
    if [ $count -ge $timeout ]; then
        echo "❌ Timeout waiting for Stirling PDF service"
        exit 1
    fi
    sleep 2
    count=$((count + 2))
    echo "   Waiting... ($count/${timeout}s)"
done
echo "✅ Stirling PDF service ready"

# Check for PDF files
if [ ! "$(find /app/input -name '*.pdf' -type f 2>/dev/null)" ]; then
    echo "❌ No PDF files found in /app/input/"
    echo "Add PDF files to the input directory"
    exit 1
fi

echo "📄 Processing PDF files:"
find /app/input -name "*.pdf" -type f -exec basename {} \;

# Run pipeline
echo "🔄 Running GraphRAG pipeline..."
python pipeline_orchestrator.py

if [ $? -eq 0 ]; then
    echo "✅ Pipeline completed successfully!"
    echo ""
    echo "🎯 Interactive Query Interface"
    echo "=============================="
    echo "Commands:"
    echo "  local <query>   - Search specific entities/relationships"
    echo "  global <query>  - Search broad themes/summaries"
    echo "  exit           - Exit interface"
    echo ""
    
    # Interactive query loop
    while true; do
        echo -n "GraphRAG> "
        read input
        
        case "$input" in
            "exit"|"quit"|"q")
                echo "👋 Goodbye!"
                break
                ;;
            "help"|"h")
                echo "Commands: local <query>, global <query>, exit"
                ;;
            local\ *)
                query="${input#local }"
                if [ -n "$query" ]; then
                    echo "🔍 Local search: $query"
                    cd /app/graphrag_output && python -m graphrag query --root . --method local --query "$query" 2>/dev/null || echo "❌ Query failed"
                else
                    echo "Usage: local <your question>"
                fi
                ;;
            global\ *)
                query="${input#global }"
                if [ -n "$query" ]; then
                    echo "🌐 Global search: $query"
                    cd /app/graphrag_output && python -m graphrag query --root . --method global --query "$query" 2>/dev/null || echo "❌ Query failed"
                else
                    echo "Usage: global <your question>"
                fi
                ;;
            "")
                # Empty input, continue
                ;;
            *)
                echo "❌ Unknown command. Try: local <query>, global <query>, or exit"
                ;;
        esac
    done
else
    echo "❌ Pipeline failed"
    exit 1
fi
