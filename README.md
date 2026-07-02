# RAG Document Intelligence System

A production-ready **Retrieval-Augmented Generation (RAG)** API that ingests documents (PDF, CSV, XML) and answers questions against them using Google's Gemini LLM with vector search — deployable via Docker, Kubernetes, and Terraform.

---

## Core Motive

Most LLMs are limited to their training data and cannot answer questions about private or custom documents. This system solves that by:

1. **Ingesting** documents (PDF, CSV, XML) — parsing, chunking, and indexing them into a vector database
2. **Retrieving** the most relevant chunks for a user's question using semantic similarity search
3. **Generating** a grounded answer using Gemini 2.5 Flash — with strict fact-attribution to prevent hallucination

This enables **secure, private Q&A over your own documents** without sending your data to train third-party models.

---

## Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| **LLM** | Google Gemini 2.5 Flash (via `langchain-google-genai`) | Answer generation with fact-attribution |
| **Embeddings** | `all-MiniLM-L6-v2` (HuggingFace, local & free) | Converts text chunks to vector embeddings |
| **Vector Store** | ChromaDB (persistent) | Stores & retrieves document embeddings |
| **Orchestration** | LangChain | RAG chain: retrieval + LLM composition |
| **API Framework** | FastAPI + Pydantic | REST endpoints for ingest, query, health |
| **Document Parsing** | PyPDF, CSV, lxml | Multi-format document loading |
| **MCP** | Model Context Protocol | Expose RAG as MCP tools for AI agents |
| **Containerization** | Docker / Docker Compose | Single-command deployment |
| **Orchestration** | Kubernetes (K8s) | Production-grade scaling (2 replicas + PVC) |
| **Infrastructure** | Terraform (AWS S3) | Document storage provisioning |

---

## Architecture & Workflow

```
User Uploads Document (PDF/CSV/XML)
         │
         ▼
┌─────────────────────┐
│   /ingest endpoint   │
│  FastAPI + LangChain │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  Document Loader    │
│  (PyPDF / CSV / XML)│
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  Section Splitting  │
│  (heading detection)│
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  Chunking           │
│  RecursiveCharacter │
│  TextSplitter       │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  Embedding          │
│  all-MiniLM-L6-v2   │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  ChromaDB           │
│  (Vector Store)     │
└─────────────────────┘

User Asks Question
         │
         ▼
┌─────────────────────┐
│   /query endpoint   │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  Similarity Search  │
│  (top-k=4 chunks)   │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  Gemini 2.5 Flash   │
│  (grounded answer   │
│   with attribution) │
└─────────┬───────────┘
          │
          ▼
   Answer + Sources
```

---

## Quick Start

### Prerequisites

- Python 3.11+
- A **Google Gemini API key** — get one free at [Google AI Studio](https://aistudio.google.com/app/apikey)

### 1. Clone & Setup

```bash
git clone https://github.com/shrey2522/RAG.git
cd RAG
```

### 2. Environment Variables

Create a `.env` file (or edit the existing one):

```env
GOOGLE_API_KEY=your_gemini_api_key_here
CHROMA_PERSIST_DIR=storage/chroma_db
EMBEDDING_MODEL=all-MiniLM-L6-v2
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
COLLECTION_NAME=documents
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the API

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

API will be available at `http://localhost:8000`

### 5. Ingest a Document

```bash
curl -X POST -F "file=@path/to/document.pdf" http://localhost:8000/ingest
```

### 6. Ask a Question

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What does this document say about X?"}'
```

---

## API Reference

### `GET /health`

Health check endpoint.

**Response:** `{"status": "ok"}`

---

### `POST /ingest`

Upload a document (PDF, CSV, or XML) for indexing.

| Parameter | Type | Description |
|---|---|---|
| `file` | File (multipart) | The document file to ingest |

**Response:**
```json
{
  "message": "Ingested 24 chunks from report.pdf",
  "chunks": 24
}
```

---

### `POST /query`

Ask a question against the ingested documents.

| Parameter | Type | Description |
|---|---|---|
| `question` | string | Your question |

**Response:**
```json
{
  "answer": "According to the 'Key Innovations' section, the company introduced...",
  "source_documents": [
    {
      "content": "The relevant text chunk...",
      "source": "report.pdf"
    }
  ]
}
```

---

## Docker Deployment

### Using Docker Compose (Recommended)

```bash
docker compose up --build
```

This builds the image and starts the container on port `8000` with:
- Environment variables from `.env`
- Persistent volume for ChromaDB (`./storage:/app/storage`)

### Using Docker Directly

```bash
docker build -t rag-api .
docker run -p 8000:8000 --env-file .env -v ./storage:/app/storage rag-api
```

---

## Kubernetes Deployment

Deploy to any K8s cluster with 2 replicas and persistent storage:

```bash
kubectl apply -f infra/k8s/deployment.yaml
kubectl apply -f infra/k8s/service.yaml
```

**Prerequisites:**
- A Kubernetes secret `rag-secrets` with key `google_api_key`
- A default StorageClass for PVC

---

## Terraform (AWS S3)

Provision an S3 bucket for document storage with versioning and encryption:

```bash
cd infra/terraform
terraform init
terraform apply -var="aws_region=us-east-1" -var="bucket_name=my-rag-documents"
```

---

## MCP Integration

The system also exposes RAG capabilities as MCP (Model Context Protocol) tools, allowing AI agents to query your documents programmatically.

Run the MCP server:

```bash
python -c "from app.mcp_server import start_mcp_thread; start_mcp_thread()"
```

Available tools:
- `query_documents` — Ask a question and get answer with sources
- `list_sources` — List all document sources in the vector store

---

## Project Structure

```
Rag/
├── app/
│   ├── main.py              # FastAPI application (endpoints)
│   ├── config.py            # Environment configuration
│   ├── document_loader.py   # PDF/CSV/XML loading & chunking
│   ├── vector_store.py      # ChromaDB vector store management
│   ├── rag_chain.py         # LangChain RAG chain (Gemini + retrieval)
│   ├── mcp_server.py        # MCP tool server for AI agents
│   └── __init__.py
├── infra/
│   ├── k8s/
│   │   ├── deployment.yaml  # K8s Deployment + PVC
│   │   └── service.yaml     # LoadBalancer service
│   └── terraform/
│       ├── main.tf          # AWS S3 bucket with versioning + encryption
│       ├── variables.tf
│       └── outputs.tf
├── data/                    # Sample documents (gitignored)
├── storage/                 # ChromaDB persistent storage (gitignored)
├── Dockerfile               # Python 3.11-slim container
├── docker-compose.yml       # Single-service compose
├── requirements.txt         # Python dependencies
└── .env                     # Environment variables (gitignored)
```

---

## Security Notes

- **NEVER commit your `.env` file** — it contains your `GOOGLE_API_KEY`. The `.gitignore` already excludes it.
- For production, inject secrets via environment variables (Docker secrets, K8s Secrets, or your CI/CD platform).
- The vector store is local by default. For team use, configure ChromaDB to use a shared backend.
