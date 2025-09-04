# PDF to GraphRAG Knowledge Pipeline

A complete end-to-end pipeline that converts PDF documents into queryable knowledge graphs using GraphRAG (Graph Retrieval-Augmented Generation) with Groq's fast LLM processing.

## 🎯 What This Pipeline Does

1. **PDF Processing**: Extracts text from PDFs using Stirling PDF API (with OCR fallback)
2. **Text Cleaning**: Processes and cleans extracted text for optimal GraphRAG ingestion
3. **Knowledge Graph Generation**: Creates entities, relationships, and communities using GraphRAG
4. **Intelligent Querying**: Enables natural language queries over the knowledge graph

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   PDF Input     │───▶│  Stirling PDF   │───▶│  Text Cleaning  │
│  (aws_book.pdf) │    │   Processing    │    │   & Chunking    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                        │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   GraphRAG      │◀───│   Knowledge     │◀───│   Processed     │
│   Querying      │    │   Graph Gen     │    │     Text        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Key Components

- **Stirling PDF**: Dockerized PDF processing service (text extraction + OCR)
- **GraphRAG**: Microsoft's graph-based RAG implementation 
- **Groq API**: Fast LLM processing (GPT-OSS 120B model)
- **OpenAI API**: Embeddings generation (text-embedding-3-small)

## 🚀 Quick Start

### ⚡ One-Command Launch (Easiest)

**For users who just want to test the functionality with minimal setup:**

1. **Add your PDF**:
   ```powershell
   # Create input directory and add your PDF
   mkdir input
   copy "C:\path\to\your\document.pdf" .\input\
   ```

2. **Run the one-command launcher**:
   ```powershell
   # Windows
   .\run-graphrag.ps1
   
   # Linux/Mac  
   ./run-graphrag.sh
   ```

3. **Enter your API keys when prompted** and let it run!

**What it does automatically**:
- ✅ Builds Docker containers
- ✅ Starts PDF processing service
- ✅ Processes your PDFs
- ✅ Generates knowledge graph
- ✅ Opens interactive query mode
- ✅ Handles all backend complexity

**Total user effort**: Add PDF → Run script → Enter API keys → Ask questions!

### 📺 Example Usage

```powershell
# Step 1: Add your document
mkdir input
copy "AWS_Guide.pdf" .\input\

# Step 2: Run one command
.\run-graphrag.ps1

# Output:
# 🚀 One-Command PDF to Knowledge Graph Pipeline
# ==============================================
# Groq API Key: [enter your key]
# OpenAI API Key: [enter your key]
# ✅ Found 1 PDF file(s) in ./input/
# 📋 PDF files to process:
#    📄 AWS_Guide.pdf
# 🚀 Ready to start? (y/N): y
# 
# 🎬 Starting the pipeline...
# 🐳 Building and starting containers...
# 📄 Processing PDF files...
# 🔄 Starting GraphRAG pipeline...
# [Processing occurs automatically...]
# 🎉 Pipeline completed successfully!
# 🤖 Starting interactive query mode...
# ❓ Your question: What are the main AWS services for compute?
# 🔍 Searching knowledge graph...
# [AI provides detailed answer about EC2, Lambda, ECS, etc.]
# 
# ❓ Your question: How do I set up auto-scaling?
# [AI provides step-by-step auto-scaling guide...]
```

---

### 🛠️ Manual Setup (Advanced Users)

**For users who want more control over the setup:**

### Prerequisites

