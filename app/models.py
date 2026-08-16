"""Pydantic schemas shared across the API."""
from typing import Optional
from pydantic import BaseModel, Field


class ChunkMetadata(BaseModel):
    source_document: str
    issuing_authority: Optional[str] = "Unknown"
    date_of_issue: Optional[str] = "Unknown"
    section_reference: Optional[str] = "Unknown"
    chunk_id: str
    page_number: Optional[int] = None


class RetrievedChunk(BaseModel):
    text: str
    metadata: ChunkMetadata
    score: float


class QueryRequest(BaseModel):
    query: str = Field(..., min_length=3, description="Natural-language tax/regulatory question")
    session_id: str = Field(default="default", description="Client-supplied session/user id for history tracking")
    top_k: Optional[int] = None


class Citation(BaseModel):
    source_document: str
    section_reference: Optional[str] = None
    date_of_issue: Optional[str] = None


class QueryResponse(BaseModel):
    answer: str
    citations: list[Citation]
    retrieved_chunks: list[RetrievedChunk]
    grounded: bool  # False -> "not found in indexed sources"


class IngestResponse(BaseModel):
    filename: str
    chunks_created: int
    status: str


class HistoryItem(BaseModel):
    id: int
    session_id: str
    query: str
    answer: str
    sources: str
    created_at: str
