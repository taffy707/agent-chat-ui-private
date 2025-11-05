# Quick Start with Docker ✅ READY!

This is the **fastest way** to get the Agent Chat UI with Document Manager running.

**Status**: ✅ Docker setup is complete and tested!

## Prerequisites

- ✅ Docker Desktop installed and running
- ✅ Node.js and pnpm installed
- ✅ Local PostgreSQL running (already configured)

## Setup (2 steps, 1 minute)

### Step 1: Start the Document API Backend (Docker)

```bash
cd document-api
./docker-start.sh
```

Wait for it to say "✅ Document API is running!" (~30 seconds)

### Step 2: Start the Frontend

```bash
# In a new terminal
cd /Users/tafadzwabwakura/agent-chat-ui
pnpm dev
```

## Done! 🎉

Open your browser: **http://localhost:3000**

- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Frontend**: http://localhost:3000

## Using the Document Manager

1. Start a chat (type any message)
2. Click the **document icon** (📄) in the top-right toolbar
3. Create a collection
4. Upload files (PDF, DOCX, TXT, HTML)
5. Done!

## Stopping

### Stop Frontend

Press `Ctrl+C` in the terminal running `pnpm dev`

### Stop Backend (Docker)

```bash
cd document-api
./docker-stop.sh
```

## Next Time

Just run these two commands:

```bash
# Terminal 1: Start backend
cd document-api && ./docker-start.sh

# Terminal 2: Start frontend
cd /Users/tafadzwabwakura/agent-chat-ui && pnpm dev
```

## Troubleshooting

**Port 8000 already in use?**

```bash
# Find and kill the process
lsof -i :8000
kill -9 <PID>
```

**Frontend not connecting to backend?**

Check `.env` has:

```
NEXT_PUBLIC_DOCUMENT_API_URL=http://localhost:8000
```

**Docker not starting?**

Make sure Docker Desktop is running, then:

```bash
cd document-api
docker-compose logs -f
```

## More Documentation

- **Docker Setup**: [document-api/DOCKER_SETUP.md](document-api/DOCKER_SETUP.md)
- **Document Manager Integration**: [DOCUMENT_MANAGER_INTEGRATION.md](DOCUMENT_MANAGER_INTEGRATION.md)
- **Detailed Guide**: [QUICKSTART_DOCUMENT_MANAGER.md](QUICKSTART_DOCUMENT_MANAGER.md)
