# Quick Demo Commands

## One-Time Setup (builds persistent containers)
```powershell
.\demo-setup.ps1
```

## Connect to Demo Pipeline
```bash
docker exec -it graphrag-demo bash
```

## Manual Container Management
```bash
# Start existing demo containers
docker-compose -f docker-compose.persistent.yml up -d

# Stop demo containers (keeps data)
docker-compose -f docker-compose.persistent.yml stop

# Remove everything (including data)
docker-compose -f docker-compose.persistent.yml down -v

# Check status
docker ps --filter "name=demo"
```

## Query Interface Commands
Once connected to the container:
```bash
# Local search (specific entities/relationships)
local What are the main AWS storage services?

# Global search (broad themes/summaries) 
global What is the overall architecture approach recommended?

# Exit
exit
```

## Demo Flow for Professor
1. Run `.\demo-setup.ps1` (one-time, 5-10 minutes)
2. Add new PDF to `.\input\` folder
3. Run: `docker exec -it graphrag-demo bash`
4. Pipeline processes automatically
5. Use query interface: `local` or `global` commands
6. Show real-time AI responses

## Benefits
- ✅ Containers persist between demos
- ✅ No rebuild time for new PDFs
- ✅ Clean query interface
- ✅ Professional presentation flow
