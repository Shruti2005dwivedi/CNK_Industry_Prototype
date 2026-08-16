"""
Document Ingestion & Preprocessing Module
------------------------------------------
Parses PDFs (with OCR fallback for scanned pages), splits them into
semantically coherent chunks, and tags each chunk with metadata
(source document, issuing authority, date of issue, section reference)
so the generation step can attach citations later.
"""
import os
import re
import uuid
from dataclasses import dataclass, field

from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.config import settings

try:
    import pymupdf as fitz  # PyMuPDF (new import name; falls back to legacy below)
except ImportError:  # pragma: no cover
    try:
        import fitz  # legacy PyMuPDF import
    except ImportError:
        fitz = None

try:
    import pytesseract
    from PIL import Image
    import io
    OCR_AVAILABLE = True
except ImportError:  # pragma: no cover
    OCR_AVAILABLE = False


@dataclass
class Chunk:
    text: str
    source_document: str
    chunk_id: str
    page_number: int
    issuing_authority: str = "Unknown"
    date_of_issue: str = "Unknown"
    section_reference: str = "Unknown"


DATE_PATTERN = re.compile(
    r"\b(\d{1,2}[-/](?:\d{1,2}|[A-Za-z]{3,9})[-/]\d{2,4})\b"
)
SECTION_PATTERN = re.compile(
    r"\b(Section\s+\d+[A-Za-z]*|Circular\s+No\.?\s*[\w/-]+|Notification\s+No\.?\s*[\w/-]+)\b",
    re.IGNORECASE,
)
AUTHORITY_KEYWORDS = {
    "cbdt": "CBDT",
    "cbic": "CBIC",
    "rbi": "RBI",
    "sebi": "SEBI",
    "gst council": "GST Council",
    "income tax department": "Income Tax Department",
}


def _guess_authority(text: str) -> str:
    lowered = text.lower()
    for key, label in AUTHORITY_KEYWORDS.items():
        if key in lowered:
            return label
    return "Unknown"


def _guess_date(text: str) -> str:
    match = DATE_PATTERN.search(text)
    return match.group(1) if match else "Unknown"


def _guess_section(text: str) -> str:
    match = SECTION_PATTERN.search(text)
    return match.group(1) if match else "Unknown"


def _ocr_page(page) -> str:
    """OCR fallback for scanned/image-only pages."""
    if not OCR_AVAILABLE:
        return ""
    try:
        pix = page.get_pixmap(dpi=200)
        img = Image.open(io.BytesIO(pix.tobytes("png")))
        return pytesseract.image_to_string(img)
    except Exception as e:
        # If OCR fails, return empty string instead of crashing
        print(f"OCR failed: {e}")
        return ""


def extract_pages(pdf_path: str) -> list[tuple[int, str]]:
    """Returns a list of (page_number, text) tuples, using OCR fallback
    whenever a page yields negligible extractable text (i.e. it's scanned)."""
    if fitz is None:
        raise RuntimeError("PyMuPDF (fitz) is not installed. Run: pip install PyMuPDF")

    pages = []
    doc = fitz.open(pdf_path)
    for i, page in enumerate(doc, start=1):
        text = page.get_text("text").strip()
        if len(text) < 20 and OCR_AVAILABLE:  # likely scanned / image-only page
            try:
                text = _ocr_page(page).strip()
            except Exception as e:
                print(f"OCR failed for page {i}: {e}")
                # Continue with extracted text even if OCR fails
        pages.append((i, text))
    doc.close()
    return pages


def chunk_document(pdf_path: str) -> list[Chunk]:
    """Full ingestion pipeline for a single PDF: extract -> chunk -> tag metadata."""
    filename = os.path.basename(pdf_path)
    pages = extract_pages(pdf_path)

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    chunks: list[Chunk] = []
    for page_number, page_text in pages:
        if not page_text.strip():
            continue
        for piece in splitter.split_text(page_text):
            if not piece.strip():
                continue
            chunks.append(
                Chunk(
                    text=piece.strip(),
                    source_document=filename,
                    chunk_id=str(uuid.uuid4()),
                    page_number=page_number,
                    issuing_authority=_guess_authority(piece),
                    date_of_issue=_guess_date(piece),
                    section_reference=_guess_section(piece),
                )
            )
    return chunks


def chunk_plain_text(text: str, source_document: str) -> list[Chunk]:
    """Same pipeline but for already-extracted plain text (e.g. .txt uploads,
    or for local testing without a PDF binary)."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks = []
    for piece in splitter.split_text(text):
        if not piece.strip():
            continue
        chunks.append(
            Chunk(
                text=piece.strip(),
                source_document=source_document,
                chunk_id=str(uuid.uuid4()),
                page_number=1,
                issuing_authority=_guess_authority(piece),
                date_of_issue=_guess_date(piece),
                section_reference=_guess_section(piece),
            )
        )
    return chunks
