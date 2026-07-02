import os
import tempfile
import uuid

from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel

from app.document_loader import load_and_split
from app.rag_chain import query_documents as rag_query
from app.vector_store import add_documents

app = FastAPI(title="RAG-MCP Document Intelligence", version="1.0.0")


class QueryRequest(BaseModel):
    question: str


class QueryResponse(BaseModel):
    answer: str
    source_documents: list


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/ingest")
async def ingest(file: UploadFile = File(...)):
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in (".pdf", ".csv", ".xml"):
        raise HTTPException(400, f"Unsupported file type: {ext}")

    tmp_path = os.path.join(tempfile.gettempdir(), f"{uuid.uuid4()}{ext}")
    try:
        content = await file.read()
        with open(tmp_path, "wb") as f:
            f.write(content)

        chunks = load_and_split(tmp_path)
        add_documents(chunks)
        return {"message": f"Ingested {len(chunks)} chunks from {file.filename}", "chunks": len(chunks)}
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


@app.post("/query", response_model=QueryResponse)
def query(req: QueryRequest):
    try:
        result = rag_query(req.question)
        return QueryResponse(**result)
    except ValueError as e:
        raise HTTPException(500, str(e))
    except Exception as e:
        raise HTTPException(500, f"{type(e).__name__}: {e}")
