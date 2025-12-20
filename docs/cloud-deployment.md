# Supe Cloud Deployment Configuration
# For use with Claude agents and other AI systems

## Environment Variables

Required for cloud deployment:

```bash
# Database path (SQLite for local, or connection string for PostgreSQL)
TASC_DB=/app/data/tasc.sqlite

# Optional: API mode
SUPE_API_HOST=0.0.0.0
SUPE_API_PORT=8000

# Optional: Logging
SUPE_LOG_LEVEL=INFO
```

## Docker Deployment

### Single Container
```bash
# Build
docker build -t supe .

# Run interactive
docker run -it -v $(pwd)/data:/app/data supe

# Run proof command
docker run -v $(pwd):/workspace -w /workspace supe prove "pytest tests/"
```

### With Docker Compose
```bash
# Start services
docker-compose up -d

# Execute commands
docker exec -it supe supe prove "echo hello"
docker exec -it supe supe status

# One-shot runner
docker-compose --profile runner run supe-runner prove "pytest"
```

## Claude Agent Integration

### MCP Server Configuration

Add to your Claude Desktop configuration:

```json
{
  "mcpServers": {
    "supe": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "-v", "$(pwd):/workspace", "-w", "/workspace", "supe", "mcp-server"],
      "env": {}
    }
  }
}
```

### Direct CLI Usage

Claude agents can use supe CLI directly for proof-of-work:

```python
# In agent code
import subprocess

# Prove a task
result = subprocess.run(
    ["supe", "prove", "pytest tests/"],
    capture_output=True,
    text=True
)

# Check proof
if "PROVEN" in result.stdout:
    print("Task completed with proof")
```

## Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: supe
spec:
  replicas: 1
  selector:
    matchLabels:
      app: supe
  template:
    metadata:
      labels:
        app: supe
    spec:
      containers:
        - name: supe
          image: ghcr.io/your-repo/supe:latest
          env:
            - name: TASC_DB
              value: /data/tasc.sqlite
          volumeMounts:
            - name: data
              mountPath: /data
      volumes:
        - name: data
          persistentVolumeClaim:
            claimName: supe-data
```

## Health Checks

```bash
# Check if supe is running
supe status

# Verify proof system
supe prove "echo health-check"
```

## Logging

Supe outputs structured logs compatible with cloud logging systems:

```bash
# Enable verbose logging
SUPE_LOG_LEVEL=DEBUG supe prove "command"

# JSON output for log aggregation
supe prove "command" 2>&1 | jq -R 'fromjson? // {raw: .}'
```
