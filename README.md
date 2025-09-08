# PDF to GraphRAG Knowledge Pipeline

A complete pipeline for converting PDF documents into queryable knowledge graphs using Microsoft's GraphRAG framework with Groq LLM integration.

## Project Structure

```
├── pipeline_orchestrator.py    # Main orchestration script
├── settings_fast.yaml          # GraphRAG configuration (rate-limited)
├── requirements.txt            # Python dependencies
├── input/                      # Place your PDF files here
└── graphrag_output/            # Generated knowledge graph data

```

## Architecture

```
┌─────────────────┐     ┌─────────────────┐    ┌─────────────────┐
│   PDF Input     │───▶│  Stirling PDF   │───▶│  Text Cleaning  │
│  (aws_book.pdf) │     │   Processing    │    │   & Chunking    │
└─────────────────┘     └─────────────────┘    └─────────────────┘
                                                        │
┌─────────────────┐    ┌─────────────────┐     ┌─────────────────┐
│   GraphRAG      │◀───│   Knowledge     │◀───│   Processed     │
│   Querying      │    │   Graph Gen     │     │     Text        │
└─────────────────┘    └─────────────────┘     └─────────────────┘
```

### Key Components

- **Stirling PDF**: Dockerized PDF processing service (text extraction + OCR)
- **GraphRAG**: Microsoft's graph-based RAG implementation 
- **Groq API**: Fast LLM processing (GPT-OSS 120B model)
- **OpenAI API**: Embeddings generation (text-embedding-3-small)

## Quick Start

### Prerequisites

1. **API Keys Required**:
   - [Groq API Key](https://console.groq.com/) 
   - [OpenAI API Key](https://platform.openai.com/api-keys) (for embeddings)


### Manual Setup

1. **Clone & Navigate**:
   ```powershell
   git clone https://github.com/justavik/RAGProject.git
   cd RAGProject
   ```

2. **Configure API Keys**:

3. **Run Pipeline**:
   ```powershell
   python pipeline_orchestrator.py
   ```

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

```powershell
cd .\graphrag_output
python -m graphrag query --root . --method global --query "Your question here"
```

**Query Types**:
- `global`: Broad questions about the entire document
- `local`: Specific questions about particular entities/concepts
```

## Configuration

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

## Performance

### Processing Times
- **Processing Time for 462 page AWS Guide Book: ~ 7 minutes**

### Bottlenecks
1. **API Rate Limits**: Primary limitation
2. **Network Latency**: To Groq/OpenAI servers
3. **PDF Complexity**: OCR vs direct text extraction

### Cost Estimates (Groq)
- **Processing**: ~$0.15 per 100 pages
- **Querying**: ~$0.01 per query (depends on reasoning level)
- **Storage**: Minimal (local files)
