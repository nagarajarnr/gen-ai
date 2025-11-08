# Accord AI - Simplified Q&A & Fine-Tuning API 🚀

## ✅ What You Get

A **clean, focused API** with only what you need:

- 🔐 **Authentication** (JWT-based login/signup)
- 🤖 **Q&A with Gemini 2.0 Flash** (text, images, PDFs)
- 📄 **8K PDF Conversion** (ultra HD before analysis!)
- 🎯 **Model Fine-Tuning** (upload data, train, monitor)

**No bloat. Just results.**

---

## 🚀 Quick Start

### 1. Start Everything
```bash
docker-compose up -d
```

### 2. Set Your Gemini API Key
Create `.env` file:
```env
GOOGLE_API_KEY=your-gemini-api-key-here
```

Get your key at: https://makersuite.google.com/app/apikey

### 3. Test It
```bash
# Open API docs
http://localhost:8000/docs

# Or run automated tests
.\test_simplified_apis.ps1
```

---

## 📋 All 8 APIs

### Authentication (No token required)
1. **POST** `/api/v1/auth/signup` - Register
2. **POST** `/api/v1/auth/login` - Login

### Q&A (Token required)
3. **POST** `/api/v1/qa/text` - Ask text questions
4. **POST** `/api/v1/qa/image` - Ask about images
5. **POST** `/api/v1/qa/pdf` - Ask about PDFs (8K conversion!)

### Fine-Tuning (Token required)
6. **POST** `/api/v1/finetune/upload-image` - Add training data
7. **POST** `/api/v1/finetune/start` - Start training job
8. **GET** `/api/v1/finetune/status/{job_id}` - Check progress

---

## 🌟 Special Features

### 📄 PDF to 8K Ultra HD
When you upload a PDF:
1. Each page is converted to **8K resolution** (7680px width)
2. Sent to Gemini 2.0 Flash for analysis
3. Gets the **best possible quality** for AI understanding

**Why?** Better image quality = Better AI answers!

### 🤖 Gemini 2.0 Flash
- Latest Google AI model
- Multi-modal (text + images)
- Fast and accurate
- Perfect for document analysis

---

## 💡 Example Usage

### 1. Sign Up & Get Token
```bash
curl -X POST "http://localhost:8000/api/v1/auth/signup" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "johndoe",
    "email": "john@example.com",
    "phone": "+1234567890",
    "password": "SecurePass123!"
  }'

# Save the access_token from response
```

### 2. Ask a Text Question
```bash
curl -X POST "http://localhost:8000/api/v1/qa/text" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "question=What is quantum computing?"
```

### 3. Ask About an Image
```bash
curl -X POST "http://localhost:8000/api/v1/qa/image" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@screenshot.png" \
  -F "question=What UI issues do you see?"
```

### 4. Ask About a PDF (with 8K conversion!)
```bash
curl -X POST "http://localhost:8000/api/v1/qa/pdf" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@document.pdf" \
  -F "question=Summarize the key points"
```

### 5. Fine-Tune a Model
```bash
# Upload training data
curl -X POST "http://localhost:8000/api/v1/finetune/upload-image" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@training1.png" \
  -F "prompt=Identify issues" \
  -F "expected_output=Logo missing"

# Start training
curl -X POST "http://localhost:8000/api/v1/finetune/start" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "model_name=my-custom-model" \
  -F "epochs=10"

# Check status (use job_id from previous response)
curl -X GET "http://localhost:8000/api/v1/finetune/status/JOB_ID" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 📊 System Status

| Service | Status | URL |
|---------|--------|-----|
| **API** | ✅ Running | http://localhost:8000 |
| **API Docs** | ✅ Available | http://localhost:8000/docs |
| **MongoDB** | ✅ Running | localhost:27017 |
| **Mongo Express** | ✅ Running | http://localhost:8081 |

Check health:
```bash
curl http://localhost:8000/health
```

---

## 🔑 Authentication

All Q&A and Fine-Tuning endpoints require JWT authentication:

```http
Authorization: Bearer YOUR_TOKEN_HERE
```

Token expires after **24 hours**. Just login again to get a new one.

---

## 🐍 Python Example

```python
import requests

BASE_URL = "http://localhost:8000/api/v1"

