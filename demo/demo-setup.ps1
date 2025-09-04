#!/usr/bin/env pwsh

Write-Host @"
██████╗ ███████╗███╗   ███╗ ██████╗     ██████╗ ██╗██████╗ ███████╗██╗     ██╗███╗   ██╗███████╗
██╔══██╗██╔════╝████╗ ████║██╔═══██╗    ██╔══██╗██║██╔══██╗██╔════╝██║     ██║████╗  ██║██╔════╝
██║  ██║█████╗  ██╔████╔██║██║   ██║    ██████╔╝██║██████╔╝█████╗  ██║     ██║██╔██╗ ██║█████╗  
██║  ██║██╔══╝  ██║╚██╔╝██║██║   ██║    ██╔═══╝ ██║██╔═══╝ ██╔══╝  ██║     ██║██║╚██╗██║██╔══╝  
██████╔╝███████╗██║ ╚═╝ ██║╚██████╔╝    ██║     ██║██║     ███████╗███████╗██║██║ ╚████║███████╗
╚═════╝ ╚══════╝╚═╝     ╚═╝ ╚═════╝     ╚═╝     ╚═╝╚═╝     ╚══════╝╚══════╝╚═╝╚═╝  ╚═══╝╚══════╝
🎯 Persistent Demo Pipeline - Build Once, Use Many Times!
"@ -ForegroundColor Cyan

Write-Host "🔧 Demo Setup (One-time build, persistent containers)" -ForegroundColor Yellow
Write-Host "====================================================" -ForegroundColor Yellow

# Check Docker
try {
    docker info | Out-Null
    Write-Host "✅ Docker is running" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker is not running. Please start Docker Desktop." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Get API keys
Write-Host "`n🔑 API Configuration" -ForegroundColor Yellow
$groqKey = Read-Host "Groq API Key"
$openaiKey = Read-Host "OpenAI API Key (for embeddings)"

if ([string]::IsNullOrWhiteSpace($groqKey) -or [string]::IsNullOrWhiteSpace($openaiKey)) {
    Write-Host "❌ Both API keys are required" -ForegroundColor Red
    exit 1
}

# Set environment variables
$env:GROQ_API_KEY = $groqKey
$env:OPENAI_API_KEY = $openaiKey

# Check for PDFs
$pdfFiles = Get-ChildItem -Path ".\input" -Filter "*.pdf" -ErrorAction SilentlyContinue
if (-not $pdfFiles) {
    Write-Host "`n❌ No PDF files found in .\input\" -ForegroundColor Red
    Write-Host "Please add your PDF files to the input directory first." -ForegroundColor Yellow
    Write-Host "Example: copy 'C:\path\to\document.pdf' .\input\" -ForegroundColor Gray
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "`n✅ Found $($pdfFiles.Count) PDF file(s):" -ForegroundColor Green
foreach ($pdf in $pdfFiles) {
    Write-Host "   📄 $($pdf.Name)" -ForegroundColor Gray
}

# Check if containers exist
$existingContainer = docker ps -a --filter "name=graphrag-demo" --format "{{.Names}}" 2>$null
$existingPdfContainer = docker ps -a --filter "name=stirling-pdf-demo" --format "{{.Names}}" 2>$null

if ($existingContainer -eq "graphrag-demo" -and $existingPdfContainer -eq "stirling-pdf-demo") {
    Write-Host "`n🔄 Found existing demo containers" -ForegroundColor Yellow
    $restart = Read-Host "Restart existing containers? (y/N)"
    
    if ($restart -eq 'y' -or $restart -eq 'Y') {
        Write-Host "🔄 Restarting containers..." -ForegroundColor Yellow
        docker-compose -f docker-compose.persistent.yml down 2>$null
        Start-Sleep 2
        docker-compose -f docker-compose.persistent.yml up -d
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Containers restarted!" -ForegroundColor Green
            Write-Host "`n🚀 Connect to demo:" -ForegroundColor Cyan
            Write-Host "   docker exec -it graphrag-demo bash" -ForegroundColor White
        } else {
            Write-Host "❌ Failed to restart containers" -ForegroundColor Red
        }
    } else {
        Write-Host "💡 To manually connect: docker exec -it graphrag-demo bash" -ForegroundColor Gray
    }
} else {
    Write-Host "`n🏗️  Building demo environment (this may take a few minutes)..." -ForegroundColor Yellow
    
    # Build and start
    docker-compose -f docker-compose.persistent.yml up --build -d
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Demo environment ready!" -ForegroundColor Green
        Write-Host "`n🎯 Next Steps:" -ForegroundColor Cyan
        Write-Host "1. Connect to pipeline: docker exec -it graphrag-demo bash" -ForegroundColor White
        Write-Host "2. Pipeline will process your PDFs automatically" -ForegroundColor White
        Write-Host "3. Use the interactive query interface" -ForegroundColor White
        Write-Host "`nDemo containers will persist until you run:" -ForegroundColor Gray
        Write-Host "   docker-compose -f docker-compose.persistent.yml down" -ForegroundColor Gray
    } else {
        Write-Host "❌ Failed to build demo environment" -ForegroundColor Red
    }
}

Write-Host "`n📊 Container Status:" -ForegroundColor Yellow
docker ps --filter "name=graphrag-demo" --filter "name=stirling-pdf-demo" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

Read-Host "`nPress Enter to exit"
