#!/usr/bin/env python3
"""
PDF to GraphRAG Pipeline Orchestrator

This module coordinates the end-to-end processing pipeline from PDF documents
to GraphRAG knowledge graphs and inference capabilities.
"""

import asyncio
import io
import json
import logging
import os
import re
import shutil
import subprocess
import sys
import threading
import time
import zipfile
from pathlib import Path
from queue import Queue, Empty
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

import requests
import yaml

# Load environment variables from .env file
try:
    from dotenv import load_dotenv  
    load_dotenv()
    print("Loaded environment variables from .env file")
except ImportError:
    print("python-dotenv not installed, using system environment variables")

# Pipeline configuration
@dataclass
class PipelineConfig:
    # Stirling PDF settings
    stirling_url: str = "http://localhost:8081"
    
    # Input/Output paths
    input_pdf_dir: str = "./input"
    processed_text_dir: str = "./processed_text"
    graphrag_input_dir: str = "./graphrag_input"
    graphrag_output_dir: str = "./graphrag_output"
    
    # OCR settings
    ocr_languages: Optional[List[str]] = None
    use_ocr: bool = True
    clean_text: bool = True
    
    def __post_init__(self):
        if self.ocr_languages is None:
            self.ocr_languages = ["eng"]


class PDFProcessor:
    """Handles PDF processing via Stirling PDF API"""
    
    def __init__(self, stirling_url: str):
        self.stirling_url = stirling_url
        self.session = requests.Session()
    
    def extract_text(self, pdf_path: Path, output_dir: Path) -> Path:
        """Extract text from PDF using Stirling PDF API"""
        try:
            # First try direct text extraction
            return self._extract_direct_text(pdf_path, output_dir)
        except Exception as e:
            logging.warning(f"Direct text extraction failed: {e}")
            # Fall back to OCR
            return self._extract_with_ocr(pdf_path, output_dir)
    
    def _extract_direct_text(self, pdf_path: Path, output_dir: Path) -> Path:
        """Extract text directly from PDF"""
        url = f"{self.stirling_url}/api/v1/convert/pdf/text"
        
        with open(pdf_path, 'rb') as f:
            files = {
                'fileInput': (pdf_path.name, f, 'application/pdf')
            }
            data = {
                'outputFormat': 'txt'
            }
            
            response = self.session.post(url, files=files, data=data)
            response.raise_for_status()
            
            # Save extracted text
            output_path = output_dir / f"{pdf_path.stem}.txt"
            output_path.write_bytes(response.content)
            
            logging.info(f"Extracted text from {pdf_path.name} -> {output_path}")
            return output_path
    
    def _extract_with_ocr(self, pdf_path: Path, output_dir: Path) -> Path:
        """Extract text using OCR"""
        url = f"{self.stirling_url}/api/v1/misc/ocr-pdf"
        
        with open(pdf_path, 'rb') as f:
            files = {
                'fileInput': (pdf_path.name, f, 'application/pdf')
            }
            data = {
                'languages': ['eng'],
                'sidecar': True,  # Get text file alongside PDF
                'ocrType': 'force-ocr',
                'ocrRenderType': 'sandwich',
                'clean': True,
                'cleanFinal': True
            }
            
            response = self.session.post(url, files=files, data=data)
            response.raise_for_status()
            
            # Handle zip response (PDF + text file)
            if response.headers.get('content-type') == 'application/octet-stream':
                
                zip_buffer = io.BytesIO(response.content)
                with zipfile.ZipFile(zip_buffer, 'r') as zip_file:
                    # Extract text file from zip
                    for file_info in zip_file.filelist:
                        if file_info.filename.endswith('.txt'):
                            text_content = zip_file.read(file_info)
                            output_path = output_dir / f"{pdf_path.stem}_ocr.txt"
                            output_path.write_bytes(text_content)
                            
                            logging.info(f"OCR extracted text from {pdf_path.name} -> {output_path}")
                            return output_path
            
            # Fallback: save as text directly
            output_path = output_dir / f"{pdf_path.stem}_ocr.txt"
            output_path.write_bytes(response.content)
            return output_path