1. **API Keys Required**:
   - [Groq API Key](https://console.groq.com/) (free tier available)
   - [OpenAI API Key](https://platform.openai.com/api-keys) (for embeddings)

2. **Docker** (for Stirling PDF service)

### Manual Setup

1. **Clone & Navigate**:
   ```powershell
   git clone https://github.com/justavik/RAGProject.git
   cd RAGProject
   ```

2. **Configure API Keys**:
   ```powershell
   # Copy the template and add your API keys
   copy .env.template .env
   # Edit .env with your actual API keys
   ```

3. **Run Setup Script**:
   ```powershell
   .\setup_groq_env.ps1
   ```

4. **Start Docker Service**:
   ```powershell
   docker-compose up -d
   ```

5. **Run Pipeline**:
   ```powershell
   python pipeline_orchestrator.py
   ```

### What's Included vs Generated

**📁 Files in Repository** (what you get when cloning):
```
✅ pipeline_orchestrator.py     # Main pipeline script
✅ settings_fast.yaml           # Optimized GraphRAG config  
✅ docker-compose.yml          # Stirling PDF service config
✅ requirements.txt            # Python dependencies
✅ setup_groq_env.ps1         # Environment setup script
✅ .env.template              # API keys template
✅ graphrag_output/           # GraphRAG working directory
   ├── prompts/.gitkeep       # Directory structure placeholder
   └── settings.yaml          # Runtime GraphRAG configuration
✅ README.md                  # This comprehensive documentation
```

**🚫 Not Included** (generated during pipeline execution):
```
❌ .env                       # Your API keys (copy from .env.template)
❌ *.pdf                      # Your input PDFs (add your own)
❌ graphrag_env/              # Virtual environment (created by setup)
❌ graphrag_output/output/    # Generated knowledge graph files
❌ graphrag_output/cache/     # Processing cache files  
❌ graphrag_output/logs/      # Execution logs
❌ StirlingPDF/              # Docker volume data (created at runtime)
❌ pipeline_results.json     # Execution summary (generated each run)
```

**🔧 What New Users Need to Do**:
1. Get API keys (Groq + OpenAI)
2. Copy `.env.template` to `.env` and add keys
3. Add their PDF file to the root directory
4. Run the setup script

2. **Create Environment File**:
   Create `.env` file with your API keys:
   ```env
   GROQ_API_KEY=your_groq_api_key_here
   GRAPHRAG_API_KEY=your_openai_api_key_here
   OPENAI_API_KEY=your_openai_api_key_here
   STIRLING_PDF_URL=http://localhost:8080
   CHUNK_SIZE=1200
   CHUNK_OVERLAP=50
   ```

3. **Start Services**:
   ```powershell
   # Start Stirling PDF service
   docker-compose up -d
   
   # Activate Python environment
   .\graphrag_env\Scripts\Activate.ps1
   
   # Load environment variables
   .\setup_groq_env.ps1
   ```

4. **Add Your PDF**:
   Place your PDF file as `aws_book.pdf` in the root directory (or modify the pipeline for your file)

### Run the Pipeline

```powershell
# Run the complete pipeline
python pipeline_orchestrator.py
```

The pipeline will:
- ✅ Extract text from your PDF
- ✅ Clean and process the text
- ✅ Generate the knowledge graph
- ✅ Enter interactive query mode

## 🔧 How It Works Under the Hood

### Stirling PDF Processing Engine

**Stirling PDF** is a Java-based, locally-hosted web application that provides comprehensive PDF manipulation capabilities. Here's how it works internally:

#### Architecture & Components
- **Backend**: Spring Boot Java application with REST API endpoints
- **PDF Processing**: Uses multiple libraries depending on the operation:
  - **Apache PDFBox**: Core PDF manipulation and text extraction
  - **LibreOffice**: Document conversion (PDF ↔ Word/PowerPoint/etc.)
  - **Tesseract OCR**: Optical Character Recognition for scanned documents
  - **qpdf**: PDF compression and optimization
- **Frontend**: HTML/CSS/JavaScript web interface
- **Container**: Runs in Docker with all dependencies pre-installed

#### Text Extraction Process
1. **Direct Text Extraction** (Primary Method):
   ```
   PDF → PDFBox Parser → Extract Text Streams → Clean Text → Output
   ```
   - Reads embedded text directly from PDF's content streams
   - Fast and accurate for PDFs with selectable text
   - Preserves text structure and formatting

2. **OCR Fallback** (For Scanned PDFs):
   ```
   PDF → Convert to Images → Tesseract OCR → Text Recognition → Output
   ```
   - Used when direct extraction fails or yields poor results
   - Converts PDF pages to images (PNG/JPEG)
   - Applies Tesseract OCR with configurable languages
   - More time-consuming but handles scanned documents

#### API Endpoints Used in Pipeline
- `/api/v1/convert/pdf/text` - Direct text extraction
- `/api/v1/misc/ocr-pdf` - OCR-based extraction
- Supports batch processing and custom parameters

#### Performance Characteristics
- **Speed**: Direct extraction ~1-5 seconds per document
- **OCR Speed**: ~10-30 seconds per page (depending on complexity)
- **Memory**: Efficiently handles large PDFs through streaming
- **Languages**: Supports 40+ languages for OCR

### Microsoft GraphRAG Knowledge Engine

**GraphRAG** is a sophisticated knowledge graph generation system that transforms unstructured text into queryable graph structures using Large Language Models.

#### Core Architecture

```
Input Text → TextUnits → Entity/Relationship Extraction → Graph Building → Community Detection → Summarization → Query Interface
```

#### Phase-by-Phase Breakdown

**Phase 1: Text Chunking (Compose TextUnits)**
```python
# Conceptual process
document = "Your PDF text content..."
chunk_size = 1200  # tokens (configurable)
overlap = 50       # token overlap between chunks

text_units = []
for i in range(0, len(document), chunk_size - overlap):
    chunk = document[i:i + chunk_size]
    text_units.append(TextUnit(id=i, content=chunk, source_document=doc_id))
```

- **Purpose**: Break large documents into analyzable chunks
- **Configuration**: Chunk size (300-1200 tokens), overlap percentage
- **Output**: Individual TextUnit objects with metadata

**Phase 2: Graph Extraction (The AI Magic)**

This is where the heavy LLM processing happens:

1. **Entity & Relationship Extraction**:
   ```
   For each TextUnit:
   │
   ├─ LLM Prompt: "Extract entities (people, places, organizations, events) 
   │              and relationships between them from this text"
   │
   ├─ LLM Response: JSON structure with:
   │   ├─ Entities: [{name, type, description}, ...]
   │   └─ Relationships: [{source, target, description, strength}, ...]
   │
   └─ Merge overlapping entities across chunks
   ```

2. **Entity Deduplication & Summarization**:
   ```python
   # Entities with same name/type get merged
   entity_AWS = {
       descriptions: [
           "Cloud computing platform by Amazon",
           "Amazon Web Services offering compute resources", 
           "AWS provides scalable cloud infrastructure"
       ]
   }
   
   # LLM creates unified description
   llm_prompt = "Summarize these descriptions into one coherent description"
   final_description = "Amazon Web Services (AWS) is Amazon's comprehensive cloud computing platform..."
   ```

3. **Claim Extraction** (Optional):
   - Extracts factual statements with time bounds
   - Example: "AWS Lambda was launched in 2014"
   - Creates "Covariate" objects for temporal reasoning

**Phase 3: Graph Augmentation (Community Detection)**

Uses the **Hierarchical Leiden Algorithm** for community detection:

```python
# Simplified community detection process
graph = create_graph(entities, relationships)

def leiden_clustering(graph, resolution=1.0):
    """
    Leiden algorithm finds communities by optimizing modularity
    """
    communities = {}
    
    # Step 1: Each node starts in its own community
    for node in graph.nodes:
        communities[node] = node
    
    # Step 2: Iteratively move nodes to improve modularity
    improved = True
    while improved:
        improved = False
        for node in graph.nodes:
            best_community = find_best_community(node, communities, graph)
            if best_community != communities[node]:
                communities[node] = best_community
                improved = True
    
    # Step 3: Create hierarchical structure
    return create_hierarchy(communities)
```

**Why Leiden Algorithm?**
- **Purpose**: Identifies clusters of related entities
- **Example**: In AWS document - all Lambda-related entities form one community, 
  all S3-related entities form another
- **Hierarchical**: Creates nested communities (AWS Services → Compute Services → Lambda Components)
- **Quality**: Superior to older methods like Louvain algorithm

**Phase 4: Community Summarization**

```python
for community in communities:
    # Get all entities and relationships in this community
    community_content = get_community_subgraph(community)
    
    # Generate executive summary
    llm_prompt = f"""
    Analyze this community of entities and relationships:
    Entities: {community_content.entities}
    Relationships: {community_content.relationships}
    
    Generate:
    1. Executive summary of this community
    2. Key themes and concepts
    3. Important relationships
    4. Notable entities and their roles
    """
    
    community_report = llm.generate(llm_prompt)
    store_report(community.id, community_report)
```

**Phase 5-7: Final Processing**
- **Document Linking**: Connect TextUnits back to original documents
- **Vector Embeddings**: Generate embeddings for semantic search
- **Graph Visualization**: Optional 2D projections using UMAP

#### Query Processing

**Global Search** (For broad questions):
```python
def global_search(query):
    # Use community reports for broad understanding
    relevant_communities = find_relevant_communities(query)
    context = combine_community_reports(relevant_communities)
    
    # Generate answer using community-level knowledge
    answer = llm.generate(f"Based on this knowledge: {context}\nAnswer: {query}")
    return answer
```

**Local Search** (For specific entity questions):
```python
def local_search(query):
    # Find specific entities mentioned in query
    entities = extract_entities_from_query(query)
    
    # Get entity neighborhood (connected entities and relationships)
    context = get_entity_neighborhoods(entities)
    
    # Include relevant text units for grounding
    text_context = get_relevant_text_units(entities)
    
    answer = llm.generate(f"Context: {context + text_context}\nAnswer: {query}")
    return answer
```

#### Data Model & Storage

GraphRAG creates these key data structures:
```python
# Parquet files generated
entities.parquet          # All extracted entities
relationships.parquet     # All relationships between entities
communities.parquet       # Community assignments
community_reports.parquet # Generated community summaries
text_units.parquet       # Original text chunks
documents.parquet        # Source document metadata
```

#### Why GraphRAG is Superior to Basic RAG

**Traditional RAG Problems**:
1. **Can't Connect Dots**: If info about AWS Lambda is in chunk 1 and pricing in chunk 50, basic RAG might miss connections
2. **No Holistic Understanding**: Can't answer "What are the main themes in this document?"

**GraphRAG Solutions**:
1. **Relationship Mapping**: Explicitly models connections between concepts
2. **Hierarchical Understanding**: Community structure provides multi-level abstractions
3. **Synthesis Capability**: Can generate insights from combining multiple pieces of information

#### Performance & Scaling

**Token Usage** (Major Cost Factor):
```
For 1000-page document:
├─ Entity Extraction: ~500-1000 API calls
├─ Relationship Extraction: ~500-1000 API calls  
├─ Community Summarization: ~50-200 API calls
├─ Text Embeddings: 1 call per text unit
└─ Total: ~1500-2500 LLM API calls

Cost: $5-50 depending on model (GPT-4 vs GPT-3.5 vs Groq)
```

**Processing Pipeline**:
- **Parallel Processing**: Multiple text chunks processed simultaneously
- **Caching**: Results cached to avoid reprocessing
- **Incremental Updates**: Can add new documents to existing graphs

**Memory Requirements**:
- **During Processing**: 2-8GB RAM for large documents
- **Storage**: ~10-100MB per 100 pages of processed documents
- **Vector Store**: Additional space for embeddings

### Query the Knowledge Graph

Once the pipeline completes, you can query in two ways:

**1. Interactive Mode** (automatically starts after pipeline):
```
Enter your question: What is AWS Lambda?
```

**2. Direct Command**:
```powershell
cd .\graphrag_output
python -m graphrag query --root . --method global --query "Your question here"
```

**Query Types**:
- `global`: Broad questions about the entire document
- `local`: Specific questions about particular entities/concepts

## 📁 Project Structure

```
FinalRAG/
├── 📄 pipeline_orchestrator.py     # Main pipeline script
├── 📄 settings_fast.yaml           # GraphRAG configuration (optimized)
├── 📄 setup_groq_env.ps1          # Environment setup script
├── 📄 requirements.txt             # Python dependencies
├── 📄 docker-compose.yml          # Stirling PDF service config
├── 📄 .env                        # API keys (create this)
├── 📄 aws_book.pdf                # Your input PDF
├── 📁 graphrag_env/               # Python virtual environment
├── 📁 graphrag_output/            # GraphRAG working directory
│   ├── 📁 input/                  # Processed text files
│   ├── 📁 output/                 # Generated knowledge graph
│   ├── 📁 prompts/               # GraphRAG prompts
│   └── 📄 settings.yaml          # Runtime GraphRAG config
└── 📁 StirlingPDF/               # Docker volume data
```

## ⚙️ Configuration

### Performance Tuning

The pipeline is pre-configured for optimal speed/cost balance:

- **Groq GPT-OSS 120B**: Fast, cost-effective LLM processing
- **OpenAI Embeddings**: Reliable text-embedding-3-small
- **Optimized Concurrency**: Balanced to avoid rate limits
- **No Caching**: Disabled to avoid Groq API compatibility issues

### Rate Limits & Concurrency

Current settings in `settings_fast.yaml`:
```yaml
concurrent_requests: 10        # Groq LLM calls
embedding_concurrent: 15       # OpenAI embedding calls  
num_threads: 20               # Overall parallelization
stagger: 0.1                  # Delay between requests
```

**If you hit rate limits**, reduce these values in `settings_fast.yaml`.

### Switching Models

To use different models, edit `settings_fast.yaml`:

```yaml
models:
  default_chat_model:
    model: openai/gpt-oss-120b        # Groq models
    # OR
    model: gpt-4o-mini                # OpenAI models (change api_base too)
```

## 🔧 Troubleshooting

### Common Issues

**1. Rate Limit Errors (429)**
```
openai.RateLimitError: Error code: 429
```
**Solution**: Reduce concurrency in `settings_fast.yaml`:
```yaml
concurrent_requests: 5    # Reduce from 10
num_threads: 10          # Reduce from 20
```

**2. Unicode Encoding Errors**
```
UnicodeEncodeError: 'charmap' codec can't encode character
```
**Solution**: Set UTF-8 encoding in PowerShell:
```powershell
$OutputEncoding = [console]::InputEncoding = [console]::OutputEncoding = New-Object System.Text.UTF8Encoding
```

**3. Stirling PDF Connection Failed**
```
Cannot reach API: Connection refused
```
**Solution**: Ensure Docker service is running:
```powershell
docker-compose up -d
docker ps  # Should show stirling-pdf container
```

**4. GraphRAG Module Not Found**
```
No module named graphrag
```
**Solution**: Ensure virtual environment is activated:
```powershell
.\graphrag_env\Scripts\Activate.ps1
```

**5. Environment Variables Not Found**
```
KeyError: 'GROQ_API_KEY'
```
**Solution**: Run the environment setup:
```powershell
.\setup_groq_env.ps1
```

### Performance Optimization

**Speed vs Cost Trade-offs**:

1. **Fastest (Higher Cost)**:
   - Use `gpt-4o-mini` with OpenAI
   - Increase `concurrent_requests: 20`
   - Decrease `chunk_size: 800`

2. **Balanced (Current)**:
   - Use `openai/gpt-oss-120b` with Groq
   - `concurrent_requests: 10`
   - `chunk_size: 1200`

3. **Cheapest (Slower)**:
   - Use `mixtral-8x7b-32768` with Groq
   - Decrease `concurrent_requests: 3`
   - Increase `chunk_size: 2000`

## 🚗 Expected Performance

### Processing Times
- **Small PDF** (50 pages): ~5-10 minutes
- **Medium PDF** (200 pages): ~15-30 minutes  
- **Large PDF** (500+ pages): ~45-90 minutes

### Bottlenecks
1. **API Rate Limits**: Primary limitation
2. **Network Latency**: To Groq/OpenAI servers
3. **PDF Complexity**: OCR vs direct text extraction

### Cost Estimates (Groq)
- **Processing**: ~$0.10-$0.50 per 100 pages
- **Querying**: ~$0.01 per query
- **Storage**: Minimal (local files)

## 🔄 Development & Customization

### Adding New PDF Sources

1. **Modify Input Path**:
   ```python
   # In pipeline_orchestrator.py, main() function:
   pdf_files = [Path("your_document.pdf")]
   ```

2. **Batch Processing**:
   ```python
   # Process multiple PDFs:
   pdf_files = list(Path("./pdfs/").glob("*.pdf"))
   ```

### Custom GraphRAG Settings

Create your own settings by copying `settings_fast.yaml`:
```powershell
cp settings_fast.yaml settings_custom.yaml
# Edit settings_custom.yaml
# Update pipeline_orchestrator.py to use your custom settings
```

### Integration with Other Services

The pipeline is modular - you can replace components:

- **PDF Processing**: Replace Stirling PDF with PyPDF2, pdfplumber, etc.
- **LLM Provider**: Switch from Groq to Anthropic, Azure OpenAI, etc.
- **Vector Store**: GraphRAG supports different vector databases

## 📊 Monitoring & Logging

### Real-time Progress
The pipeline provides detailed logging:
- 📊 File processing progress
- 🔄 GraphRAG indexing stages  
- ⏱️ Performance timing
- ⚠️ Error details with solutions

### Output Files
- `pipeline_results.json`: Execution summary
- `graphrag_output/logs/`: Detailed GraphRAG logs
- `graphrag_output/output/`: Generated knowledge artifacts

## 📊 Technical Configuration Deep-Dive

### Groq API Rate Limiting & Optimization

**Rate Limit Configuration** (in `settings_fast.yaml`):
```yaml
llm:
  api_key: ${GROQ_API_KEY}
  type: openai_chat
  model: llama-3.1-70b-versatile  # 250K TPM limit
  api_base: https://api.groq.com/openai/v1
  concurrent_requests: 10         # Reduced from default 25
  
parallelization:
  num_threads: 20                 # Reduced from default 50
  
cache:
  type: none                      # Disabled due to Groq compatibility
```

**Why These Settings Matter**:
- **Groq TPM Limit**: 250,000 tokens per minute across all requests
- **Conservative Concurrency**: 10 concurrent requests prevent 429 errors
- **No Caching**: Groq responses have different format than OpenAI, causing parsing errors
- **Thread Management**: 20 threads balance speed with stability

### Pipeline Architecture & Data Flow

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Input PDF     │ -> │  Stirling PDF    │ -> │  Cleaned Text   │
│  (aws_book.pdf) │    │   Text Extract   │    │    (.txt)       │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                          │
┌─────────────────┐    ┌──────────────────┐              │
│   Query Loop    │ <- │    GraphRAG      │ <───────────┘
│  (Interactive)  │    │ Knowledge Graph  │    
└─────────────────┘    └──────────────────┘
                              │
                       ┌──────────────────┐
                       │   Parquet Files  │
                       │ (entities, rels, │
                       │  communities)    │
                       └──────────────────┘
```

### File Structure & Outputs

**Input Processing**:
- `input/aws_book.pdf` → Raw PDF document
- `processed_text/aws_book_processed.txt` → Extracted & cleaned text
- `graphrag_input/aws_book_processed.txt` → Copy for GraphRAG processing

**GraphRAG Outputs** (in `graphrag_output/output/`):
- `entities.parquet` → All extracted entities (AWS services, concepts, etc.)
- `relationships.parquet` → Connections between entities
- `communities.parquet` → Clustered groups of related entities
- `community_reports.parquet` → AI-generated summaries of each cluster
- `text_units.parquet` → Original text chunks with metadata
- `documents.parquet` → Source document information

**Configuration Files**:
- `settings_fast.yaml` → Main GraphRAG configuration (rate limits, models)
- `docker-compose.yml` → Stirling PDF service definition
- `requirements.txt` → Python dependencies

### Advanced Error Handling & Troubleshooting

**Common Issues & Solutions**:

1. **Groq Rate Limits (429 errors)**:
   ```
   Error: Request rate limit exceeded
   Solution: Reduce concurrent_requests in settings_fast.yaml
   Current: 10 (conservative for 250K TPM limit)
   ```

2. **Unicode Encoding Errors**:
   ```powershell
   # Set PowerShell to UTF-8 before running
   [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
   ```

3. **Stirling PDF Connection Issues**:
   ```powershell
   # Verify service is running
   docker-compose ps
   # Should show stirling-pdf container as "Up"
   ```

4. **Memory Issues During Processing**:
   ```yaml
   # Reduce chunk size in settings_fast.yaml
   chunks:
     size: 300      # Reduce from 1200 for large documents
     overlap: 100   # Maintain good overlap
   ```

### Performance Benchmarks

**Processing Times** (AWS Book Example - ~1000 pages):
- PDF Text Extraction: ~30 seconds
- GraphRAG Indexing: ~45-60 minutes (with rate limiting)
- Knowledge Graph Generation: Creates ~500 entities, ~800 relationships
- Query Response Time: ~10-30 seconds per query

**Resource Usage**:
- RAM: 4-8GB during processing
- Storage: ~50MB for complete knowledge graph
- Network: ~250K tokens to Groq API (~$1-2 in API costs)

**Scalability**:
- Documents up to 2000 pages: Works well with current settings
- Larger documents: May need chunk size reduction and longer processing time
- Multiple documents: Can be processed sequentially or with separate projects

### Production Deployment Considerations

**Repository Structure & Sharing**:

The `.gitignore` is carefully configured to share essential setup files while excluding:
- **Generated content**: Knowledge graphs, cache files, logs (recreated during processing)
- **Sensitive data**: API keys in `.env` files, personal PDF documents
- **Environment-specific**: Virtual environments, Docker volumes, OS-specific files
- **Large files**: PDFs, processing outputs (users add their own documents)

**What gets shared in repository**:
```yaml
Essential Files:
  ✅ pipeline_orchestrator.py      # Core pipeline logic
  ✅ settings_fast.yaml            # Optimized configurations
  ✅ docker-compose.yml           # Service definitions  
  ✅ requirements.txt             # Dependencies
  ✅ .env.template               # API key template
  ✅ graphrag_output/settings.yaml # GraphRAG runtime config
  ✅ README.md                   # Complete documentation

Directory Structure:
  ✅ graphrag_output/prompts/.gitkeep # Preserves directory structure
  🚫 graphrag_output/output/          # Generated knowledge graphs
  🚫 graphrag_output/cache/           # Processing cache
  🚫 StirlingPDF/                     # Docker volume data
```

**Docker Compose Setup**:
```yaml
# Recommended production settings
services:
  stirling-pdf:
    image: frooodle/s-pdf:latest
    restart: unless-stopped
    ports:
      - "8080:8080"
    volumes:
      - ./StirlingPDF:/usr/share/tesseract-ocr/5/tessdata
    environment:
      - DOCKER_ENABLE_SECURITY=false
      - INSTALL_BOOK_AND_ADVANCED_HTML_OPS=false
    deploy:
      resources:
        limits:
          memory: 4G
          cpus: '2.0'
```

**Environment Variables**:
```bash
# Required for production
GROQ_API_KEY=your_groq_api_key_here
OPENAI_API_KEY=your_openai_key_for_embeddings
GRAPHRAG_LOG_LEVEL=INFO
PYTHONIOENCODING=utf-8
```

**Monitoring & Logging**:
- Monitor API usage through Groq dashboard
- Track processing times with `pipeline_results.json`
- Use GraphRAG logs for debugging indexing issues
- Consider implementing retry logic for rate limit handling


## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push branch: `git push origin feature/amazing-feature`
5. Open Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **Microsoft GraphRAG**: Graph-based RAG implementation
- **Groq**: Fast LLM inference platform
- **Stirling PDF**: Open-source PDF manipulation tool
- **OpenAI**: Embedding models and APIs

---

**Need Help?** 
- 📖 Check the troubleshooting section above
- 🐛 Open an issue on GitHub
- 💡 Join the community discussions
