# Accord AI Compliance

A production-ready AI-powered compliance document management and Q&A system with multi-modal support (text, PDF, images), vector search, and fine-tuning capabilities.

## Features

- 🚀 **FastAPI Backend**: High-performance async API with MVC architecture
- 📄 **Multi-Modal Ingestion**: Text, PDF (with image extraction), and image uploads
- 🔍 **Vector Similarity Search**: Semantic search across documents and images
- 🤖 **AI-Powered Q&A**: Compliance-focused answers with citations and confidence scores
- ✅ **NPCI BBPS Compliance**: Automated screen validation with logo detection and guideline checking
- 🎯 **Fine-Tuning API**: Upload images and fine-tune Gemini models with full GCP integration
- 🐳 **Fully Dockerized**: Complete docker-compose setup for local development
- 🔒 **Security & Compliance**: PII redaction, audit trails, input validation
- 🧪 **Comprehensive Tests**: pytest suite with integration tests

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  FastAPI API    │────▶│    MongoDB      │◀────│ Mongo Express   │
│  (Python)       │     │  (Documents,    │     │ (Web UI)        │
│                 │     │   Embeddings,   │     │ Port 8081       │
│  - Ingestion    │     │   Audit Logs)   │     └─────────────────┘
│  - QA Engine    │     └─────────────────┘
│  - NPCI Check   │
│  - Fine-tuning  │
│  - Vector Search│
└─────────────────┘
```

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.11+ (for local development)

### 1. Clone and Setup

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your configuration
nano .env
```

### 2. Build and Start Services

```bash
# Build and start all services (FastAPI + MongoDB)
docker-compose up --build

# Or run in detached mode
docker-compose up --build -d

# Using Makefile
make start
```

### 3. Configure Gemini API (Recommended for Top Accuracy)

