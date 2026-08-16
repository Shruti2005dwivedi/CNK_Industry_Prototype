"""
FastAPI backend for the RAG-Driven Tax & Regulatory Knowledge Assistant.

Endpoints:
  POST /ingest        -- upload a PDF, get it parsed/chunked/embedded/indexed
  POST /query          -- ask a natural-language question, get a cited answer
  GET  /history/{sid}  -- retrieve past queries + sources for a session
  GET  /health         -- liveness check
"""
import os
import shutil
import tempfile

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from app.generation import generate_answer
from app.history import get_history, init_db, log_query
from app.ingestion import chunk_document
from app.models import (
    ChunkMetadata,
    Citation,
    HistoryItem,
    IngestResponse,
    QueryRequest,
    QueryResponse,
    RetrievedChunk,
)
from app.retrieval import hybrid_search
from app.vectorstore import get_vector_store

app = FastAPI(
    title="RAG-Driven Tax & Regulatory Knowledge Assistant",
    description="Semantic + keyword retrieval over tax circulars/notifications with citation-grounded answers.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten this before real deployment
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    init_db()
    get_vector_store()  # warms up the Chroma client


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/ingest", response_model=IngestResponse)
async def ingest(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Only PDF files are supported by this endpoint.")

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name

    try:
        chunks = chunk_document(tmp_path)
        store = get_vector_store()
        count = store.add_chunks(chunks)
    finally:
        # Close file handles before deletion on Windows
        import time
        time.sleep(0.5)  # Give Windows time to release file handles
        try:
            os.unlink(tmp_path)
        except PermissionError:
            pass  # Ignore if file is still locked

    return IngestResponse(filename=file.filename, chunks_created=count, status="indexed")


@app.post("/query", response_model=QueryResponse)
def query(req: QueryRequest):
    chunks = hybrid_search(req.query, top_k=req.top_k)
    answer, grounded = generate_answer(req.query, chunks)

    citations = []
    if grounded:
        seen = set()
        for c in chunks:
            m = c["metadata"]
            key = (m.get("source_document"), m.get("section_reference"))
            if key not in seen:
                seen.add(key)
                citations.append(
                    Citation(
                        source_document=m.get("source_document", "Unknown"),
                        section_reference=m.get("section_reference"),
                        date_of_issue=m.get("date_of_issue"),
                    )
                )

    retrieved = [
        RetrievedChunk(
            text=c["text"],
            score=c["score"],
            metadata=ChunkMetadata(
                source_document=c["metadata"].get("source_document", "Unknown"),
                issuing_authority=c["metadata"].get("issuing_authority"),
                date_of_issue=c["metadata"].get("date_of_issue"),
                section_reference=c["metadata"].get("section_reference"),
                chunk_id=c["metadata"].get("source_document", "") + str(c["metadata"].get("page_number", "")),
                page_number=c["metadata"].get("page_number"),
            ),
        )
        for c in chunks
    ]

    log_query(
        session_id=req.session_id,
        query=req.query,
        answer=answer,
        sources=[c.model_dump() for c in citations],
        grounded=grounded,
    )

    return QueryResponse(answer=answer, citations=citations, retrieved_chunks=retrieved, grounded=grounded)


@app.get("/history/{session_id}", response_model=list[HistoryItem])
def history(session_id: str):
    rows = get_history(session_id)
    return [
        HistoryItem(
            id=r["id"],
            session_id=r["session_id"],
            query=r["query"],
            answer=r["answer"],
            sources=r["sources"],
            created_at=r["created_at"],
        )
        for r in rows
    ]
