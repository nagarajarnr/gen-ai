# Sample Documents

This directory contains sample documents for testing and demonstration.

## Included Samples

- **sample_policy.txt**: Simple text compliance policy
- Add your own PDF and image files here for testing

## Using Sample Data

### Automatic Ingestion

Run the sample ingestion script:

```bash
make ingest-sample
# or
docker-compose exec api python scripts/ingest_samples.py
```

### Manual Ingestion

#### Text Document
```bash
curl -X POST "http://localhost:8000/api/v1/ingest/text" \
  -H "Content-Type: application/json" \
  -d @- <<EOF
{
  "text": "$(cat samples/sample_policy.txt)",
  "metadata": {"source": "samples", "type": "policy"}
}
EOF
```

#### PDF Document (if you add one)
```bash
curl -X POST "http://localhost:8000/api/v1/ingest/pdf" \
  -F "file=@samples/your_document.pdf" \
  -F 'metadata={"department": "legal"}'
```

#### Image (if you add one)
```bash
curl -X POST "http://localhost:8000/api/v1/ingest/image" \
  -F "file=@samples/your_image.png" \
  -F 'metadata={"type": "diagram"}'
```

## Testing Q&A

After ingesting documents:

```bash
curl -X POST "http://localhost:8000/api/v1/qa" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are the key data protection principles?",
    "scope": "all",
    "top_k": 5
  }'
```

## Adding Your Own Documents

You can add your own compliance documents to this directory:
- PDF files (`.pdf`)
- Images (`.jpg`, `.png`, `.gif`)
- Text files (`.txt`)

Then ingest them using the API or sample script.

