"""
Bulk-ingest every PDF in a folder straight into the vector store.
Useful for seeding the knowledge base before the API/frontend is even up.

Usage:
    python scripts/ingest_cli.py data/sample_docs
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tqdm import tqdm

from app.history import init_db
from app.ingestion import chunk_document
from app.vectorstore import get_vector_store


def main(folder: str):
    init_db()
    store = get_vector_store()
    pdf_paths = list(Path(folder).glob("*.pdf"))

    if not pdf_paths:
        print(f"No PDFs found in {folder}")
        return

    total = 0
    for path in tqdm(pdf_paths, desc="Ingesting"):
        chunks = chunk_document(str(path))
        total += store.add_chunks(chunks)

    print(f"Indexed {total} chunks from {len(pdf_paths)} document(s).")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python scripts/ingest_cli.py <folder_with_pdfs>")
        sys.exit(1)
    main(sys.argv[1])
