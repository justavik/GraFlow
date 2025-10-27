# GraphRAG Chunk Size Study - Reproducibility Repository

## Repository Structure

```
GraFlow/
├── entity_validator.py           # SelfCheckGPT hallucination detection
├── visualize_graph.py             # Knowledge graph visualization tool
├── pipeline_orchestrator.py       # GraphRAG indexing automation
├── settings_fast.yaml             # GraphRAG configuration (Groq API)
├── requirements.txt               # Python dependencies
│
├── graphrag_output/prompts/       # Prompts directory
├── graphrag_output/settings.yaml/ 
├── graphrag_output/output/        # Generated knowledge graphs post indexing runs
│   ├── graph.graphml              # 3200-token run graph (929 entities)
│   ├── entities.parquet           # Entity extraction results
│   ├── relationships.parquet      # Entity relationships
│   └── text_units.parquet         # Source text chunks
│
├── pipeline_results.json          # Experimental metrics (post run)
└── validation_report.csv          # Hallucination analysis results

```

---

## Reproduce Our Results

### Prerequisites

- **Python 3.8+** with pip
- **API Keys** (for validation and visualization only):
  - [Groq API Key](https://console.groq.com/) - For entity validation
  - [OpenAI API Key](https://platform.openai.com/api-keys) - For embeddings (optional)

### Installation

1. **Clone Repository**:
   ```bash
   git clone https://github.com/justavik/GraFlow.git
   cd GraFlow
   ```

2. **Create Virtual Environment**:
   ```bash
   python -m venv venv
   
   # Windows PowerShell:
   .\venv\Scripts\Activate.ps1
   
   # Windows CMD:
   venv\Scripts\activate.bat
   
   # Linux/Mac:
   source venv/bin/activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure API Keys** (optional, for validation):
   Create `.env` file:
   ```env
   GROQ_API_KEY=your_groq_api_key_here
   OPENAI_API_KEY=your_openai_api_key_here  # Optional
   ```

---

## Explore Generated Results

### 1. Visualize Knowledge Graph

```bash
# Generate graph visualization from 3200-token run
python visualize_graph.py
```

**Generates:**
- `paper/paper_figures/fig3_knowledge_graph.png` - Top 150 entities, color-coded by centrality
- `paper/paper_figures/fig4_degree_distribution.png` - Degree distribution histogram
- **Statistics:** 929 entities, 1367 relationships, average degree 2.94

**Graph Insights:**
- **Hub nodes:** AWS (degree 101), Amazon Web Services (80), CloudTrail (39)
- **Sparse connectivity:** Density 0.0032 (selective relationship extraction)
- **Power-law distribution:** Few high-degree hubs, many peripheral nodes

### 2. Inspect Hallucination Validation Results

```bash
# View validation report (CSV format)
head -20 validation_report.csv
```

**Contains:**
- Per-entity hallucination status (SUPPORTED/UNSUPPORTED)
- Confidence scores (0-1)
- Validation issues identified
- Processing time per entity

---

## Reproduce Full Experiment

### Prerequisites for Full Reproduction

1. **Source Document:** 
   - Place PDF in `input/` directory

2. **Stirling PDF** (for text extraction):
   ```bash
   # Download and run Stirling PDF
   curl -L -o stirling-pdf.jar https://github.com/Stirling-Tools/Stirling-PDF/releases/latest/download/Stirling-PDF.jar
   java -jar stirling-pdf.jar
   # Runs on http://localhost:8080
   ```

3. **API Keys Required:**
   - Groq API (entity extraction + validation)
   - OpenAI API (embeddings)

### Run GraphRAG Indexing

```bash
# Run all 7 chunk sizes in increments of 400 (800-3200 tokens)
python pipeline_orchestrator.py
```

**What this does:**
1. Extracts text from PDF via Stirling PDF API
2. Cleans and preprocesses text (removes headers, footers, page numbers)
3. Chunks text at provided size in settings_fast.yaml
4. Runs GraphRAG entity extraction (Groq LLM: llama-3.3-70b-versatile)
5. Builds knowledge graph (node deduplication, relationship extraction)
6. Applies Leiden community detection (hierarchical clustering)
7. Generates vector embeddings (OpenAI text-embedding-3-small)
8. Saves results to `graphrag_output/`

### Run Hallucination Validation

```bash
# Validate entity descriptions using SelfCheckGPT
python entity_validator.py --all
```

**What this does:**
1. Loads entities from `graphrag_output/output/entities.parquet`
2. Retrieves source text chunks for each entity
3. Uses LLM (llama-3.3-70b-versatile via Groq) to verify descriptions
4. Classifies as SUPPORTED (no hallucination) or UNSUPPORTED (hallucination)
5. Generates `validation_report.csv` with per-entity results

---

## Acknowledgments

- **Microsoft GraphRAG** - Core knowledge graph framework
- **Groq** - High-performance LLM API
- **OpenAI** - Embedding models
- **NetworkX** - Graph analysis library
- **Stirling PDF** - PDF text extraction

---