**Get your FREE API key from Google:**
1. Visit [https://makersuite.google.com/app/apikey](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy your key (starts with `AIza...`)

**Add to your environment:**

Create `.env` file in project root:
```bash
cp env.example .env
```

Edit `.env` and set your API key:
```env
GOOGLE_API_KEY=AIzaSy...your_actual_key_here
```

**Restart services:**
```bash
docker-compose down
docker-compose up --build
```

> **Note**: Without API key, system runs in stub mode (basic functionality). With Gemini, you get:
> - ⚡ Ultra-fast responses (Gemini 2.0 Flash)
> - 🎯 High-accuracy compliance checking
> - 🔍 Advanced logo detection & image analysis
> - 📊 Detailed compliance reports

### 4. Verify Services

- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs (Interactive Swagger UI)
- **Mongo Express**: http://localhost:8081 (MongoDB Web UI - login: admin/admin123)
- **MongoDB**: localhost:27017

Check logs to verify Gemini is working:
```bash
docker-compose logs api | grep "Gemini"
# Should see: ✅ Initialized GeminiAPIAdapter with model: gemini-2.0-flash-exp
```

### 5. Ingest Sample Data

```bash
make ingest-sample
```

### 5. Test Q&A

```bash
curl -X POST "http://localhost:8000/api/v1/qa" \
  -H "Content-Type: application/json" \
  -d '{"query": "What are the data retention policies?", "scope": "all"}'
```

## Development

### Local Development (without Docker)

```bash
# Install dependencies
pip install -r requirements.txt

# Start MongoDB (via Docker)
docker-compose up -d mongo

# Run FastAPI server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run tests
make test
```

### Project Structure

```
accord-ai-compliance/
├── app/                    # FastAPI application
│   ├── main.py            # Application entry point
│   ├── config.py          # Configuration management
│   ├── database.py        # MongoDB connection
│   ├── models/            # Pydantic models
│   ├── controllers/       # Business logic
│   ├── routers/           # API endpoints
│   ├── adapters/          # Pluggable model/embedding adapters
│   ├── utils/             # PDF/image processing utilities
│   └── middleware/        # PII redaction middleware
├── mono-express-admin/    # Admin dashboard (disabled by default)
├── scripts/               # Utility scripts
│   ├── fine_tune_gemini.py
│   └── ingest_samples.py
├── tests/                 # pytest test suite
├── samples/               # Sample documents
└── docker-compose.yml     # Container orchestration
```

## Environment Variables

Key environment variables (see `.env.example` for full list):

### Core Configuration
- `ENVIRONMENT`: `development` or `production`
- `API_HOST`: API host (default: `0.0.0.0`)
- `API_PORT`: API port (default: `8000`)
- `LOG_LEVEL`: Logging level (default: `INFO`)

### MongoDB
- `MONGO_URI`: MongoDB connection string
- `MONGO_DB_NAME`: Database name (default: `accord_compliance`)

### Storage
- `STORAGE_PATH`: File storage path (default: `./storage`)
- `MAX_FILE_SIZE_MB`: Max upload size (default: `50`)

### Model Configuration
- `MODEL_ADAPTER`: `local_stub` or `gemini_vertex` (default: `local_stub`)
- `EMBEDDING_ADAPTER`: `local_stub` or `gemini` (default: `local_stub`)

### Google Cloud / Vertex AI (for production)
- `GEMINI_PROJECT`: GCP project ID
- `GEMINI_LOCATION`: GCP region (e.g., `us-central1`)
- `GEMINI_CREDENTIALS_PATH`: Path to service account JSON
- `GEMINI_MODEL_NAME`: Model name (e.g., `gemini-1.5-pro`)

### Security
- `API_KEY`: Optional API key for authentication
- `PII_REDACTION_ENABLED`: Enable PII redaction (default: `true`)

## API Endpoints

### Ingestion

#### Ingest Text
```bash
POST /api/v1/ingest/text
Content-Type: application/json

{
  "text": "Your compliance document text...",
  "metadata": {
    "source": "policy-handbook",
    "version": "2.1"
  }
}
```

#### Ingest PDF
```bash
POST /api/v1/ingest/pdf
Content-Type: multipart/form-data

file=@compliance_policy.pdf
metadata={"department": "legal"}
```

#### Ingest Image
```bash
POST /api/v1/ingest/image
Content-Type: multipart/form-data

file=@flowchart.png
metadata={"type": "process-diagram"}
```

### Q&A

#### Ask Question
```bash
POST /api/v1/qa
Content-Type: application/json

{
  "query": "What are the GDPR data retention requirements?",
  "scope": "all",
  "top_k": 5
}
```

### NPCI BBPS Compliance

#### Check Screen Compliance
```bash
POST /api/v1/compliance/npci/check
Content-Type: multipart/form-data

file=@screenshot.png
screen_type=categories
```

Response:
```json
{
  "screen_type": "categories",
  "compliance_score": 85.5,
  "final_verdict": "Partially Compliant",
  "issues_identified": ["Missing 3 categories"],
  "comparison_table": {...},
  "reasoning": "..."
}
```

#### Get Guidelines
```bash
GET /api/v1/compliance/npci/guidelines
GET /api/v1/compliance/npci/guidelines/categories
```

### Fine-Tuning (NEW!)

#### Upload Training Image
```bash
POST /api/v1/finetune/upload-image
Content-Type: multipart/form-data

file=@training_image.png
prompt="Analyze this compliance screen"
expected_output="The screen shows..."
```

#### Start Fine-Tuning Job
```bash
POST /api/v1/finetune/start
Content-Type: application/json

{
  "job_name": "compliance_v1",
  "base_model": "gemini-1.5-pro",
  "data_source": "mixed",
  "epochs": 5,
  "include_images": true,
  "min_samples": 100
}
```

#### Monitor Job
```bash
GET /api/v1/finetune/status/{job_id}
```

See [FINE_TUNING_GUIDE.md](FINE_TUNING_GUIDE.md) for complete documentation.

Response:
```json
{
  "answer": "According to the stored compliance documents...",
  "confidence": 0.92,
  "citations": [
    {
      "doc_id": "507f1f77bcf86cd799439011",
      "filename": "gdpr_policy.pdf",
      "excerpt": "Data must be retained for no longer than...",
      "similarity_score": 0.89
    }
  ],
  "query": "What are the GDPR data retention requirements?",
  "model_used": "local_stub_v1",
  "timestamp": "2025-11-07T10:30:00Z"
}
```

### Documents

#### List Documents
```bash
GET /api/v1/documents?skip=0&limit=20
```

#### Get Document
```bash
GET /api/v1/documents/{document_id}
```

## Fine-Tuning with Gemini/Vertex AI

### Prerequisites

1. **Enable Google Cloud APIs**:
   ```bash
   gcloud services enable aiplatform.googleapis.com
   gcloud services enable storage-component.googleapis.com
   ```

2. **Create Service Account**:
   ```bash
   gcloud iam service-accounts create accord-ai \
     --display-name="Accord AI Service Account"
   
   gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
     --member="serviceAccount:accord-ai@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
     --role="roles/aiplatform.user"
   
   gcloud iam service-accounts keys create credentials.json \
     --iam-account=accord-ai@YOUR_PROJECT_ID.iam.gserviceaccount.com
   ```

3. **Configure Environment**:
   ```bash
   export GEMINI_PROJECT="your-gcp-project"
   export GEMINI_LOCATION="us-central1"
   export GEMINI_CREDENTIALS_PATH="./credentials.json"
   ```

### Run Fine-Tuning

```bash
# Activate virtual environment
source venv/bin/activate

# Run fine-tuning script
python scripts/fine_tune_gemini.py \
  --dataset-source audit \
  --min-samples 100 \
  --epochs 3
```

The script will:
1. Extract Q&A pairs from audit logs
2. Format data for Vertex AI
3. Upload to GCS
4. Start fine-tune job
5. Register new model in MongoDB

### Switch to Fine-Tuned Model

Update `.env`:
```bash
MODEL_ADAPTER=gemini_vertex
GEMINI_MODEL_NAME=your-fine-tuned-model-id
```

Restart services:
```bash
make restart
```

## Testing

### Run All Tests
```bash
make test
```

### Run Specific Tests
```bash
# Test ingestion
pytest tests/test_ingest.py -v

# Test QA with coverage
pytest tests/test_qa.py --cov=app/controllers/qa

# Integration tests
pytest tests/ -m integration
```

### Test Coverage
```bash
pytest --cov=app --cov-report=html
open htmlcov/index.html
```

## Makefile Commands

```bash
make start          # Start all services
make stop           # Stop all services
make restart        # Restart all services
make logs           # View logs
make test           # Run tests
make lint           # Run linters
make format         # Format code
make ingest-sample  # Ingest sample data
make clean          # Clean up containers and volumes
```

## Production Deployment Checklist

### Security
- [ ] Rotate all API keys and secrets
- [ ] Use managed secrets (AWS Secrets Manager, GCP Secret Manager)
- [ ] Enable HTTPS/TLS for all services
- [ ] Configure firewall rules (restrict MongoDB access)
- [ ] Enable API rate limiting
- [ ] Review and configure PII redaction rules
- [ ] Set up security scanning for uploaded files

### Google Cloud / Vertex AI
- [ ] Create dedicated GCP project
- [ ] Enable required APIs (AI Platform, Storage, Logging)
- [ ] Create service account with minimal permissions
- [ ] Set up VPC and private networking
- [ ] Configure budget alerts
- [ ] Review Vertex AI quotas and request increases

### Database
- [ ] Use MongoDB Atlas or managed MongoDB
- [ ] Enable authentication and authorization
- [ ] Configure backup strategy (daily snapshots)
- [ ] Set up connection pooling
- [ ] Create indexes for frequently queried fields
- [ ] Enable encryption at rest

### Vector Search Scaling
- [ ] For >100K documents, migrate to dedicated vector DB:
  - **Pinecone**: Managed, easy integration
  - **Milvus**: Self-hosted, open-source
  - **Weaviate**: GraphQL API, ML-native
  - **Qdrant**: Rust-based, high performance
- [ ] Implement caching for frequent queries
- [ ] Set up embedding batch processing

### Monitoring & Observability
- [ ] Set up application monitoring (Datadog, New Relic)
- [ ] Configure log aggregation (ELK, CloudWatch)
- [ ] Create alerts for errors and performance
- [ ] Set up uptime monitoring
- [ ] Track model performance metrics
- [ ] Monitor embedding generation latency
- [ ] Set up cost monitoring for Vertex AI

### Performance
- [ ] Configure connection pooling
- [ ] Enable Redis/Memcached for caching
- [ ] Set up CDN for static assets (admin UI)
- [ ] Optimize Docker images (multi-stage builds)
- [ ] Configure horizontal pod autoscaling (k8s)
- [ ] Load test with realistic traffic

### Backup & Disaster Recovery
- [ ] Automated daily MongoDB backups
- [ ] Backup storage files to S3/GCS
- [ ] Document restore procedures
- [ ] Set up cross-region replication
- [ ] Test disaster recovery procedures

### CI/CD
- [ ] Set up GitHub Actions / GitLab CI
- [ ] Automated testing on PRs
- [ ] Container scanning for vulnerabilities
- [ ] Automated deployment to staging
- [ ] Manual approval for production deploys

### Documentation
- [ ] API documentation (OpenAPI/Swagger)
- [ ] Architecture diagrams
- [ ] Runbooks for common issues
- [ ] Onboarding guide for new developers
- [ ] Incident response procedures

## Troubleshooting

### MongoDB Connection Issues
```bash
# Check MongoDB is running
docker-compose ps mongo

# View MongoDB logs
docker-compose logs mongo

# Test connection
docker-compose exec mongo mongosh --eval "db.adminCommand('ping')"
```

### API Not Starting
```bash
# Check logs
docker-compose logs api

# Common issues:
# - MongoDB not ready: wait 10-15 seconds after starting
# - Port conflict: check if 8000 is in use
# - Missing .env: ensure .env file exists
```

### Fine-Tuning Fails
```bash
# Verify GCP credentials
gcloud auth application-default login

# Check API enablement
gcloud services list --enabled | grep aiplatform

# Verify service account permissions
gcloud projects get-iam-policy YOUR_PROJECT_ID \
  --flatten="bindings[].members" \
  --format="table(bindings.role)" \
  --filter="bindings.members:accord-ai@"
```

### Slow Vector Search
- For small datasets (<10K docs), in-memory search is sufficient
- For larger datasets, migrate to dedicated vector DB
- Check embedding dimensions and normalize vectors
- Consider approximate nearest neighbor (ANN) algorithms

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Code Style

- Follow PEP 8 for Python code
- Use type hints for all functions
- Write docstrings for public APIs
- Run `make lint` before committing
- Use `make format` to auto-format code

## License

MIT License - see LICENSE file for details

## Support

For issues and questions:
- Open an issue on GitHub
- Check existing documentation
- Review troubleshooting section

## Acknowledgments

- FastAPI for the excellent web framework
- MongoDB for flexible document storage
- Google Gemini/Vertex AI for powerful ML capabilities
- The open-source community for amazing tools

# gen-ai
