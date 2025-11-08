# Simplified Accord AI API Guide

## 🎯 Overview

This is a **simplified, focused API** with only essential features:

✅ **Authentication** (Login/Signup)  
✅ **Q&A with Gemini 2.0 Flash** (Text, Images, PDFs with 8K conversion)  
✅ **Model Fine-Tuning** (Upload training data, start jobs, check status)  

---

## 🚀 Quick Start

### 1. Start Services
```bash
docker-compose up -d
```

### 2. Access API Documentation
- **Interactive Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

### 3. Get Your Google API Key
You need a Google Gemini API key for Q&A features:
1. Go to https://makersuite.google.com/app/apikey
2. Create an API key
3. Set it in your `.env` file:
```env
GOOGLE_API_KEY=your-gemini-api-key-here
```

---

## 📋 API Endpoints

### 🔐 Authentication

#### 1. Sign Up
```http
POST /api/v1/auth/signup
Content-Type: application/json

{
  "username": "johndoe",
  "email": "john@example.com",
  "phone": "+1234567890",
  "password": "SecurePass123!"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 86400,
  "user": {
    "_id": "abc123",
    "username": "johndoe",
    "email": "john@example.com"
  }
}
```

#### 2. Login
```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "username": "johndoe",
  "password": "SecurePass123!"
}
```

**Response:** Same as signup

---

### 🤖 Q&A with Gemini 2.0 Flash

All Q&A endpoints require authentication:
```http
Authorization: Bearer YOUR_TOKEN
```

#### 1. Ask Text Question

```http
POST /api/v1/qa/text
Content-Type: multipart/form-data
Authorization: Bearer YOUR_TOKEN

question=What is artificial intelligence?
```

**cURL Example:**
```bash
curl -X POST "http://localhost:8000/api/v1/qa/text" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "question=What is artificial intelligence?"
```

**Response:**
```json
{
  "question": "What is artificial intelligence?",
  "answer": "Artificial intelligence (AI) is the simulation of human intelligence processes by machines...",
  "model": "gemini-2.0-flash-exp",
  "user_id": "abc123"
}
```

#### 2. Ask Question About Image

```http
POST /api/v1/qa/image
Content-Type: multipart/form-data
Authorization: Bearer YOUR_TOKEN

file=@screenshot.png
question=What do you see in this image?
```

**cURL Example:**
```bash
curl -X POST "http://localhost:8000/api/v1/qa/image" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@screenshot.png" \
  -F "question=What issues do you see in this UI?"
```

**Response:**
```json
{
  "question": "What issues do you see in this UI?",
  "answer": "I can see several UI elements in this screenshot. The navigation bar has...",
  "model": "gemini-2.0-flash-exp",
  "filename": "screenshot.png",
  "user_id": "abc123"
}
```

**Supported Image Formats:**
- JPEG (.jpg, .jpeg)
- PNG (.png)
- GIF (.gif)
- BMP (.bmp)
- WebP (.webp)

#### 3. Ask Question About PDF

**🌟 Special Feature:** PDF pages are automatically converted to **ultra HD 8K resolution (7680px width)** before being sent to Gemini for maximum quality analysis!

```http
POST /api/v1/qa/pdf
Content-Type: multipart/form-data
Authorization: Bearer YOUR_TOKEN

file=@document.pdf
question=Summarize this document
```

**cURL Example:**
```bash
curl -X POST "http://localhost:8000/api/v1/qa/pdf" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@compliance_doc.pdf" \
  -F "question=What are the main compliance requirements?"
```

**Response:**
```json
{
  "question": "What are the main compliance requirements?",
  "answer": "Based on this document, the main compliance requirements are:\n1. Data protection...",
  "model": "gemini-2.0-flash-exp",
  "filename": "compliance_doc.pdf",
  "pages": 12,
  "resolution": "8K Ultra HD (7680px width)",
  "user_id": "abc123"
}
```

**PDF Processing:**
- ✅ All pages converted to 8K resolution
- ✅ Maintains aspect ratio
- ✅ Multi-page analysis
- ✅ High-quality text extraction
- ✅ Clear image rendering

---

### 🎯 Model Fine-Tuning

Fine-tune Gemini models with your own training data.

#### 1. Upload Training Image

```http
POST /api/v1/finetune/upload-image
Content-Type: multipart/form-data
Authorization: Bearer YOUR_TOKEN

file=@training_image.png
prompt=What compliance issues are visible?
expected_output=Missing Bharat Connect logo and incorrect button placement
```

**cURL Example:**
```bash
curl -X POST "http://localhost:8000/api/v1/finetune/upload-image" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@training_sample.png" \
  -F "prompt=Identify compliance issues" \
  -F "expected_output=Logo missing, colors incorrect"
```

