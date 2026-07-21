"""Centralized settings, loaded once from .env.

Every other module reads configuration through `settings`, never
os.getenv() directly -- this is the single place that knows about
environment variables.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite:///./ecommerce.db"

    ollama_base_url: str = "http://localhost:11434"
    llm_model: str = "phi"
    max_tokens: int = 256
    llm_timeout_seconds: int = 45

    embedding_model: str = "all-MiniLM-L6-v2"

    environment: str = "development"

    class Config:
        env_file = ".env"


settings = Settings()
