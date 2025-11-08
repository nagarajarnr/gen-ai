# Accord AI Compliance - Quick Start Guide

Get up and running with Accord AI Compliance in 5 minutes!

## Prerequisites

- Docker & Docker Compose installed
- At least 4GB RAM available
- Ports 8000, 8081, 27017 available

## Step-by-Step Setup

### 1. Environment Setup

```bash
# Copy environment template
cp env.example .env

# The default configuration works out of the box for local development
# No changes needed unless you want to customize
```

### 2. Build and Start Services

```bash
# Build and start all services
docker-compose up --build

# Or run in detached mode
docker-compose up --build -d

# Wait ~15 seconds for services to initialize
# Check status
docker-compose ps
```

You should see:
- ✅ `accord-api` (FastAPI)
- ✅ `accord-mongo` (MongoDB)
- ✅ `accord-mongo-express` (MongoDB Web UI)

### 3. Verify Services

```bash
# Check API health
curl http://localhost:8000/health

# Expected output:
# {"status":"healthy","environment":"development",...}
```

Access points:
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs (Interactive Swagger UI - **Use this!**)
- **Mongo Express**: http://localhost:8081 (MongoDB Web UI - login: admin/admin123)
- **MongoDB**: localhost:27017

### 4. Ingest Sample Data

```bash
# Load sample compliance documents
make ingest-sample

# Or manually:
# docker-compose exec api python scripts/ingest_samples.py
```

Expected output:
```
✓ Successfully ingested 2 sample documents
Document IDs:
  - abc123...
  - def456...
```

### 5. Test Q&A

```bash
# Ask a compliance question
curl -X POST "http://localhost:8000/api/v1/qa" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are the data retention requirements?",
    "scope": "all"
  }'
```

Expected response:
```json
{
  "answer": "According to the compliance documents...",
  "confidence": 0.85,
  "citations": [
    {
      "doc_id": "abc123...",
      "filename": "text_abc123.txt",
      "excerpt": "Personal data must be retained...",
      "similarity_score": 0.89
    }
  ],
  "query": "What are the data retention requirements?",
  "model_used": "local_stub_v1",
  "timestamp": "2025-11-07T10:30:00Z"
}
```

## Next Steps

### Explore API Documentation

Open http://localhost:8000/docs in your browser for interactive API documentation.

Try these endpoints:
1. **Ingest Text**: `/api/v1/ingest/text`
2. **Ingest PDF**: `/api/v1/ingest/pdf`
3. **Ask Question**: `/api/v1/qa`
4. **List Documents**: `/api/v1/documents`

### Import Postman Collection

Import `postman/accord-ai-compliance.postman_collection.json` into Postman for ready-to-use API requests.

### View Admin Dashboard

Navigate to http://localhost:3000 to see:
- Document count and statistics
- Recent Q&A queries
- Audit logs
- Model registry

## Common Tasks

### Ingest Your Own Documents

#### Text Document
```bash
curl -X POST "http://localhost:8000/api/v1/ingest/text" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Your compliance policy text here...",
    "metadata": {"department": "legal", "version": "1.0"}
  }'
```

#### PDF Document
```bash
curl -X POST "http://localhost:8000/api/v1/ingest/pdf" \
  -F "file=@/path/to/your/policy.pdf" \
  -F 'metadata={"department": "legal"}'
```

#### Image with OCR
```bash
curl -X POST "http://localhost:8000/api/v1/ingest/image" \
  -F "file=@/path/to/your/diagram.png" \
  -F 'metadata={"type": "flowchart"}'
```

### Query Documents

```bash
curl -X POST "http://localhost:8000/api/v1/qa" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Your compliance question here?",
    "scope": "all",
    "top_k": 5
  }'
```

### List All Documents

```bash
curl http://localhost:8000/api/v1/documents
```

### View Logs

```bash
# All services
docker-compose logs -f

# Just API
docker-compose logs -f api

# Just MongoDB
docker-compose logs -f mongo
```

## Stopping Services

```bash
# Stop services
docker-compose down

# Stop and remove volumes (deletes all data)
docker-compose down -v
```

## Troubleshooting

### API Not Responding

```bash
# Check if container is running
docker-compose ps api

# View logs
docker-compose logs api

# Restart API
docker-compose restart api
```

### MongoDB Connection Issues

```bash
# Check MongoDB is running
docker-compose ps mongo

# Test connection
docker-compose exec mongo mongosh --eval "db.adminCommand('ping')"

# If needed, restart MongoDB
docker-compose restart mongo
```

### Port Conflicts

If ports 8000, 8081, or 27017 are in use:

Edit `docker-compose.yml` and change the port mappings:
```yaml
ports:
  - "8001:8000"  # Change host port from 8000 to 8001
```

### Clean Start

```bash
# Stop everything and remove volumes
docker-compose down -v

# Remove Docker images
docker-compose down --rmi all

# Rebuild and start
docker-compose build --no-cache
docker-compose up -d
```

## Production Deployment

For production use:

1. **Update `.env`** with production values:
   ```bash
   ENVIRONMENT=production
   MODEL_ADAPTER=gemini_vertex
   GEMINI_PROJECT=your-gcp-project
   GEMINI_CREDENTIALS_PATH=/path/to/credentials.json
   ```

2. **Enable Vertex AI** (see README for full instructions):
   - Create GCP project
   - Enable Vertex AI APIs
   - Create service account
   - Download credentials

3. **Secure MongoDB**:
   - Use MongoDB Atlas or managed instance
   - Enable authentication
   - Use connection string with credentials

4. **Set up monitoring** (Datadog, New Relic, etc.)

5. **Configure backups** (see README Production Checklist)

## Getting Help

- **Documentation**: See main README.md
- **API Docs**: http://localhost:8000/docs
- **Logs**: `docker-compose logs`
- **Issues**: Check troubleshooting section above

## Architecture Overview

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  FastAPI API    │────▶│    MongoDB      │◀────│ Mongo Express   │
│  Port 8000      │     │  Port 27017     │     │ Port 8081       │
│                 │     │                 │     │                 │
│  - Ingestion    │     │  - Documents    │     │  - View DB      │
│  - Q&A          │     │  - Embeddings   │     │  - Browse Data  │
│  - NPCI Check   │     │  - Audit Logs   │     │  - Run Queries  │
│  - Fine-tuning  │     │  - Model Jobs   │     └─────────────────┘
│  - Vector Search│     │                 │
└─────────────────┘     └─────────────────┘
```

## Key Features

✅ **Multi-Modal Ingestion**: Text, PDF (with image extraction), and images  
✅ **Vector Search**: Semantic similarity search for document retrieval  
✅ **AI Q&A**: Compliance-focused question answering with citations  
✅ **OCR**: Automatic text extraction from images and PDFs  
✅ **PII Detection**: Automatic sensitive content flagging  
✅ **Audit Trails**: Complete logging of all operations  
✅ **Fine-Tuning Support**: Scripts for Gemini/Vertex AI model fine-tuning  
✅ **Admin Dashboard**: Web UI for monitoring and management  

## Example Use Cases

1. **Compliance Q&A**: "What are our GDPR data retention requirements?"
2. **Policy Search**: Find relevant sections across multiple policy documents
3. **Document Analysis**: Extract and analyze compliance requirements from PDFs
4. **Audit Trail**: Track all document access and queries for compliance reporting
5. **Multi-modal Search**: Search across text documents and scanned images

---

**You're all set!** 🚀

Start by exploring the API docs at http://localhost:8000/docs

