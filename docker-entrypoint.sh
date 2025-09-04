#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}🚀 PDF to GraphRAG Knowledge Pipeline${NC}"
echo -e "${CYAN}====================================${NC}"

# Check for API keys
if [[ -z "$GROQ_API_KEY" || -z "$GRAPHRAG_API_KEY" ]]; then
    echo -e "${RED}❌ Missing API Keys!${NC}"
    echo -e "${YELLOW}Please set environment variables:${NC}"
    echo -e "   GROQ_API_KEY=your_groq_api_key"
    echo -e "   GRAPHRAG_API_KEY=your_openai_api_key"
    echo ""
    echo -e "${BLUE}Example:${NC}"
    echo -e "   docker run -e GROQ_API_KEY=gsk_xxx -e GRAPHRAG_API_KEY=sk-xxx ..."
    exit 1
fi

# Check for PDF files in input directory
PDF_COUNT=$(find /app/input -name "*.pdf" 2>/dev/null | wc -l)
if [[ $PDF_COUNT -eq 0 ]]; then
    echo -e "${RED}❌ No PDF files found!${NC}"
    echo -e "${YELLOW}Please mount a directory with PDF files:${NC}"
    echo -e "   docker run -v /path/to/your/pdfs:/app/input ..."
    echo ""
    echo -e "${BLUE}Your PDF files should be in the mounted input directory${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Found $PDF_COUNT PDF file(s) to process${NC}"

# Start Stirling PDF service in background
echo -e "${BLUE}🐳 Starting Stirling PDF service...${NC}"
docker run -d --name stirling-pdf-temp -p 8080:8080 frooodle/s-pdf:latest > /dev/null 2>&1

# Wait for Stirling PDF to be ready
echo -e "${YELLOW}⏳ Waiting for PDF service to start...${NC}"
for i in {1..30}; do
    if curl -s http://localhost:8080 > /dev/null 2>&1; then
        echo -e "${GREEN}✅ PDF service ready!${NC}"
        break
    fi
    if [[ $i -eq 30 ]]; then
        echo -e "${RED}❌ PDF service failed to start${NC}"
        exit 1
    fi
    sleep 2
done

# Set up environment
export STIRLING_PDF_URL="http://localhost:8080"
export CHUNK_SIZE="1200"
export CHUNK_OVERLAP="50"

# Create .env file
cat > .env << EOF
GROQ_API_KEY=$GROQ_API_KEY
GRAPHRAG_API_KEY=$GRAPHRAG_API_KEY
OPENAI_API_KEY=$GRAPHRAG_API_KEY
STIRLING_PDF_URL=http://localhost:8080
CHUNK_SIZE=1200
CHUNK_OVERLAP=50
GRAPHRAG_LOG_LEVEL=INFO
PYTHONIOENCODING=utf-8
EOF

echo -e "${GREEN}✅ Environment configured${NC}"

# Find and process PDFs
echo -e "${BLUE}📄 Processing PDF files...${NC}"

# Auto-detect PDF files and copy them to expected location
for pdf_file in /app/input/*.pdf; do
    if [[ -f "$pdf_file" ]]; then
        cp "$pdf_file" "/app/$(basename "$pdf_file")"
        echo -e "${GREEN}📋 Processing: $(basename "$pdf_file")${NC}"
        break  # Process first PDF found
    fi
done

# Run the pipeline
echo -e "${CYAN}🔄 Starting GraphRAG pipeline...${NC}"
echo -e "${YELLOW}This may take 15-60 minutes depending on document size${NC}"

python pipeline_orchestrator.py

# Check if pipeline completed successfully
if [[ $? -eq 0 ]]; then
    echo -e "${GREEN}🎉 Pipeline completed successfully!${NC}"
    echo -e "${CYAN}🤖 Starting interactive query mode...${NC}"
    echo -e "${YELLOW}Ask questions about your document!${NC}"
    echo -e "${BLUE}Type 'exit' to quit${NC}"
    echo ""
    
    # Start interactive query loop
    cd /app/graphrag_output
    while true; do
        echo -n -e "${CYAN}❓ Your question: ${NC}"
        read -r question
        
        if [[ "$question" == "exit" || "$question" == "quit" ]]; then
            echo -e "${GREEN}👋 Thanks for using GraphRAG Pipeline!${NC}"
            break
        fi
        
        if [[ -n "$question" ]]; then
            echo -e "${YELLOW}🔍 Searching knowledge graph...${NC}"
            python -m graphrag query --root . --method global --query "$question"
            echo ""
        fi
    done
else
    echo -e "${RED}❌ Pipeline failed. Check logs above.${NC}"
    exit 1
fi

# Cleanup
echo -e "${BLUE}🧹 Cleaning up...${NC}"
docker stop stirling-pdf-temp > /dev/null 2>&1
docker rm stirling-pdf-temp > /dev/null 2>&1
