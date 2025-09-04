"""
Setup Validation Script
Helps new users verify their environment is correctly configured
"""

import os
import sys
import subprocess
from pathlib import Path

try:
    import requests
except ImportError:
    requests = None

def check_mark(condition, message):
    """Print status with checkmark or X"""
    symbol = "✅" if condition else "❌"
    print(f"{symbol} {message}")
    return condition

def validate_setup():
    """Validate the complete setup"""
    print("🔍 Validating FinalRAG Pipeline Setup")
    print("=" * 50)
    
    all_good = True
    
    # Check Python version
    python_version = sys.version_info
    python_ok = python_version.major == 3 and python_version.minor >= 8
    all_good &= check_mark(python_ok, f"Python version: {python_version.major}.{python_version.minor}")
    
    # Check virtual environment
    venv_active = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
    all_good &= check_mark(venv_active, "Virtual environment activated")
    
    # Check required files
    required_files = [
        "pipeline_orchestrator.py",
        "settings_fast.yaml", 
        "docker-compose.yml",
        "requirements.txt",
        ".env"
    ]
    
    for file in required_files:
        exists = Path(file).exists()
        all_good &= check_mark(exists, f"Required file: {file}")
    
    # Check environment variables
    groq_key = os.getenv('GROQ_API_KEY')
    openai_key = os.getenv('GRAPHRAG_API_KEY')
    
    groq_key_valid = bool(groq_key and groq_key != 'your_groq_api_key_here')
    openai_key_valid = bool(openai_key and openai_key != 'your_openai_api_key_here')
    
    all_good = all_good and check_mark(groq_key_valid, "Groq API key configured")
    all_good = all_good and check_mark(openai_key_valid, "OpenAI API key configured")
    
    # Check Docker
    try:
        result = subprocess.run(['docker', '--version'], capture_output=True, text=True)
        docker_ok = result.returncode == 0
    except FileNotFoundError:
        docker_ok = False
    
    all_good &= check_mark(docker_ok, "Docker installed")
    
    # Check Stirling PDF service
    stirling_ok = False
    if requests:
        try:
            response = requests.get('http://localhost:8080', timeout=5)
            stirling_ok = response.status_code == 200
        except:
            stirling_ok = False
    
    all_good = all_good and check_mark(stirling_ok, "Stirling PDF service running (http://localhost:8080)")
    
    # Check for PDF file
    pdf_files = list(Path('.').glob('*.pdf'))
    pdf_available = len(pdf_files) > 0
    all_good &= check_mark(pdf_available, f"PDF file available: {pdf_files[0] if pdf_files else 'None found'}")
    
    # Check GraphRAG directory structure
    graphrag_dir = Path('graphrag_output')
    structure_ok = graphrag_dir.exists() and (graphrag_dir / 'settings.yaml').exists()
    all_good &= check_mark(structure_ok, "GraphRAG directory structure")
    
    print("\n" + "=" * 50)
    if all_good:
        print("🎉 Setup validation PASSED! Ready to run pipeline.")
        print("\nNext steps:")
        print("   python pipeline_orchestrator.py")
    else:
        print("⚠️  Setup validation FAILED. Please fix the issues above.")
        print("\nCommon solutions:")
        print("   • Run: .\\setup_groq_env.ps1")
        print("   • Copy .env.template to .env and add API keys")
        print("   • Start Docker: docker-compose up -d")
        print("   • Add a PDF file to the root directory")

if __name__ == "__main__":
    validate_setup()
