# Setup Groq Environment Variables
# Run this script before running the pipeline

Write-Host "🔧 Setting up FinalRAG Pipeline Environment..." -ForegroundColor Green
Write-Host "=" * 60

# Check if .env.template exists and .env doesn't
if ((Test-Path ".env.template") -and !(Test-Path ".env")) {
    Write-Host "📋 Creating .env from template..." -ForegroundColor Yellow
    Copy-Item ".env.template" ".env"
    Write-Host "❗ IMPORTANT: Edit .env file and add your API keys!" -ForegroundColor Red
    Write-Host "   Get Groq API key: https://console.groq.com/keys" -ForegroundColor Cyan
    Write-Host "   Get OpenAI API key: https://platform.openai.com/api-keys" -ForegroundColor Cyan
    Write-Host ""
    Read-Host "Press Enter after you've added your API keys to .env file"
}

# Load .env file if it exists
if (Test-Path ".env") {
    Write-Host "📁 Loading environment variables from .env file..." -ForegroundColor Cyan
    Get-Content ".env" | ForEach-Object {
        if ($_ -match '^([^#][^=]+)=(.*)$') {
            $name = $matches[1].Trim()
            $value = $matches[2].Trim('"')
            Set-Item -Path "env:$name" -Value $value
            Write-Host "   Loaded: $name" -ForegroundColor Gray
        }
    }
} else {
    Write-Host "❌ .env file not found! Creating from template..." -ForegroundColor Red
    if (Test-Path ".env.template") {
        Copy-Item ".env.template" ".env"
        Write-Host "✅ .env created. Please edit it with your API keys and run this script again." -ForegroundColor Yellow
        exit 1
    } else {
        Write-Host "❌ .env.template not found! Please create .env file manually." -ForegroundColor Red
        exit 1
    }
}

# Validate API keys
$keysValid = $true

if ($env:GROQ_API_KEY -and $env:GROQ_API_KEY -ne 'your_groq_api_key_here') {
    Write-Host "✅ GROQ_API_KEY is configured" -ForegroundColor Green
} else {
    Write-Host "❌ GROQ_API_KEY not properly configured" -ForegroundColor Red
    $keysValid = $false
}

if ($env:GRAPHRAG_API_KEY -and $env:GRAPHRAG_API_KEY -ne 'your_openai_api_key_here') {
    Write-Host "✅ GRAPHRAG_API_KEY (OpenAI) is configured" -ForegroundColor Green  
} else {
    Write-Host "❌ GRAPHRAG_API_KEY (OpenAI) not properly configured" -ForegroundColor Red
    $keysValid = $false
}

if (!$keysValid) {
    Write-Host "🔑 Please edit .env file with your actual API keys and run this script again." -ForegroundColor Yellow
    exit 1
}

# Create virtual environment if it doesn't exist
if (!(Test-Path "graphrag_env")) {
    Write-Host "🐍 Creating Python virtual environment..." -ForegroundColor Cyan
    python -m venv graphrag_env
}

# Activate virtual environment
Write-Host "🔌 Activating virtual environment..." -ForegroundColor Cyan
& .\graphrag_env\Scripts\Activate.ps1

# Install requirements
Write-Host "📦 Installing Python dependencies..." -ForegroundColor Cyan
pip install -r requirements.txt

# Check Docker
Write-Host "🐳 Checking Docker..." -ForegroundColor Cyan
try {
    $dockerVersion = docker --version
    Write-Host "✅ Docker found: $dockerVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker not found. Please install Docker Desktop." -ForegroundColor Red
    Write-Host "   Download: https://www.docker.com/products/docker-desktop/" -ForegroundColor Cyan
}

Write-Host ""
Write-Host "🚀 Environment setup complete!" -ForegroundColor Green
Write-Host "   • Groq GPT-OSS 120B for LLM tasks (fast!)" -ForegroundColor Cyan
Write-Host "   • OpenAI for embeddings (reliable)" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "   1. Start Docker: docker-compose up -d" -ForegroundColor White
Write-Host "   2. Add your PDF to the root directory" -ForegroundColor White
Write-Host "   3. Run validation: python validate_setup.py" -ForegroundColor White
Write-Host "   4. Run pipeline: python pipeline_orchestrator.py" -ForegroundColor White
