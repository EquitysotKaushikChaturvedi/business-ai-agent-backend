# Business AI Agent (Backend)

## Overview
**AI Backend System** designed to serve as the "Brain" for multiple businesses. It uses **OpenAI (GPT-4o)** for intelligence and **Redis** for memory/context management.

**Key Capabilities:**
- **Business Isolation**: Strictly separates data/memory by `business_id`.
- **RAG (Knowledge)**: Ingests PDFs, Docs, Websites, and Images (OCR).
- **Intelligent Chat**: Uses GPT-4o with professional behavior guardrails.
- **Stateless API**: HTTP REST API (FastAPI) ready for scaling.

## Architecture
- **Framework**: FastAPI (Python)
- **LLM**: OpenAI (Chat Completions API)
- **Memory**: Redis (Short-term chat history, TTL managed)
- **Storage**: Redis/FAISS (Vector store for RAG)
- **OCR**: Tesseract (Local binary required)

## Production Setup 

### 1. Prerequisites
- **Redis**: Must be running (Port 6379 default).
- **Tesseract OCR**: Installed on the machine (`apt install tesseract-ocr` or Windows installer).
- **OpenAI API Key**: A valid paid key.

### 2. Configuration
Create a `.env` file in the root directory (do not commit this file):

```bash
OPENAI_API_KEY="sk-..."    # Your Production Key
REDIS_HOST="localhost"
REDIS_PORT=6379
```

### 3. Running the Server
Install dependencies and run:

```bash
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## API Endpoints (No UI)

This backend exposes the following endpoints for your Frontend/App to connect to:

- `POST /chat`: Send message (Requires `business_id`, `session_id`).
- `POST /ingest/url`: Scrape and ingest a website.
- `POST /ingest/file`: Upload PDF/Doc/Image.
- `POST /ingest/text`: Raw text dump.
- `GET /health`: Server status.