**Response:**
```json
{
  "image_id": "abc-123-def-456",
  "filename": "training_sample.png",
  "storage_path": "/app/storage/finetune/abc-123-def-456.png",
  "size_bytes": 245680,
  "format": "PNG",
  "prompt": "Identify compliance issues",
  "expected_output": "Logo missing, colors incorrect",
  "message": "Image uploaded successfully for fine-tuning"
}
```

#### 2. Start Fine-Tuning Job

```http
POST /api/v1/finetune/start
Content-Type: multipart/form-data
Authorization: Bearer YOUR_TOKEN

model_name=my-compliance-model-v1
base_model=gemini-1.5-pro
epochs=10
learning_rate=0.001
```

**cURL Example:**
```bash
curl -X POST "http://localhost:8000/api/v1/finetune/start" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "model_name=my-custom-model" \
  -F "base_model=gemini-1.5-pro" \
  -F "epochs=10" \
  -F "learning_rate=0.001"
```

**Response:**
```json
{
  "job_id": "ft-job-abc-123",
  "model_name": "my-custom-model",
  "base_model": "gemini-1.5-pro",
  "status": "pending",
  "training_images_count": 25,
  "epochs": 10,
  "learning_rate": 0.001,
  "created_at": "2025-11-07T12:30:00Z",
  "message": "Fine-tuning job created successfully. Job will start processing shortly."
}
```

**Parameters:**
- `model_name` (required): Name for your fine-tuned model
- `base_model` (optional): Base model to fine-tune (default: "gemini-1.5-pro")
- `epochs` (optional): Number of training epochs (default: 10)
- `learning_rate` (optional): Learning rate (default: 0.001)

#### 3. Check Fine-Tuning Status

```http
GET /api/v1/finetune/status/{job_id}
Authorization: Bearer YOUR_TOKEN
```

**cURL Example:**
```bash
curl -X GET "http://localhost:8000/api/v1/finetune/status/ft-job-abc-123" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response:**
```json
{
  "job_id": "ft-job-abc-123",
  "model_name": "my-custom-model",
  "base_model": "gemini-1.5-pro",
  "status": "running",
  "progress": 45,
  "epochs": 10,
  "training_images_count": 25,
  "created_at": "2025-11-07T12:30:00Z",
  "started_at": "2025-11-07T12:31:00Z",
  "completed_at": null,
  "error": null
}
```

**Status Values:**
- `pending`: Job created, waiting to start
- `running`: Currently training
- `completed`: Successfully finished
- `failed`: Error occurred
- `cancelled`: Manually stopped

---

## 🔑 Authentication Flow

```
1. Sign Up or Login
   ↓
2. Receive JWT Token (expires in 24 hours)
   ↓
3. Include in all requests:
   Authorization: Bearer {token}
   ↓
4. Use Q&A and Fine-Tuning APIs
```

---

## 📝 Complete Example Workflow

### Step 1: Register & Login
```bash
# Sign up
curl -X POST "http://localhost:8000/api/v1/auth/signup" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "johndoe",
    "email": "john@example.com",
    "phone": "+1234567890",
    "password": "SecurePass123!"
  }'

# Save the token from response
TOKEN="eyJhbGciOiJIUzI1NiIs..."
```

### Step 2: Ask Questions

**Text Question:**
```bash
curl -X POST "http://localhost:8000/api/v1/qa/text" \
  -H "Authorization: Bearer $TOKEN" \
  -F "question=Explain quantum computing"
```

**Image Question:**
```bash
curl -X POST "http://localhost:8000/api/v1/qa/image" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@screenshot.png" \
  -F "question=What UI issues are visible?"
```

**PDF Question (with 8K conversion!):**
```bash
curl -X POST "http://localhost:8000/api/v1/qa/pdf" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@report.pdf" \
  -F "question=Summarize the key findings"
```

### Step 3: Fine-Tune Model

**Upload Training Data:**
```bash
# Upload multiple training examples
curl -X POST "http://localhost:8000/api/v1/finetune/upload-image" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@example1.png" \
  -F "prompt=Identify issues" \
  -F "expected_output=Logo missing"

curl -X POST "http://localhost:8000/api/v1/finetune/upload-image" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@example2.png" \
  -F "prompt=Check compliance" \
  -F "expected_output=Colors incorrect"
```

**Start Training:**
```bash
curl -X POST "http://localhost:8000/api/v1/finetune/start" \
  -H "Authorization: Bearer $TOKEN" \
  -F "model_name=my-model-v1" \
  -F "epochs=10"

