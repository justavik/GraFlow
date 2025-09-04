#!/bin/bash

# One-Command GraphRAG Pipeline Launcher
# Usage: ./run-graphrag.sh

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}"
echo "██████╗ ██████╗ ███████╗    ████████╗ ██████╗      ██████╗ ██████╗  █████╗ ██████╗ ██╗  ██╗██████╗  █████╗  ██████╗ "
echo "██╔══██╗██╔══██╗██╔════╝    ╚══██╔══╝██╔═══██╗    ██╔════╝ ██╔══██╗██╔══██╗██╔══██╗██║  ██║██╔══██╗██╔══██╗██╔════╝ "
echo "██████╔╝██║  ██║█████╗         ██║   ██║   ██║    ██║  ███╗██████╔╝███████║██████╔╝███████║██████╔╝███████║██║  ███╗"
echo "██╔═══╝ ██║  ██║██╔══╝         ██║   ██║   ██║    ██║   ██║██╔══██╗██╔══██║██╔═══╝ ██╔══██║██╔══██╗██╔══██║██║   ██║"
echo "██║     ██████╔╝██║            ██║   ╚██████╔╝    ╚██████╔╝██║  ██║██║  ██║██║     ██║  ██║██║  ██║██║  ██║╚██████╔╝"
echo "╚═╝     ╚═════╝ ╚═╝            ╚═╝    ╚═════╝      ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝     ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝ "
echo -e "${NC}"
echo -e "${CYAN}🚀 One-Command PDF to Knowledge Graph Pipeline${NC}"
echo -e "${CYAN}==============================================${NC}"

# Check if API keys are provided
if [[ -z "$GROQ_API_KEY" && -z "$GRAPHRAG_API_KEY" ]]; then
    echo -e "${YELLOW}🔑 API Keys Setup${NC}"
    echo -e "${BLUE}Please enter your API keys:${NC}"
    
    echo -n -e "${CYAN}Groq API Key: ${NC}"
    read -r GROQ_API_KEY
    
    echo -n -e "${CYAN}OpenAI API Key (for embeddings): ${NC}"
    read -r GRAPHRAG_API_KEY
    
    # Export for this session
    export GROQ_API_KEY
    export GRAPHRAG_API_KEY
fi

# Check for PDF directory
PDF_DIR="./input"
if [[ ! -d "$PDF_DIR" ]]; then
    mkdir -p "$PDF_DIR"
fi

PDF_COUNT=$(find "$PDF_DIR" -name "*.pdf" 2>/dev/null | wc -l)
if [[ $PDF_COUNT -eq 0 ]]; then
    echo -e "${YELLOW}📄 PDF Setup${NC}"
    echo -e "${RED}No PDF files found in ./input/ directory${NC}"
    echo -e "${BLUE}Please add your PDF files to the ./input/ directory and run again${NC}"
    echo ""
    echo -e "${CYAN}Example:${NC}"
    echo -e "   cp /path/to/your/document.pdf ./input/"
    echo -e "   ./run-graphrag.sh"
    exit 1
fi

echo -e "${GREEN}✅ Found $PDF_COUNT PDF file(s) in ./input/${NC}"

# Show what we're about to process
echo -e "${BLUE}📋 PDF files to process:${NC}"
find "$PDF_DIR" -name "*.pdf" -exec basename {} \; | head -5

echo ""
echo -e "${YELLOW}⚡ This will:${NC}"
echo -e "   🔹 Start PDF processing service"
echo -e "   🔹 Extract text from your PDFs"  
echo -e "   🔹 Generate knowledge graph with AI"
echo -e "   🔹 Open interactive query interface"
echo ""
echo -e "${CYAN}⏳ Estimated time: 15-60 minutes (depending on PDF size)${NC}"
echo ""

# Confirm before proceeding
echo -n -e "${YELLOW}🚀 Ready to start? (y/N): ${NC}"
read -r confirm
if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
    echo -e "${BLUE}👋 Setup cancelled. Run again when ready!${NC}"
    exit 0
fi

echo ""
echo -e "${GREEN}🎬 Starting the pipeline...${NC}"

# Create .env file for docker-compose
cat > .env << EOF
GROQ_API_KEY=$GROQ_API_KEY
GRAPHRAG_API_KEY=$GRAPHRAG_API_KEY
EOF

# Run the full pipeline using docker-compose
echo -e "${BLUE}🐳 Building and starting containers...${NC}"

# Build the image first
docker-compose -f docker-compose.full.yml build --no-cache

# Start the pipeline
docker-compose -f docker-compose.full.yml up --abort-on-container-exit

# Cleanup
echo -e "${BLUE}🧹 Cleaning up containers...${NC}"
docker-compose -f docker-compose.full.yml down

echo -e "${GREEN}✨ Pipeline completed!${NC}"
echo -e "${CYAN}📊 Your knowledge graph data is preserved in Docker volume 'graphrag_output'${NC}"
