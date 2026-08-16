"""
Central configuration for the RAG Tax & Regulatory Knowledge Assistant.
All values are overridable via a `.env` file (see .env.example).
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # LLM provider
    llm_provider: str = "groq"  # "groq" | "gemini"
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-1.5-flash"

    # Storage
    chroma_dir: str = "./chroma_db"
    sqlite_path: str = "./query_history.db"

    # Retrieval
    embedding_model: str = "all-MiniLM-L6-v2"
    top_k: int = 5
    chunk_size: int = 800
    chunk_overlap: int = 120


settings = Settings()
