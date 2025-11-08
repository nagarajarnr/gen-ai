# 🚀 Accord AI Compliance - Quick Start

Get your AI-powered compliance system running in **2 minutes**!

---

## Step 1: Configure Gemini API (30 seconds)

### Get FREE API Key

1. Visit **[https://makersuite.google.com/app/apikey](https://makersuite.google.com/app/apikey)**
2. Sign in with your Google account
3. Click **"Create API Key"**
4. Copy your key (starts with `AIza...`)

### Set API Key

Create `.env` file in project root:

```bash
cp env.example .env
```

Edit `.env` and add your API key:

```env
GOOGLE_API_KEY=AIzaSyC...your_actual_key_here
```

> **Why Gemini?**
> - ⚡ Ultra-fast inference (<1s)
> - 🎯 High accuracy for compliance
> - 🔍 Advanced image & logo detection
> - 💰 Free tier available!

---

## Step 2: Start Services (1 minute)

```bash
docker-compose up --build
```

Wait for:
```
✅ Initialized GeminiAPIAdapter with model: gemini-2.0-flash-exp
✅ Connected to MongoDB
✅ Application startup complete
```

---

## Step 3: Access the System

### 🌐 Swagger UI (Main Interface)
**👉 http://localhost:8000/docs**

- Upload documents
- Check NPCI compliance
- Ask Q&A questions
- Upload images and start fine-tuning jobs
- Monitor all operations

### 📊 Mongo Express (Database UI)
**👉 http://localhost:8081**
- **Username**: admin
- **Password**: admin123
- Browse collections, view documents, run queries

### 🔧 API Endpoints
- **Base URL**: http://localhost:8000
- **Health Check**: http://localhost:8000/health
- **Configuration**: http://localhost:8000/api/v1/config

### 🗄️ MongoDB
- **URI**: mongodb://localhost:27017
- **Database**: accord_compliance

---

## 🎯 Quick Test

### 1. Verify API is Running

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "database": "connected",
  "model_adapter": "gemini_api"
}
```

### 2. Upload a Document

Go to **http://localhost:8000/docs** and try:

**POST /api/v1/ingest/text**
```json
{
  "text_content": "Our payment system requires PCI DSS Level 1 compliance. All transactions must be encrypted using TLS 1.3 or higher.",
  "filename": "payment_policy.txt",
  "metadata": {
    "source": "quick_test",
    "category": "payment"
  }
}
```

### 3. Ask a Question

**POST /api/v1/qa**
```json
{
  "query": "What encryption is required for payments?",
  "top_k": 5
}
```

Expected response with Gemini:
```json
{
  "query": "What encryption is required for payments?",
  "answer": "Based on the payment policy document, the system requires TLS 1.3 or higher encryption for all transactions to maintain PCI DSS Level 1 compliance...",
  "confidence": 0.92,
  "sources": [...],
  "model_used": "gemini-2.0-flash-exp"
}
```

### 4. Check NPCI Compliance

Upload a screenshot via Swagger UI:

**POST /api/v1/compliance/npci/check**
- **file**: Upload screenshot
- **screen_type**: `categories`

Get detailed compliance analysis with:
- Logo detection (Gemini Vision)
- Position & size verification
- Category completeness check
- Compliance score & recommendations

---

## 📚 What's Included

### ✅ AI Models (Gemini 2.0 Flash)
- **Q&A**: Document-based question answering
- **Vision**: Logo & UI element detection
- **Embeddings**: Semantic similarity search
- **Compliance**: Automated NPCI BBPS checking

### ✅ Features
- 📄 Multi-format ingestion (text, PDF, images)
- 🔍 Vector similarity search
- 🎯 Compliance checking (NPCI BBPS)
- 🤖 Fine-tuning API (custom models)
- 📊 Audit logs & analytics
- 🔒 PII redaction

### ✅ Infrastructure
- 🐳 Docker Compose orchestration
- 🗄️ MongoDB database
- 📊 Mongo Express UI
- 🔄 Auto-reload for development
- 📝 Comprehensive logging

---

## 🎯 Key API Endpoints

### Document Ingestion
- `POST /api/v1/ingest/text` - Ingest text documents
- `POST /api/v1/ingest/pdf` - Ingest PDF files
- `POST /api/v1/ingest/image` - Ingest images

### Q&A
- `POST /api/v1/qa` - Ask questions about documents

### NPCI Compliance
- `POST /api/v1/compliance/npci/check` - Check single screenshot
- `POST /api/v1/compliance/npci/check-batch` - Batch compliance check
- `GET /api/v1/compliance/npci/guidelines` - View all guidelines
- `GET /api/v1/compliance/npci/guidelines/{screen_type}` - Screen-specific guidelines

### Fine-Tuning
- `POST /api/v1/finetune/upload-image` - Upload training images
- `POST /api/v1/finetune/start` - Start fine-tuning job
- `GET /api/v1/finetune/status/{job_id}` - Monitor job status
- `GET /api/v1/finetune/jobs` - List all jobs

---

## 🔧 Configuration

### Model Settings

Your system is configured with:

```yaml
Model: gemini-2.0-flash-exp
Purpose: Ultra-fast, high-accuracy compliance
Speed: ⚡⚡⚡⚡⚡ (5/5)
Accuracy: ⭐⭐⭐⭐ (4/5)
Cost: 💰 (Free tier available)
```

### Environment Variables

Key settings in `.env`:

```env
# AI Model
MODEL_ADAPTER=gemini_api
EMBEDDING_ADAPTER=gemini_api
IMAGE_CAPTION_ADAPTER=gemini_vision
GOOGLE_API_KEY=your_key_here
GEMINI_MODEL_NAME=gemini-2.0-flash-exp

