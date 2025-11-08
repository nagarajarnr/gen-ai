# Test Simplified Accord AI APIs
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "Testing Simplified Accord AI APIs" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Generate random user
$randomNum = Get-Random -Maximum 9999

# Test 1: Sign Up
Write-Host "1. Testing User Registration..." -ForegroundColor Yellow
$signupBody = @{
    username = "testuser$randomNum"
    email = "testuser$randomNum@example.com"
    phone = "+1555$(Get-Random -Minimum 1000000 -Maximum 9999999)"
    password = "SecurePass123!"
} | ConvertTo-Json

try {
    $signupResponse = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/auth/signup" `
        -Method Post `
        -ContentType "application/json" `
        -Body $signupBody `
        -ErrorAction Stop
    
    $token = $signupResponse.access_token
    Write-Host "✅ Sign up successful!" -ForegroundColor Green
    Write-Host "Token: $($token.Substring(0, 50))..." -ForegroundColor Gray
    Write-Host ""
} catch {
    Write-Host "❌ Sign up failed: $_" -ForegroundColor Red
    exit 1
}

# Test 2: Text Question
Write-Host "2. Testing Text Q&A..." -ForegroundColor Yellow
$textQuestion = @{
    question = "What is artificial intelligence?"
}

try {
    $headers = @{
        "Authorization" = "Bearer $token"
    }
    
    # Create multipart form data
    $boundary = [System.Guid]::NewGuid().ToString()
    $LF = "`r`n"
    
    $bodyLines = (
        "--$boundary",
        "Content-Disposition: form-data; name=`"question`"",
        "",
        "What is artificial intelligence?",
        "--$boundary--$LF"
    ) -join $LF
    
    $response = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/qa/text" `
        -Method Post `
        -Headers @{
            "Authorization" = "Bearer $token"
            "Content-Type" = "multipart/form-data; boundary=$boundary"
        } `
        -Body $bodyLines `
        -ErrorAction Stop
    
    Write-Host "✅ Text Q&A successful!" -ForegroundColor Green
    Write-Host "Question: $($response.question)" -ForegroundColor Gray
    Write-Host "Answer: $($response.answer.Substring(0, [Math]::Min(200, $response.answer.Length)))..." -ForegroundColor Gray
    Write-Host ""
} catch {
    Write-Host "⚠️  Text Q&A test: $_" -ForegroundColor Yellow
    Write-Host ""
}

# Test 3: Fine-tune - Upload Training Image
Write-Host "3. Testing Fine-tune Image Upload..." -ForegroundColor Yellow
Write-Host "⚠️  Skipping - requires actual image file" -ForegroundColor Yellow
Write-Host ""

# Test 4: Fine-tune - Start Job
Write-Host "4. Testing Fine-tune Start..." -ForegroundColor Yellow
$finetuneData = @{
    model_name = "my-custom-model-$randomNum"
    base_model = "gemini-1.5-pro"
    epochs = 5
    learning_rate = 0.001
}

try {
    # Create multipart form data
    $boundary = [System.Guid]::NewGuid().ToString()
    $LF = "`r`n"
    
    $bodyLines = (
        "--$boundary",
        "Content-Disposition: form-data; name=`"model_name`"",
        "",
        $finetuneData.model_name,
        "--$boundary",
        "Content-Disposition: form-data; name=`"base_model`"",
        "",
        $finetuneData.base_model,
        "--$boundary",
        "Content-Disposition: form-data; name=`"epochs`"",
        "",
        $finetuneData.epochs.ToString(),
        "--$boundary",
        "Content-Disposition: form-data; name=`"learning_rate`"",
        "",
        $finetuneData.learning_rate.ToString(),
        "--$boundary--$LF"
    ) -join $LF
    
    $finetuneResponse = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/finetune/start" `
        -Method Post `
        -Headers @{
            "Authorization" = "Bearer $token"
            "Content-Type" = "multipart/form-data; boundary=$boundary"
        } `
        -Body $bodyLines `
        -ErrorAction Stop
    
    $jobId = $finetuneResponse.job_id
    Write-Host "✅ Fine-tune job created!" -ForegroundColor Green
    Write-Host "Job ID: $jobId" -ForegroundColor Gray
    Write-Host "Status: $($finetuneResponse.status)" -ForegroundColor Gray
    Write-Host ""
    
    # Test 5: Check Job Status
    Write-Host "5. Testing Fine-tune Status Check..." -ForegroundColor Yellow
    $statusResponse = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/finetune/status/$jobId" `
        -Method Get `
        -Headers $headers `
        -ErrorAction Stop
    
    Write-Host "✅ Status check successful!" -ForegroundColor Green
    Write-Host "Model: $($statusResponse.model_name)" -ForegroundColor Gray
    Write-Host "Status: $($statusResponse.status)" -ForegroundColor Gray
    Write-Host "Progress: $($statusResponse.progress)%" -ForegroundColor Gray
    Write-Host ""
    
} catch {
    Write-Host "⚠️  Fine-tune test: $_" -ForegroundColor Yellow
    Write-Host ""
}

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "✅ Testing Complete!" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Available APIs:" -ForegroundColor White
Write-Host "  - POST /api/v1/auth/signup" -ForegroundColor Gray
Write-Host "  - POST /api/v1/auth/login" -ForegroundColor Gray
Write-Host "  - POST /api/v1/qa/text" -ForegroundColor Gray
Write-Host "  - POST /api/v1/qa/image" -ForegroundColor Gray
Write-Host "  - POST /api/v1/qa/pdf (with 8K conversion!)" -ForegroundColor Gray
Write-Host "  - POST /api/v1/finetune/upload-image" -ForegroundColor Gray
Write-Host "  - POST /api/v1/finetune/start" -ForegroundColor Gray
Write-Host "  - GET  /api/v1/finetune/status/{job_id}" -ForegroundColor Gray
Write-Host ""
Write-Host "API Docs: http://localhost:8000/docs" -ForegroundColor Cyan

