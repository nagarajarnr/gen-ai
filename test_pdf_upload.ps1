# Test PDF Upload Script
$url = "http://localhost:8000/api/v1/ingest/pdf"
$pdfPath = "C:/Users/plutosone-munisekhar/Downloads/Compressed-Webguidelines.pdf"
$metadata = '{"department": "legal", "classification": "internal"}'

# Using curl.exe (if available)
curl.exe --location $url `
  --form "file=@$pdfPath" `
  --form "metadata=$metadata"