# Database
MONGO_URI=mongodb://mongo:27017
MONGO_DB_NAME=accord_compliance

# Security
PII_REDACTION_ENABLED=true

# Search
TOP_K_RESULTS=5
SIMILARITY_THRESHOLD=0.7
```

---

## 📖 Documentation

- **Full Guide**: `README.md`
- **Quick Start**: `QUICKSTART.md`
- **Gemini Setup**: `GEMINI_SETUP_GUIDE.md`
- **NPCI Compliance**: `NPCI_COMPLIANCE_GUIDE.md`
- **Fine-Tuning**: `FINE_TUNING_GUIDE.md`

---

## 🐛 Troubleshooting

### "Gemini API not configured"

**Solution**: Set `GOOGLE_API_KEY` in `.env` file and rebuild:

```bash
# Edit .env file
nano .env  # Add: GOOGLE_API_KEY=AIza...

# Rebuild
docker-compose down
docker-compose up --build
```

### Check if Gemini is Working

```bash
# View logs
docker-compose logs api | grep "Gemini"

# Should see:
# ✅ Initialized GeminiAPIAdapter with model: gemini-2.0-flash-exp
```

### Services Not Starting

```bash
# Check status
docker-compose ps

# View logs
docker-compose logs

# Restart
docker-compose restart
```

### Port Already in Use

Edit `docker-compose.yml` and change ports:

```yaml
ports:
  - "8001:8000"  # Change 8000 to 8001
```

---

## 🎉 You're Ready!

Your AI-powered compliance system is now running with:
- ⚡ Gemini 2.0 Flash for ultra-fast responses
- 🔍 Advanced image analysis & logo detection
- 📊 Automated NPCI BBPS compliance checking
- 🤖 Fine-tuning capabilities
- 📝 Complete audit trail

### Next Steps

1. **Test Q&A**: Visit http://localhost:8000/docs and try Q&A endpoint
2. **Upload Documents**: Ingest your compliance documents
3. **Check Compliance**: Upload NPCI screenshots for analysis
4. **View Data**: Browse MongoDB at http://localhost:8081
5. **Read Docs**: Check `GEMINI_SETUP_GUIDE.md` for advanced features

---

## 💡 Pro Tips

1. **Use Gemini 2.0 Flash** for best speed/accuracy balance (already configured!)
2. **Monitor usage** at https://makersuite.google.com/
3. **Check logs** regularly: `docker-compose logs -f api`
4. **View database** in Mongo Express to see ingested data
5. **Test incrementally** - start with simple queries, then complex compliance checks

---

## 📞 Support

- **GitHub Issues**: Report bugs or request features
- **Documentation**: See `docs/` folder for detailed guides
- **Logs**: `docker-compose logs api`
- **Health Check**: http://localhost:8000/health

---

**Happy Compliance Checking! 🎯**
