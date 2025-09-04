# One-Command GraphRAG Pipeline Launcher (Windows)
# Usage: .\run-graphrag.ps1

Write-Host @"
██████╗ ██████╗ ███████╗    ████████╗ ██████╗      ██████╗ ██████╗  █████╗ ██████╗ ██╗  ██╗██████╗  █████╗  ██████╗ 
██╔══██╗██╔══██╗██╔════╝    ╚══██╔══╝██╔═══██╗    ██╔════╝ ██╔══██╗██╔══██╗██╔══██╗██║  ██║██╔══██╗██╔══██╗██╔════╝ 
██████╔╝██║  ██║█████╗         ██║   ██║   ██║    ██║  ███╗██████╔╝███████║██████╔╝███████║██████╔╝███████║██║  ███╗
██╔═══╝ ██║  ██║██╔══╝         ██║   ██║   ██║    ██║   ██║██╔══██╗██╔══██║██╔═══╝ ██╔══██║██╔══██╗██╔══██║██║   ██║
██║     ██████╔╝██║            ██║   ╚██████╔╝    ╚██████╔╝██║  ██║██║  ██║██║     ██║  ██║██║  ██║██║  ██║╚██████╔╝
╚═╝     ╚═════╝ ╚═╝            ╚═╝    ╚═════╝      ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝     ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝ 
"@ -ForegroundColor Cyan

Write-Host "🚀 One-Command PDF to Knowledge Graph Pipeline" -ForegroundColor Cyan
Write-Host "==============================================" -ForegroundColor Cyan

# Check if API keys are provided
if (-not $env:GROQ_API_KEY -and -not $env:GRAPHRAG_API_KEY) {
    Write-Host "🔑 API Keys Setup" -ForegroundColor Yellow
    Write-Host "Please enter your API keys:" -ForegroundColor Blue
    
    $env:GROQ_API_KEY = Read-Host "Groq API Key"
    $env:GRAPHRAG_API_KEY = Read-Host "OpenAI API Key (for embeddings)"
}

# Check for PDF directory
$pdfDir = "./input"
if (-not (Test-Path $pdfDir)) {
    New-Item -ItemType Directory -Path $pdfDir -Force | Out-Null
}

$pdfFiles = Get-ChildItem -Path $pdfDir -Filter "*.pdf" -ErrorAction SilentlyContinue
if ($pdfFiles.Count -eq 0) {
    Write-Host "📄 PDF Setup" -ForegroundColor Yellow
    Write-Host "No PDF files found in ./input/ directory" -ForegroundColor Red
    Write-Host "Please add your PDF files to the ./input/ directory and run again" -ForegroundColor Blue
    Write-Host ""
    Write-Host "Example:" -ForegroundColor Cyan
    Write-Host "   copy `"C:\path\to\your\document.pdf`" .\input\"
    Write-Host "   .\run-graphrag.ps1"
    exit 1
}

Write-Host "✅ Found $($pdfFiles.Count) PDF file(s) in ./input/" -ForegroundColor Green

# Show what we're about to process
Write-Host "📋 PDF files to process:" -ForegroundColor Blue
$pdfFiles | Select-Object -First 5 | ForEach-Object { Write-Host "   📄 $($_.Name)" }

Write-Host ""
Write-Host "⚡ This will:" -ForegroundColor Yellow
Write-Host "   🔹 Start PDF processing service"
Write-Host "   🔹 Extract text from your PDFs"
Write-Host "   🔹 Generate knowledge graph with AI"
Write-Host "   🔹 Open interactive query interface"
Write-Host ""
Write-Host "⏳ Estimated time: 15-60 minutes (depending on PDF size)" -ForegroundColor Cyan
Write-Host ""

# Confirm before proceeding
$confirm = Read-Host "🚀 Ready to start? (y/N)"
if ($confirm -notmatch "^[Yy]$") {
    Write-Host "👋 Setup cancelled. Run again when ready!" -ForegroundColor Blue
    exit 0
}

Write-Host ""
Write-Host "🎬 Starting the pipeline..." -ForegroundColor Green

# Create .env file for docker-compose
@"
GROQ_API_KEY=$env:GROQ_API_KEY
GRAPHRAG_API_KEY=$env:GRAPHRAG_API_KEY
"@ | Out-File -FilePath ".env" -Encoding UTF8

# Check if Docker is running
try {
    docker version | Out-Null
    Write-Host "✅ Docker is running" -ForegroundColor Green
}
catch {
    Write-Host "❌ Docker is not running. Please start Docker Desktop and try again." -ForegroundColor Red
    exit 1
}

# Run the full pipeline using docker-compose
Write-Host "🐳 Building and starting containers..." -ForegroundColor Blue

try {
    # Build the image first
    docker-compose -f docker-compose.full.yml build --no-cache
    
    # Start the pipeline
    docker-compose -f docker-compose.full.yml up --abort-on-container-exit
    
    Write-Host "✨ Pipeline completed!" -ForegroundColor Green
    Write-Host "📊 Your knowledge graph data is preserved in Docker volume 'graphrag_output'" -ForegroundColor Cyan
}
catch {
    Write-Host "❌ Pipeline failed. Check the output above for details." -ForegroundColor Red
}
finally {
    # Cleanup
    Write-Host "🧹 Cleaning up containers..." -ForegroundColor Blue
    docker-compose -f docker-compose.full.yml down
}