# 1. Login
response = requests.post(f"{BASE_URL}/auth/login", json={
    "username": "johndoe",
    "password": "SecurePass123!"
})
token = response.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# 2. Ask a question
response = requests.post(
    f"{BASE_URL}/qa/text",
    headers=headers,
    data={"question": "Explain AI"}
)
print(response.json()["answer"])

# 3. Ask about an image
with open("screenshot.png", "rb") as f:
    response = requests.post(
        f"{BASE_URL}/qa/image",
        headers=headers,
        files={"file": f},
        data={"question": "What's in this image?"}
    )
print(response.json()["answer"])

# 4. Ask about a PDF (8K conversion!)
with open("report.pdf", "rb") as f:
    response = requests.post(
        f"{BASE_URL}/qa/pdf",
        headers=headers,
        files={"file": f},
        data={"question": "Summarize this"}
    )
print(response.json()["answer"])
```

---

## 📁 Project Structure

```
mini-ultra-ai/
├── app/
│   ├── routers/
│   │   ├── auth.py          # Login/Signup
│   │   ├── qa.py            # Q&A APIs
│   │   └── fine_tune.py     # Fine-tuning APIs
│   ├── services/
│   │   └── gemini_service.py  # Gemini integration
│   ├── middleware/
│   │   └── auth.py          # JWT authentication
│   └── main.py              # FastAPI app
├── docker-compose.yml       # Docker setup
├── requirements.txt         # Python dependencies
├── SIMPLIFIED_API_GUIDE.md  # Detailed API docs
└── README_SIMPLIFIED.md     # This file
```

---

## 🛠️ Tech Stack

- **FastAPI** 0.115.0 - Modern Python web framework
- **MongoDB** 7.0 - Database
- **Gemini 2.0 Flash** - Google's latest AI model
- **JWT** - Authentication
- **Docker** - Containerization
- **PyMuPDF** - PDF processing (8K conversion)
- **Pillow** - Image processing

---

## 📚 Documentation

| Document | Description |
|----------|-------------|
| **SIMPLIFIED_API_GUIDE.md** | Complete API reference with examples |
| **AUTH_GUIDE.md** | Authentication details |
| **test_simplified_apis.ps1** | Automated test script |

---

## 🔧 Configuration

### Required Environment Variables

```env
# MongoDB
MONGODB_URL=mongodb://mongo:27017
DATABASE_NAME=accord_compliance

# JWT (CHANGE IN PRODUCTION!)
JWT_SECRET_KEY=your-secret-key-min-32-chars
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Google Gemini (REQUIRED!)
GOOGLE_API_KEY=your-gemini-api-key
```

### Optional Settings

```env
MAX_FILE_SIZE_MB=50
LOG_LEVEL=INFO
```

---

## 🧪 Testing

### Automated Test
```powershell
.\test_simplified_apis.ps1
```

### Manual Tests
```bash
# Health check
curl http://localhost:8000/health

# Sign up
curl -X POST http://localhost:8000/api/v1/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"username":"test","email":"test@test.com","phone":"+1234567890","password":"Test123!"}'
```

---

## ⚠️ Important Notes

1. **Set GOOGLE_API_KEY** - Required for Q&A features
2. **Change JWT_SECRET_KEY** - Use a strong secret in production
3. **File Size Limit** - Default 50MB per file
4. **Token Expiry** - 24 hours, re-login after that
5. **8K Conversion** - PDF pages auto-converted to 7680px width

---

## 🎯 What Was Removed

This is a **simplified version**. We removed:
- ❌ NPCI compliance checking
- ❌ Document ingestion endpoints
- ❌ Complex fine-tuning options
- ❌ Unnecessary features

**Result:** Clean, focused, easy to use!

---

## 🚀 Next Steps

1. **Start services**: `docker-compose up -d`
2. **Set API key**: Add `GOOGLE_API_KEY` to `.env`
3. **Open docs**: http://localhost:8000/docs
4. **Test APIs**: Use the examples above
5. **Build your app**: Integrate with your frontend

---

## 💬 Support

- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **MongoDB UI**: http://localhost:8081

---

## ✨ Summary

✅ **8 Essential APIs**  
✅ **JWT Authentication**  
✅ **Gemini 2.0 Flash**  
✅ **8K PDF Conversion**  
✅ **Model Fine-Tuning**  
✅ **Production-Ready**  

**Everything you need. Nothing you don't.** 🎯

---

*Built with ❤️ using FastAPI and Gemini 2.0 Flash*

