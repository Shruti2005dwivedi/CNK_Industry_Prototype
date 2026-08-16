"""
Embedding & Vector Store Module (embedding half)
--------------------------------------------------
Wraps sentence-transformers so the rest of the app never has to think
about the underlying model. Swapping to Gemini/OpenAI embeddings later
only means changing this file.
"""
from functools import lru_cache

from app.config import settings


@lru_cache(maxsize=1)
def _get_model():
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(settings.embedding_model)


def embed_texts(texts: list[str]) -> list[list[float]]:
    model = _get_model()
    vectors = model.encode(texts, show_progress_bar=False, normalize_embeddings=True)
    return vectors.tolist()


def embed_query(query: str) -> list[float]:
    return embed_texts([query])[0]