# Response: { "job_id": "ft-job-abc-123", ... }
```

**Check Status:**
```bash
curl -X GET "http://localhost:8000/api/v1/finetune/status/ft-job-abc-123" \
  -H "Authorization: Bearer $TOKEN"
```

---

## 🐍 Python Example

```python
import requests

BASE_URL = "http://localhost:8000/api/v1"

# 1. Sign up
response = requests.post(f"{BASE_URL}/auth/signup", json={
    "username": "johndoe",
    "email": "john@example.com",
    "phone": "+1234567890",
    "password": "SecurePass123!"
})
token = response.json()["access_token"]

# 2. Headers for authenticated requests
headers = {"Authorization": f"Bearer {token}"}

# 3. Ask text question
response = requests.post(
    f"{BASE_URL}/qa/text",
    headers=headers,
    data={"question": "What is AI?"}
)
print(response.json()["answer"])

# 4. Ask question about image
with open("screenshot.png", "rb") as f:
    response = requests.post(
        f"{BASE_URL}/qa/image",
        headers=headers,
        files={"file": f},
        data={"question": "What do you see?"}
    )
print(response.json()["answer"])

# 5. Ask question about PDF (with 8K conversion!)
with open("document.pdf", "rb") as f:
    response = requests.post(
        f"{BASE_URL}/qa/pdf",
        headers=headers,
        files={"file": f},
        data={"question": "Summarize this"}
    )
print(response.json()["answer"])

# 6. Upload training image
with open("training.png", "rb") as f:
    response = requests.post(
        f"{BASE_URL}/finetune/upload-image",
        headers=headers,
        files={"file": f},
        data={
            "prompt": "Identify issues",
            "expected_output": "Logo missing"
        }
    )
print(response.json())

# 7. Start fine-tuning
response = requests.post(
    f"{BASE_URL}/finetune/start",
    headers=headers,
    data={"model_name": "my-model", "epochs": 10}
)
job_id = response.json()["job_id"]

# 8. Check status
response = requests.get(
    f"{BASE_URL}/finetune/status/{job_id}",
    headers=headers
)
print(response.json())
```

---

## 🌟 Key Features

### PDF to 8K Conversion
- **Automatic**: No configuration needed
- **High Quality**: 7680px width (8K resolution)
- **Maintains Aspect Ratio**: Professional rendering
- **All Pages**: Multi-page analysis supported
- **Gemini Vision**: Best quality for AI analysis

### Authentication
- **JWT Tokens**: Secure, industry-standard
- **24-hour Expiry**: Long-lasting sessions
- **Bcrypt Hashing**: Secure password storage
- **Unique Users**: Email, phone, username uniqueness

### Gemini 2.0 Flash
- **Latest Model**: Best performance and accuracy
- **Multi-modal**: Text, images, PDFs
- **Fast**: Optimized for speed
- **Accurate**: High-quality responses

---

## 📊 Error Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 201 | Created (signup) |
| 400 | Bad request (invalid data) |
| 401 | Unauthorized (no/invalid token) |
| 403 | Forbidden (inactive user) |
| 404 | Not found (job/resource doesn't exist) |
| 409 | Conflict (duplicate user) |
| 413 | Payload too large (file >50MB) |
| 500 | Server error |

---

## 🔧 Configuration

### Environment Variables

```env
# MongoDB
MONGODB_URL=mongodb://mongo:27017
DATABASE_NAME=accord_compliance

# JWT Authentication
JWT_SECRET_KEY=your-secret-key-min-32-chars
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Google Gemini (REQUIRED for Q&A)
GOOGLE_API_KEY=your-gemini-api-key

# File Upload
MAX_FILE_SIZE_MB=50

# Logging
LOG_LEVEL=INFO
```

---

## 🧪 Testing

Run the automated test script:

```powershell
# PowerShell
.\test_simplified_apis.ps1
```

**Tests Covered:**
✅ User registration  
✅ User login  
✅ Text Q&A  
✅ Image Q&A (manual)  
✅ PDF Q&A (manual)  
✅ Fine-tune upload (manual)  
✅ Fine-tune start  
✅ Fine-tune status  

---

## 📚 Additional Resources

- **API Docs**: http://localhost:8000/docs
- **Redoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health
- **MongoDB UI**: http://localhost:8081

---

## 🎯 Summary

This simplified API provides exactly what you need:

✅ **8 Essential Endpoints**  
✅ **JWT Authentication**  
✅ **Gemini 2.0 Flash Integration**  
✅ **8K PDF Conversion**  
✅ **Model Fine-Tuning**  
✅ **Production-Ready**  

**No bloat. Just what matters.** 🚀

---

*Last Updated: November 7, 2025*