class TextProcessor:
    """Processes extracted text for GraphRAG ingestion"""
    
    @staticmethod
    def clean_text(text: str) -> str:
        """Clean and normalize extracted text"""
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove page numbers and headers/footers (basic patterns)
        text = re.sub(r'\n\d+\s*\n', '\n', text)
        text = re.sub(r'\n\s*Page \d+.*?\n', '\n', text, flags=re.IGNORECASE)
        
        # Normalize line breaks
        text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)
        
        # Remove leading/trailing whitespace
        text = text.strip()
        
        return text
    
    def process_text_file(self, input_path: Path, output_dir: Path) -> Path:
        """Process a single text file for GraphRAG"""
        
        # Read and clean text
        text = input_path.read_text(encoding='utf-8', errors='ignore')
        cleaned_text = self.clean_text(text)
        
        # Create output file
        output_path = output_dir / f"{input_path.stem}_processed.txt"
        output_path.write_text(cleaned_text, encoding='utf-8')
        
        logging.info(f"Processed text file: {input_path} -> {output_path}")
        return output_path


class GraphRAGManager:
    """Manages GraphRAG indexing and querying"""
    
    def __init__(self, config: PipelineConfig):
        self.config = config
        self.graphrag_dir = Path(config.graphrag_output_dir)
        self.input_dir = Path(config.graphrag_input_dir)
    
    def setup_graphrag_project(self, use_fast_settings: bool = True):
        """Initialize GraphRAG project structure"""
        
        # Create directories
        self.graphrag_dir.mkdir(parents=True, exist_ok=True)
        self.input_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy optimized settings if requested
        if use_fast_settings:
            fast_settings = Path("settings_fast.yaml")
            if fast_settings.exists():
                target_settings = self.graphrag_dir / "settings.yaml"
                shutil.copy2(fast_settings, target_settings)
                logging.info(f"Using optimized fast settings: {target_settings}")
        
        logging.info(f"GraphRAG project directories created at {self.graphrag_dir}")
        # Note: GraphRAG init will create settings.yaml automatically if not present
    
    def copy_processed_texts(self, text_files: List[Path]):
        """Copy processed text files to GraphRAG input directory"""
        
        # GraphRAG expects input files in the root input directory
        for text_file in text_files:
            dest_path = self.graphrag_dir / "input" / text_file.name
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(text_file, dest_path)
            logging.info(f"Copied {text_file} -> {dest_path}")
    
    async def run_indexing(self):
        """Run GraphRAG indexing process with comprehensive monitoring"""
        
        # Check if initialization is needed BEFORE changing directories
        settings_file = self.graphrag_dir / "settings.yaml"
        need_init = not settings_file.exists()
        
        # Change to GraphRAG directory
        original_cwd = os.getcwd()
        os.chdir(self.graphrag_dir)
        
        def read_output(pipe, queue, prefix):
            """Read subprocess output in a separate thread"""
            try:
                for line in iter(pipe.readline, ''):
                    if line:
                        queue.put((prefix, line.strip()))
                pipe.close()
            except Exception as e:
                queue.put((prefix, f"ERROR reading output: {e}"))
        
        def monitor_progress(process, stdout_queue, stderr_queue, start_time):
            """Monitor and log progress with timeout detection"""
            last_output_time = time.time()
            output_timeout = 300  # 5 minutes without output = timeout
            heartbeat_interval = 30  # Show heartbeat every 30 seconds
            last_heartbeat = time.time()
            
            while process.poll() is None:
                current_time = time.time()
                
                # Check for stdout output
                try:
                    prefix, line = stdout_queue.get_nowait()
                    logging.info(f"[{prefix}] {line}")
                    last_output_time = current_time
                    
                    # Detect specific progress indicators
                    if any(keyword in line.lower() for keyword in [
                        'embedding', 'chunk', 'entity', 'relationship', 'community',
                        'processing', 'stage', 'step', 'progress', 'complete'
                    ]):
                        print(f"🔄 PROGRESS: {line}")
                    
                except Empty:
                    pass
                
                # Check for stderr output
                try:
                    prefix, line = stderr_queue.get_nowait()
                    logging.warning(f"[{prefix}] {line}")
                    last_output_time = current_time
                    
                    # Highlight errors and warnings
                    if any(keyword in line.lower() for keyword in ['error', 'fail', 'exception']):
                        print(f"❌ ERROR: {line}")
                    elif any(keyword in line.lower() for keyword in ['warning', 'warn']):
                        print(f"⚠️ WARNING: {line}")
                    
                except Empty:
                    pass
                
                # Heartbeat to show process is alive
                if current_time - last_heartbeat >= heartbeat_interval:
                    elapsed = int(current_time - start_time)
                    print(f"💓 Process running... Elapsed: {elapsed//60}m {elapsed%60}s")
                    last_heartbeat = current_time
                
                # Timeout detection
                if current_time - last_output_time > output_timeout:
                    logging.error(f"No output for {output_timeout} seconds, process may be hung")
                    print(f"⏰ WARNING: No output for {output_timeout//60} minutes. Process may be hung.")
                    print("Consider terminating if this continues much longer.")
                
                time.sleep(1)  # Check every second
        
        try:
            start_time = time.time()
            
            # Use python -m graphrag to ensure we use the correct environment
            # First, initialize GraphRAG project if needed
            if need_init:
                print("🚀 Initializing GraphRAG project...")
                logging.info("Initializing GraphRAG project")
                cmd = [sys.executable, "-m", "graphrag", "init", "--root", "."]
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
                
                if result.returncode != 0:
                    error_msg = f"GraphRAG init failed (exit code {result.returncode})"
                    logging.error(f"{error_msg}: {result.stderr}")
                    print(f"❌ {error_msg}")
                    print(f"STDERR: {result.stderr}")
                    print(f"STDOUT: {result.stdout}")
                    raise RuntimeError(f"{error_msg}: {result.stderr}")
                
                print("✅ GraphRAG project initialized successfully")
                logging.info("GraphRAG project initialized")
            else:
                print("ℹ️ GraphRAG project already initialized, skipping init")
                logging.info("GraphRAG project already initialized, skipping init")
            
            # Check input files
            input_dir = self.graphrag_dir / "input"
            input_files = list(input_dir.glob("*.txt")) if input_dir.exists() else []
            total_size = sum(f.stat().st_size for f in input_files) if input_files else 0
            
            print(f"📁 Input files: {len(input_files)} files, {total_size:,} bytes total")
            if total_size > 1_000_000:  # > 1MB
                print(f"📊 Large dataset detected ({total_size/1_000_000:.1f}MB) - this will take time")
                print("💡 Performance factors:")
                print("   • OpenAI API rate limits (main bottleneck)")
                print("   • Network latency to OpenAI servers")
                print("   • Text chunking and embedding generation")
                print("   • GPU won't help much - it's mostly API-bound")
            
            # Run actual indexing with live monitoring
            print("🔄 Starting GraphRAG indexing with live monitoring...")
            print("💡 This process is primarily limited by OpenAI API calls, not local compute")
            logging.info("Starting GraphRAG indexing")
            
            cmd = [sys.executable, "-m", "graphrag", "index", "--root", ".", "--verbose"]
            
            # Start process with pipes for real-time output
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            # Setup output monitoring
            stdout_queue = Queue()
            stderr_queue = Queue()
            
            stdout_thread = threading.Thread(
                target=read_output, 
                args=(process.stdout, stdout_queue, "STDOUT")
            )
            stderr_thread = threading.Thread(
                target=read_output, 
                args=(process.stderr, stderr_queue, "STDERR")
            )
            
            stdout_thread.daemon = True
            stderr_thread.daemon = True
            stdout_thread.start()
            stderr_thread.start()
            
            # Monitor progress
            try:
                monitor_progress(process, stdout_queue, stderr_queue, start_time)
                
                # Wait for completion
                return_code = process.wait()
                
                # Collect any remaining output
                time.sleep(2)  # Allow threads to finish
                while True:
                    try:
                        prefix, line = stdout_queue.get_nowait()
                        logging.info(f"[{prefix}] {line}")
                    except Empty:
                        break
                
                while True:
                    try:
                        prefix, line = stderr_queue.get_nowait()
                        logging.warning(f"[{prefix}] {line}")
                    except Empty:
                        break
                
                elapsed = int(time.time() - start_time)
                
                if return_code != 0:
                    error_msg = f"GraphRAG indexing failed (exit code {return_code})"
                    logging.error(f"{error_msg} after {elapsed}s")
                    print(f"❌ {error_msg} after {elapsed//60}m {elapsed%60}s")
                    
                    # Try to get more error details
                    try:
                        log_files = list((self.graphrag_dir / "output").glob("**/*.log"))
                        if log_files:
                            latest_log = max(log_files, key=lambda x: x.stat().st_mtime)
                            print(f"📋 Check log file for details: {latest_log}")
                            tail_content = latest_log.read_text()[-2000:]  # Last 2000 chars
                            print(f"Last log entries:\n{tail_content}")
                    except Exception as e:
                        print(f"Could not read log files: {e}")
                    
                    raise RuntimeError(f"{error_msg}")
                
                print(f"✅ GraphRAG indexing completed successfully in {elapsed//60}m {elapsed%60}s")
                logging.info(f"GraphRAG indexing completed successfully in {elapsed}s")
                
                # Show output summary
                output_dir = self.graphrag_dir / "output"
                if output_dir.exists():
                    artifacts = list(output_dir.glob("**/*"))
                    print(f"📊 Generated {len(artifacts)} output artifacts in {output_dir}")
                
            except KeyboardInterrupt:
                print("\n🛑 Indexing interrupted by user")
                process.terminate()
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill()
                raise
            
        except subprocess.TimeoutExpired:
            print("⏰ GraphRAG initialization timed out")
            raise RuntimeError("GraphRAG initialization timed out after 2 minutes")
        finally:
            os.chdir(original_cwd)
    
    async def query(self, question: str, query_type: str = "global") -> str:
        """Query the GraphRAG knowledge graph"""
        
        original_cwd = os.getcwd()
        os.chdir(self.graphrag_dir)
        
        try:
            cmd = [
                sys.executable, "-m", "graphrag", "query",
                "--root", ".",
                "--method", query_type,
                "--query", question
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                logging.error(f"GraphRAG query failed: {result.stderr}")
                raise RuntimeError(f"Query failed: {result.stderr}")
            
            return result.stdout.strip()
            
        finally:
            os.chdir(original_cwd)


class PipelineOrchestrator:
    """Main pipeline orchestrator"""
    
    def __init__(self, config: PipelineConfig):
        self.config = config
        self.pdf_processor = PDFProcessor(config.stirling_url)
        self.text_processor = TextProcessor()
        self.graphrag_manager = GraphRAGManager(config)
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
    
    async def run_pipeline(self, pdf_files: List[Path]) -> Dict:
        """Run the complete pipeline with comprehensive monitoring"""
        
        start_time = datetime.now()
        results = {
            'start_time': start_time.isoformat(),
            'processed_files': [],
            'errors': [],
            'pipeline_stages': []
        }
        
        def log_stage(stage_name: str, status: str, details: str = ""):
            """Log pipeline stage with status"""
            stage_info = {
                'stage': stage_name,
                'status': status,
                'timestamp': datetime.now().isoformat(),
                'details': details
            }
            results['pipeline_stages'].append(stage_info)
            
            status_emoji = {
                'starting': '🚀',
                'running': '🔄', 
                'completed': '✅',
                'failed': '❌',
                'warning': '⚠️'
            }.get(status, 'ℹ️')
            
            print(f"{status_emoji} {stage_name}: {status.upper()}")
            if details:
                print(f"   {details}")
        
        try:
            # Create output directories
            log_stage("Directory Setup", "starting")
            Path(self.config.processed_text_dir).mkdir(parents=True, exist_ok=True)
            log_stage("Directory Setup", "completed", f"Created {self.config.processed_text_dir}")
            
            total_files = len(pdf_files)
            total_size = sum(f.stat().st_size for f in pdf_files if f.exists())
            log_stage("Pipeline Initialization", "starting", 
                     f"{total_files} PDF files, {total_size:,} bytes total")
            
            # Validate Stirling PDF connection
            try:
                # Try to access the main page instead of the non-existent /api/v1/info endpoint
                response = self.pdf_processor.session.get(f"{self.config.stirling_url}/", timeout=10)
                if response.status_code == 200:
                    log_stage("Stirling PDF Connection", "completed", "API accessible")
                else:
                    log_stage("Stirling PDF Connection", "warning", f"API returned {response.status_code}")
            except Exception as e:
                log_stage("Stirling PDF Connection", "failed", f"Cannot reach API: {e}")
                print("💡 Make sure Stirling PDF Docker container is running: docker-compose up -d")
                raise
            
            logging.info(f"Starting pipeline for {total_files} PDF files ({total_size:,} bytes)")
            
            # Step 1: Process PDFs to extract text
            log_stage("PDF Text Extraction", "starting")
            processed_texts = []
            
            for i, pdf_file in enumerate(pdf_files, 1):
                try:
                    print(f"📄 Processing file {i}/{total_files}: {pdf_file.name}")
                    file_size = pdf_file.stat().st_size
                    print(f"   Size: {file_size:,} bytes")
                    
                    text_file = self.pdf_processor.extract_text(
                        pdf_file, 
                        Path(self.config.processed_text_dir)
                    )
                    
                    # Validate extracted text
                    extracted_size = text_file.stat().st_size
                    extracted_text = text_file.read_text(encoding='utf-8', errors='ignore')
                    char_count = len(extracted_text)
                    
                    print(f"   ✅ Extracted: {extracted_size:,} bytes, {char_count:,} characters")
                    
                    if char_count < 100:
                        log_stage("Text Extraction Validation", "warning", 
                                f"{pdf_file.name}: Only {char_count} characters extracted")
                    
                    # Process text for GraphRAG
                    cleaned_text_file = self.text_processor.process_text_file(
                        text_file,
                        Path(self.config.processed_text_dir)
                    )
                    
                    # Validate processed text
                    cleaned_text = cleaned_text_file.read_text(encoding='utf-8', errors='ignore')
                    cleaned_char_count = len(cleaned_text)
                    
                    print(f"   🧹 Cleaned: {cleaned_char_count:,} characters")
                    
                    processed_texts.append(cleaned_text_file)
                    results['processed_files'].append({
                        'file': str(pdf_file),
                        'original_size': file_size,
                        'extracted_chars': char_count,
                        'cleaned_chars': cleaned_char_count
                    })
                    
                except Exception as e:
                    error_msg = f"Failed to process {pdf_file}: {e}"
                    logging.error(error_msg)
                    results['errors'].append(error_msg)
                    log_stage("PDF Processing", "failed", f"{pdf_file.name}: {e}")
                    print(f"❌ Error processing {pdf_file.name}: {e}")
            
            if not processed_texts:
                raise RuntimeError("No PDF files were successfully processed")
            
            total_processed_chars = sum(
                len(f.read_text(encoding='utf-8', errors='ignore')) 
                for f in processed_texts
            )
            log_stage("PDF Text Extraction", "completed", 
                     f"{len(processed_texts)} files, {total_processed_chars:,} total characters")
            
            # Step 2: Setup GraphRAG
            log_stage("GraphRAG Setup", "starting")
            self.graphrag_manager.setup_graphrag_project()
            self.graphrag_manager.copy_processed_texts(processed_texts)
            
            # Validate GraphRAG input
            input_files = list((self.graphrag_manager.graphrag_dir / "input").glob("*.txt"))
            log_stage("GraphRAG Setup", "completed", f"{len(input_files)} files copied to GraphRAG input")
            
            # Step 3: Run GraphRAG indexing
            log_stage("GraphRAG Indexing", "starting")
            
            await self.graphrag_manager.run_indexing()
            log_stage("GraphRAG Indexing", "completed")
            
            # Pipeline completion
            end_time = datetime.now()
            duration = end_time - start_time
            results['end_time'] = end_time.isoformat()
            results['duration'] = str(duration)
            results['status'] = 'completed'
            
            print("\n" + "="*60)
            print("🎉 PIPELINE COMPLETED SUCCESSFULLY!")
            print("="*60)
            print(f"⏱️ Total time: {duration}")
            print(f"📊 Processed: {len(processed_texts)} files, {total_processed_chars:,} characters")
            print(f"🗂️ Output: {self.graphrag_manager.graphrag_dir}")
            print("="*60)
            
            logging.info(f"Pipeline completed successfully in {duration}")
            
        except Exception as e:
            results['status'] = 'failed'
            results['error'] = str(e)
            end_time = datetime.now()
            results['end_time'] = end_time.isoformat()
            results['duration'] = str(end_time - start_time)
            
            log_stage("Pipeline", "failed", str(e))
            logging.error(f"Pipeline failed: {e}")
            
            print("\n" + "="*60)
            print("❌ PIPELINE FAILED")
            print("="*60)
            print(f"Error: {e}")
            print(f"Duration before failure: {end_time - start_time}")
            print("Check logs above for detailed error information")
            print("="*60)
            raise
        
        return results
    
    async def query_knowledge_graph(self, question: str, query_type: str = "global") -> str:
        """Query the generated knowledge graph"""
        logging.info(f"Querying knowledge graph: {question}")
        answer = await self.graphrag_manager.query(question, query_type)
        logging.info("Query completed")
        return answer


async def main():
    """Main entry point"""
    
    # Configuration
    config = PipelineConfig(
        input_pdf_dir="./input",
        processed_text_dir="./processed_text",
        graphrag_input_dir="./graphrag_input",
        graphrag_output_dir="./graphrag_output"
    )
    
    # Initialize pipeline
    pipeline = PipelineOrchestrator(config)
    
    # Find PDF files
    input_dir = Path(config.input_pdf_dir)
    pdf_files = list(input_dir.glob("*.pdf"))
    
    if not pdf_files:
        # Use the aws_book.pdf from current directory
        aws_book = Path("aws_book.pdf")
        if aws_book.exists():
            pdf_files = [aws_book]
        else:
            print("No PDF files found. Please place PDF files in the input directory or ensure aws_book.pdf exists.")
            return
    
    try:
        # Run pipeline
        results = await pipeline.run_pipeline(pdf_files)
        
        # Save results
        results_file = Path("pipeline_results.json")
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"Pipeline completed! Results saved to {results_file}")
        
        # Interactive query loop
        # print("\nKnowledge graph is ready! You can now ask questions.")
        # print("Type 'quit' to exit, 'local:' prefix for local queries")
        
        # while True:
        #     question = input("\nEnter your question: ").strip()
            
        #     if question.lower() == 'quit':
        #         break
            
        #     if question.startswith('local:'):
        #         query_type = 'local'
        #         question = question[6:].strip()
        #     else:
        #         query_type = 'global'
            
        #     try:
        #         answer = await pipeline.query_knowledge_graph(question, query_type)
        #         print(f"\nAnswer ({query_type} search):")
        #         print(answer)
        #     except Exception as e:
        #         print(f"Query failed: {e}")
    
    except Exception as e:
        print(f"Pipeline failed: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    import asyncio
    sys.exit(asyncio.run(main()))
