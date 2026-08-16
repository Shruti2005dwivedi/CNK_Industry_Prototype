"""
Retrieval Module
------------------
Combines semantic similarity (ChromaDB) with keyword search (BM25) using
Reciprocal Rank Fusion (RRF) -- this is what gives good precision for
queries that mention an exact section/circular number, while still
handling queries phrased nothing like the source statute.
"""
from app.bm25_index import BM25Index
from app.config import settings
from app.vectorstore import get_vector_store

RRF_K = 60  # standard smoothing constant for reciprocal rank fusion


def _chunk_key(item: dict) -> str:
    m = item["metadata"]
    return f'{m.get("source_document")}::{m.get("page_number")}::{item["text"][:50]}'


def hybrid_search(query: str, top_k: int | None = None) -> list[dict]:
    top_k = top_k or settings.top_k
    store = get_vector_store()

    semantic_results = store.semantic_search(query, top_k=top_k * 3)

    all_docs = store.all_documents()
    bm25 = BM25Index(all_docs)
    keyword_results = bm25.search(query, top_k=top_k * 3)

    # Reciprocal Rank Fusion
    fused_scores: dict[str, float] = {}
    item_lookup: dict[str, dict] = {}

    for rank, item in enumerate(semantic_results):
        key = _chunk_key(item)
        fused_scores[key] = fused_scores.get(key, 0) + 1 / (RRF_K + rank + 1)
        item_lookup[key] = item

    for rank, item in enumerate(keyword_results):
        key = _chunk_key(item)
        fused_scores[key] = fused_scores.get(key, 0) + 1 / (RRF_K + rank + 1)
        item_lookup.setdefault(key, item)

    ranked_keys = sorted(fused_scores, key=lambda k: fused_scores[k], reverse=True)[:top_k]
    reranked = []
    for key in ranked_keys:
        item = item_lookup[key]
        reranked.append({**item, "score": fused_scores[key]})
    return reranked
