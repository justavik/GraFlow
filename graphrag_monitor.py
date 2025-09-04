#!/usr/bin/env python3
"""
GraphRAG Performance Monitor and Troubleshooter

This script helps monitor GraphRAG indexing performance and identify bottlenecks.
"""

import json
import time
import requests
from pathlib import Path
from datetime import datetime, timedelta
import subprocess
import sys
from typing import Optional

try:
    import psutil
except ImportError:
    print("⚠️ psutil not installed. Install with: pip install psutil")
    psutil = None

class GraphRAGMonitor:
    """Monitor GraphRAG performance and identify bottlenecks"""
    
    def __init__(self, graphrag_dir: str = "./graphrag_output"):
        self.graphrag_dir = Path(graphrag_dir)
        self.start_time = None
        self.api_call_count = 0
        self.last_api_check = None
    
    def check_openai_api_status(self, api_key: Optional[str] = None):
        """Check OpenAI API status and rate limits"""
        if not api_key:
            # Try to get from environment or settings
            env_file = self.graphrag_dir / ".env"
            if env_file.exists():
                env_content = env_file.read_text()
                for line in env_content.split('\n'):
                    if line.startswith('GRAPHRAG_API_KEY='):
                        api_key = line.split('=', 1)[1]
                        break
        
        if not api_key:
            print("⚠️ No API key found for status check")
            return None
        
        try:
            # Test API connectivity
            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }
            
            # Simple API call to check status
            response = requests.get(
                'https://api.openai.com/v1/models', 
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                print("✅ OpenAI API: Accessible")
                
                # Check rate limit headers
                if 'x-ratelimit-remaining-requests' in response.headers:
                    remaining = response.headers.get('x-ratelimit-remaining-requests')
                    reset_time = response.headers.get('x-ratelimit-reset-requests')
                    print(f"📊 Rate limit: {remaining} requests remaining")
                    if reset_time:
                        print(f"🔄 Rate limit resets: {reset_time}")
                
                return True
                
            elif response.status_code == 429:
                print("⚠️ OpenAI API: Rate limited!")
                retry_after = response.headers.get('retry-after', 'unknown')
                print(f"   Retry after: {retry_after} seconds")
                return False
                
            else:
                print(f"❌ OpenAI API: Error {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ OpenAI API check failed: {e}")
            return False
    
    def estimate_processing_time(self, input_size_chars: int):
        """Estimate processing time based on input size"""
        
        # Rough estimates based on typical GraphRAG performance
        chars_per_minute = 50_000  # Conservative estimate
        minutes_estimated = input_size_chars / chars_per_minute
        
        print(f"📊 PROCESSING TIME ESTIMATES:")
        print(f"   Input size: {input_size_chars:,} characters")
        print(f"   Estimated time: {minutes_estimated:.1f} minutes")
        
        if minutes_estimated > 30:
            print(f"⚠️ Large dataset! This will take {minutes_estimated/60:.1f} hours")
            print("💡 Consider:")
            print("   • Processing smaller chunks first")
            print("   • Using gpt-4o-mini instead of gpt-4-turbo")
            print("   • Reducing chunk overlap")
        
        return minutes_estimated
    
    def analyze_bottlenecks(self):
        """Analyze potential performance bottlenecks"""
        
        print("\n🔍 BOTTLENECK ANALYSIS:")
        print("="*50)
        
        # 1. API Rate Limits (Primary bottleneck)
        print("1️⃣ OpenAI API Rate Limits (MAIN BOTTLENECK)")
        print("   • GPT-4 models: ~500 requests/minute")
        print("   • Embedding models: ~3000 requests/minute") 
        print("   • Each document chunk = multiple API calls")
        print("   • Rate limiting causes delays between calls")
        
        # 2. Network latency
        print("\n2️⃣ Network Latency")
        print("   • Each API call has ~100-500ms latency")
        print("   • Hundreds/thousands of calls per document")
        print("   • Total latency = major time component")
        
        # 3. Local compute (minimal impact)
        print("\n3️⃣ Local Compute (MINIMAL IMPACT)")
        if psutil:
            cpu_count = psutil.cpu_count()
            memory = psutil.virtual_memory()
            print(f"   • CPU cores: {cpu_count}")
            print(f"   • RAM: {memory.total / (1024**3):.1f} GB")
        else:
            print("   • System info unavailable (install psutil)")
        print("   • Text processing is lightweight")
        print("   • GPU won't help (all work is API calls)")
        
        # 4. Model selection impact
        print("\n4️⃣ Model Selection Impact")
        print("   • gpt-4-turbo-preview: Slower, higher quality")
        print("   • gpt-4o-mini: 2-3x faster, good quality")
        print("   • text-embedding-3-small: Fast embeddings")
        
        print("\n💡 SPEED OPTIMIZATION RECOMMENDATIONS:")
        print("✅ Use gpt-4o-mini instead of gpt-4-turbo")
        print("✅ Reduce chunk_size (less text per API call)")
        print("✅ Reduce chunk_overlap")
        print("✅ Process smaller documents first")
        print("❌ GPU acceleration won't help")
        print("❌ More CPU cores won't help")
        print("❌ More RAM won't help")
        
    def monitor_indexing_process(self, max_duration_minutes: int = 60):
        """Monitor an active GraphRAG indexing process"""
        
        print(f"👀 Monitoring GraphRAG indexing (max {max_duration_minutes} minutes)")
        self.start_time = time.time()
        max_duration = max_duration_minutes * 60
        
        # Look for python processes running graphrag
        while time.time() - self.start_time < max_duration:
            current_time = time.time()
            elapsed = current_time - self.start_time
            
            # Check for GraphRAG processes
            graphrag_processes = []
            if psutil:
                for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'cpu_percent']):
                    try:
                        if proc.info['cmdline'] and any('graphrag' in arg for arg in proc.info['cmdline']):
                            graphrag_processes.append(proc.info)
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
            
            # Status update
            if graphrag_processes:
                print(f"🔄 {len(graphrag_processes)} GraphRAG processes running (elapsed: {elapsed/60:.1f}m)")
                for proc in graphrag_processes:
                    print(f"   PID {proc['pid']}: CPU {proc['cpu_percent']:.1f}%")
            else:
                print(f"ℹ️ No GraphRAG processes found (elapsed: {elapsed/60:.1f}m)")
            
            # Check output directory for progress
            output_dir = self.graphrag_dir / "output"
            if output_dir.exists():
                artifacts = list(output_dir.glob("**/*"))
                if artifacts:
                    latest_artifact = max(artifacts, key=lambda x: x.stat().st_mtime)
                    time_since_latest = current_time - latest_artifact.stat().st_mtime
                    print(f"📁 {len(artifacts)} output files, latest: {time_since_latest/60:.1f}m ago")
            
            # Check if we should continue
            if not graphrag_processes and elapsed > 300:  # 5 minutes
                print("✅ No active processes and sufficient time elapsed - likely completed")
                break
            
            time.sleep(30)  # Check every 30 seconds
        
        if time.time() - self.start_time >= max_duration:
            print(f"⏰ Monitoring stopped after {max_duration_minutes} minutes")


