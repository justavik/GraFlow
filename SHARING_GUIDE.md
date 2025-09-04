# Repository Sharing Guide

## ✅ What Gets Shared in Git Repository

### Essential Pipeline Files
- `pipeline_orchestrator.py` - Main pipeline script
- `settings_fast.yaml` - Optimized GraphRAG configuration
- `docker-compose.yml` - Stirling PDF service definition
- `requirements.txt` - Python dependencies
- `README.md` - Comprehensive documentation

### Setup & Configuration
- `.env.template` - API keys template (users copy to .env)
- `setup_groq_env.ps1` - Automated environment setup
- `validate_setup.py` - Setup validation script
- `.gitignore` - Properly configured to exclude sensitive/generated content

### GraphRAG Directory Structure
- `graphrag_output/settings.yaml` - Runtime GraphRAG configuration
- `graphrag_output/prompts/.gitkeep` - Preserves directory structure

## 🚫 What Gets Ignored (Not Shared)

### Sensitive Information
- `.env` - Contains actual API keys
- `*.pdf` - User's private documents

### Generated Content
- `graphrag_output/output/` - Knowledge graph files (entities, relationships)
- `graphrag_output/cache/` - Processing cache
- `graphrag_output/logs/` - Execution logs
- `pipeline_results.json` - Pipeline execution summary

### Environment-Specific
- `graphrag_env/` - Python virtual environment
- `StirlingPDF/` - Docker volume data
- `__pycache__/` - Python bytecode
- OS-specific files (.DS_Store, Thumbs.db)

## 🔧 What New Users Need to Do

1. **Clone repository** - Gets all essential files
2. **Copy .env.template to .env** - Add their API keys
3. **Run setup script** - `.\setup_groq_env.ps1`
4. **Add their PDF** - Place in root directory
5. **Start Docker** - `docker-compose up -d`
6. **Run validation** - `python validate_setup.py`
7. **Execute pipeline** - `python pipeline_orchestrator.py`

## 📊 File Size Considerations

**Repository size**: ~1-2MB (just code and docs)
**Generated output**: ~10-100MB (depends on document size)
**Docker volumes**: ~500MB-1GB (Stirling PDF dependencies)

This structure ensures:
- ✅ New users get everything needed to run the pipeline
- ✅ No sensitive data (API keys) or large files in git
- ✅ Generated content is recreated during processing
- ✅ Clear separation between shared code and user data
