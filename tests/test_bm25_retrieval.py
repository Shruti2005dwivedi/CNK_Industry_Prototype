import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.bm25_index import BM25Index

DOCS = [
    {"text": "Input tax credit cannot be claimed after the statutory deadline under Section 16(4).",
     "metadata": {"source_document": "circular_12.pdf"}},
    {"text": "RBI circular on KYC norms for periodic updation of customer accounts.",
     "metadata": {"source_document": "rbi_kyc.pdf"}},
    {"text": "SEBI guidelines on related party transactions and disclosure requirements.",
     "metadata": {"source_document": "sebi_rpt.pdf"}},
]


def test_bm25_ranks_relevant_doc_first():
    index = BM25Index(DOCS)
    results = index.search("input tax credit statutory deadline", top_k=3)
    assert results, "Expected at least one BM25 result"
    assert results[0]["metadata"]["source_document"] == "circular_12.pdf"


def test_bm25_returns_empty_for_no_match():
    index = BM25Index(DOCS)
    results = index.search("zzz nonexistent term qqq", top_k=3)
    assert results == []


if __name__ == "__main__":
    test_bm25_ranks_relevant_doc_first()
    test_bm25_returns_empty_for_no_match()
    print("All BM25 tests passed.")
