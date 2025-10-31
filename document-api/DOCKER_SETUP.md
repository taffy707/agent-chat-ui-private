# Docker Setup Guide for Document API

This guide shows you how to run the Document Upload API using Docker, making it super easy to start and stop the backend.

## Prerequisites

- Docker Desktop installed and running
- That's it! No Python, PostgreSQL, or other dependencies needed.

## Quick Start (30 seconds)

### Start the API

```bash
cd document-api
./docker-start.sh
```

That's it! The API will be running at **http://localhost:8000**

### Stop the API

```bash
./docker-stop.sh
```

## What Gets Started

When you run `./docker-start.sh`, Docker Compose will:

1. **Start PostgreSQL database** (in a container)
   - Port: 5433 (mapped to avoid conflicts with local PostgreSQL)
   - Data is persisted in a Docker volume

2. **Build and start the Document API** (in a container)
   - Port: 8000
   - Automatically connects to the PostgreSQL container
   - Includes all dependencies

## Manual Docker Commands

If you prefer manual control:

### Start everything

```bash
docker-compose up -d --build
```

### Stop everything

```bash
docker-compose down
```

### View logs

```bash
# All services
docker-compose logs -f

# Just the API
docker-compose logs -f api

# Just the database
docker-compose logs -f postgres
```

### Rebuild after code changes

```bash
docker-compose up -d --build
```

### Stop and remove all data (including database)

```bash
docker-compose down -v
```

## Configuration

### Environment Variables

Edit `.env.docker` to configure:

```env
GCP_PROJECT_ID=your-project-id
VERTEX_AI_DATA_STORE_ID=your-datastore-id
VERTEX_AI_LOCATION=global
GCS_BUCKET_NAME=your-bucket-name
```

### Google Cloud Credentials

If you need to use Google Cloud credentials:

1. Place your service account key file in the `document-api` folder (e.g., `credentials/key.json`)

2. Edit `docker-compose.yml` and uncomment these lines:

```yaml
volumes:
  - ./credentials:/app/credentials:ro

environment:
  GOOGLE_APPLICATION_CREDENTIALS: /app/credentials/key.json
```

3. Restart: `./docker-start.sh`

Alternatively, mount your local gcloud config:

```yaml
volumes:
  - ~/.config/gcloud:/root/.config/gcloud:ro
```

## Accessing the API

Once started:

- **API Base URL**: http://localhost:8000
- **Interactive API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Alternative API Docs**: http://localhost:8000/redoc

## Database Access

The PostgreSQL database is accessible at:

- **Host**: localhost
- **Port**: 5433 (note: not the standard 5432)
- **Database**: vertex_ai_documents
- **Username**: postgres
- **Password**: postgres

Connect with:

```bash
psql -h localhost -p 5433 -U postgres -d vertex_ai_documents
```

Or use a GUI tool like pgAdmin or DBeaver.

## Troubleshooting

### "Docker is not running"

Start Docker Desktop first, then run `./docker-start.sh`

### Port 8000 already in use

Stop any other services using port 8000:

```bash
# Find what's using port 8000
lsof -i :8000

# Kill it
kill -9 <PID>

# Or change the port in docker-compose.yml:
ports:
  - "8001:8080"  # Use port 8001 instead
```

### API not responding

Check the logs:

```bash
docker-compose logs -f api
```

### Database connection errors

Ensure the database is healthy:

```bash
docker-compose ps

# Should show both containers as "Up" and "healthy"
```

### Changes not showing up

Rebuild the container:

```bash
docker-compose up -d --build
```

### Reset everything

```bash
# Stop and remove all containers and data
docker-compose down -v

# Start fresh
./docker-start.sh
```

## Development Workflow

### For Frontend Development

1. **Start the backend once**:
   ```bash
   cd document-api
   ./docker-start.sh
   ```

2. **Start the frontend** (in another terminal):
   ```bash
   cd agent-chat-ui
   pnpm dev
   ```

3. **Work on your frontend** - the backend stays running in Docker

4. **When done for the day**:
   ```bash
   cd document-api
   ./docker-stop.sh
   ```

### For Backend Development

If you're making changes to the backend code:

1. **Make your changes** to Python files

2. **Rebuild and restart**:
   ```bash
   docker-compose up -d --build
   ```

3. **Check logs** for errors:
   ```bash
   docker-compose logs -f api
   ```

**Pro tip**: For faster development, you can mount your code as a volume (see `docker-compose.yml` comments) to enable hot-reloading without rebuilding.

## Container Management

### View running containers

```bash
docker-compose ps
```

### Restart a specific service

```bash
# Restart just the API
docker-compose restart api

# Restart just the database
docker-compose restart postgres
```

### Exec into a container

```bash
# Access the API container shell
docker-compose exec api bash

# Access PostgreSQL CLI
docker-compose exec postgres psql -U postgres -d vertex_ai_documents
```

## Production Considerations

For production deployment:

1. **Use secrets** instead of plain text passwords
2. **Use a managed database** (Cloud SQL, RDS, etc.)
3. **Set up proper logging** and monitoring
4. **Use environment-specific configs**
5. **Enable HTTPS/TLS**
6. **Set up health checks** and auto-restart policies

See [DEPLOYMENT.md](./DEPLOYMENT.md) for production deployment guides.

## Cleanup

### Remove just the containers

```bash
./docker-stop.sh
# or
docker-compose down
```

### Remove containers AND data

```bash
docker-compose down -v
```

### Remove images too

```bash
docker-compose down -v --rmi all
```

## Advantages of Using Docker

✅ **No local dependencies** - Don't need to install Python, PostgreSQL, etc.
✅ **Consistent environment** - Same setup on all machines
✅ **Easy cleanup** - Remove everything with one command
✅ **Isolated** - Doesn't interfere with other projects
✅ **Fast startup** - One command to start everything
✅ **Data persistence** - Database data survives restarts

## Next Steps

- Read the [main README](./README.md) for API usage
- Check [QUICKSTART.md](./QUICKSTART.md) for testing
- See [FRONTEND_SETUP.md](./FRONTEND_SETUP.md) for frontend integration

## Quick Reference

| Command | Description |
|---------|-------------|
| `./docker-start.sh` | Start everything |
| `./docker-stop.sh` | Stop everything |
| `docker-compose logs -f` | View logs |
| `docker-compose ps` | Check status |
| `docker-compose down -v` | Reset everything |
| `docker-compose up -d --build` | Rebuild and restart |

---

**Happy Dockerizing!** 🐳