def main():
    """Main CLI interface"""
    import argparse
    
    parser = argparse.ArgumentParser(description="GraphRAG Performance Monitor")
    parser.add_argument("--graphrag-dir", default="./graphrag_output", help="GraphRAG project directory")
    parser.add_argument("--check-api", action="store_true", help="Check OpenAI API status")
    parser.add_argument("--analyze", action="store_true", help="Analyze performance bottlenecks")
    parser.add_argument("--monitor", action="store_true", help="Monitor active indexing process")
    parser.add_argument("--estimate", type=int, help="Estimate processing time for X characters")
    parser.add_argument("--max-time", type=int, default=60, help="Max monitoring time in minutes")
    
    args = parser.parse_args()
    
    monitor = GraphRAGMonitor(args.graphrag_dir)
    
    if args.check_api:
        monitor.check_openai_api_status()
    
    if args.analyze:
        monitor.analyze_bottlenecks()
    
    if args.estimate:
        monitor.estimate_processing_time(args.estimate)
    
    if args.monitor:
        monitor.monitor_indexing_process(args.max_time)
    
    if not any([args.check_api, args.analyze, args.monitor, args.estimate]):
        # Default: run all checks
        print("🔍 Running comprehensive GraphRAG performance analysis...\n")
        monitor.check_openai_api_status()
        print()
        monitor.analyze_bottlenecks()
        
        # Check for input files to estimate processing time
        input_dir = Path(args.graphrag_dir) / "input"
        if input_dir.exists():
            input_files = list(input_dir.glob("*.txt"))
            if input_files:
                total_chars = sum(
                    len(f.read_text(encoding='utf-8', errors='ignore')) 
                    for f in input_files
                )
                print(f"\n📊 Found {len(input_files)} input files with {total_chars:,} characters")
                monitor.estimate_processing_time(total_chars)


if __name__ == "__main__":
    main()
