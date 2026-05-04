"""Central configuration via pydantic-settings."""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # LLM
    llm_base_url: str = "https://api.openai.com/v1"
    llm_api_key: str = "sk-placeholder"
    llm_model: str = "gpt-4o-mini"

    # Embeddings & reranking
    embedding_model: str = "all-MiniLM-L6-v2"
    reranker_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"

    # ChromaDB
    chroma_persist_dir: str = "./chroma_db"
    chroma_collection: str = "rag_documents"

    # Retrieval
    top_k_retrieval: int = 20
    top_k_rerank: int = 5
    max_tokens: int = 1024
    temperature: float = 0.2

    log_level: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    return Settings()
