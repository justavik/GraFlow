# Professional Demo Setup

This folder contains a persistent Docker setup designed for demonstrations and presentations where you need reliable, repeatable performance.

## 🎯 Why Use This Demo Setup?

- ✅ **One-time build**: Containers persist between sessions (no 800-second rebuilds)
- ✅ **Professional presentation**: Clean interface for demos
- ✅ **Quick PDF swapping**: Add new PDFs without rebuilding
- ✅ **Reliable performance**: Containers stay ready for instant queries

## 🚀 Quick Demo Setup

### First Time Setup (5-10 minutes)
```powershell
cd demo
.\demo-setup.ps1
```

This builds persistent containers that stay available until you explicitly remove them.

### For Each Demo (30 seconds)
1. Add new PDF to `../input/` folder
2. Connect to demo environment:
   ```bash
   docker exec -it graphrag-demo bash
   ```
3. Pipeline processes automatically
4. Use query interface:
   ```bash
   local What are the main topics?
   global What is the overall theme?
   exit
   ```

## 📋 Demo Commands Reference

### Container Management
```bash
# Check demo container status
docker ps --filter "name=demo"

# Start existing demo containers
docker-compose -f docker-compose.persistent.yml up -d

# Stop containers (keeps data)
docker-compose -f docker-compose.persistent.yml stop

# Remove everything (including data)
docker-compose -f docker-compose.persistent.yml down -v
```

### Query Interface
Once connected to the pipeline:
```bash
# Search specific entities and relationships
local What are the main AWS storage services?

# Search broad themes and summaries  
global What is the overall architecture approach?

# Get help
help

# Exit
exit
```

## 🎓 Perfect for Professor Presentations

1. **Setup Phase** (do once):
   - Run `.\demo-setup.ps1` 
   - Wait 5-10 minutes for container build
   - Test with sample PDF

2. **Demo Phase** (repeat for each new PDF):
   - Add PDF to input folder
   - Run: `docker exec -it graphrag-demo bash`
   - Show real-time processing
   - Demonstrate query capabilities
   - Clean exit

3. **Benefits**:
   - No waiting during presentation
   - Professional, consistent interface
   - Easy to switch between PDFs
   - Reliable performance

## 🔧 Files in This Directory

- `demo-setup.ps1` - One-time container setup script
- `docker-compose.persistent.yml` - Persistent container configuration
- `Dockerfile.demo` - Optimized demo container
- `docker-entrypoint-demo.sh` - Clean demo interface script

## 🚨 Important Notes

- Containers persist until manually removed
- Uses separate volumes (`demo_*`) to avoid conflicts
- Designed for presentation environments
- Optimized for quick PDF processing and querying
