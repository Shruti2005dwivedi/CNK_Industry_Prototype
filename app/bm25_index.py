"""
Lightweight BM25 keyword index used alongside semantic search.
Rebuilt in-memory from whatever is currently in the vector store, so it
never drifts out of sync with a separate copy of the data.
"""
import re

from rank_bm25 import BM25Okapi

_TOKEN_RE = re.compile(r"[A-Za-z0-9]+")


def _tokenize(text: str) -> list[str]:
    return _TOKEN_RE.findall(text.lower())


class BM25Index:
    def __init__(self, documents: list[dict]):
        """documents: list of {"text":..., "metadata":...}"""
        self.documents = documents
        corpus = [_tokenize(d["text"]) for d in documents]
        self.bm25 = BM25Okapi(corpus) if corpus else None

    def search(self, query: str, top_k: int = 5) -> list[dict]:
        if not self.bm25:
            return []
        scores = self.bm25.get_scores(_tokenize(query))
        ranked = sorted(zip(self.documents, scores), key=lambda x: x[1], reverse=True)[:top_k]
        return [{"text": d["text"], "metadata": d["metadata"], "score": float(s)} for d, s in ranked if s > 0]
