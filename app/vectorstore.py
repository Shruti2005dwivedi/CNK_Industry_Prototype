"""
Embedding & Vector Store Module (storage half)
-------------------------------------------------
Uses ChromaDB as a self-hosted, zero-cost vector store for the prototype
(same role pgvector/Pinecone play in the original design doc). Because
Chroma speaks a simple add/query API, migrating to pgvector or Pinecone
later just means swapping this module.
"""
import chromadb
from chromadb.config import Settings as ChromaSettings

from app.config import settings
from app.embeddings import embed_texts, embed_query
from app.ingestion import Chunk

COLLECTION_NAME = "tax_regulatory_docs"


class VectorStore:
    def __init__(self):
        self.client = chromadb.PersistentClient(
            path=settings.chroma_dir,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        self.collection = self.client.get_or_create_collection(
            name=COLLECTION_NAME, metadata={"hnsw:space": "cosine"}
        )

    def add_chunks(self, chunks: list[Chunk]) -> int:
        if not chunks:
            return 0
        vectors = embed_texts([c.text for c in chunks])
        self.collection.add(
            ids=[c.chunk_id for c in chunks],
            embeddings=vectors,
            documents=[c.text for c in chunks],
            metadatas=[
                {
                    "source_document": c.source_document,
                    "issuing_authority": c.issuing_authority,
                    "date_of_issue": c.date_of_issue,
                    "section_reference": c.section_reference,
                    "page_number": c.page_number,
                }
                for c in chunks
            ],
        )
        return len(chunks)

    def semantic_search(self, query: str, top_k: int = 5) -> list[dict]:
        if self.collection.count() == 0:
            return []
        query_vector = embed_query(query)
        results = self.collection.query(query_embeddings=[query_vector], n_results=top_k)
        return self._format(results)

    def all_documents(self) -> list[dict]:
        """Used by the BM25 keyword index to build/rebuild itself."""
        if self.collection.count() == 0:
            return []
        data = self.collection.get(include=["documents", "metadatas"])
        return [
            {"id": _id, "text": doc, "metadata": meta}
            for _id, doc, meta in zip(data["ids"], data["documents"], data["metadatas"])
        ]

    @staticmethod
    def _format(results: dict) -> list[dict]:
        out = []
        docs = results.get("documents", [[]])[0]
        metas = results.get("metadatas", [[]])[0]
        dists = results.get("distances", [[]])[0]
        for doc, meta, dist in zip(docs, metas, dists):
            similarity = 1 - dist  # cosine distance -> similarity
            out.append({"text": doc, "metadata": meta, "score": similarity})
        return out


_store: VectorStore | None = None


def get_vector_store() -> VectorStore:
    global _store
    if _store is None:
        _store = VectorStore()
    return _store
