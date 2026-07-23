"""Centralized settings, loaded once from .env.

Every other module reads configuration through `settings`, never
os.getenv() directly -- this is the single place that knows about
environment variables.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./ecommerce.db"

    ollama_base_url: str = "http://localhost:11434"
    llm_model: str = "phi"
    max_tokens: int = 256
    llm_timeout_seconds: int = 45

    # Master switch for the language model. When False, the system runs
    # in "safe mode": intent detection uses keyword matching only and
    # replies skip the friendly LLM-written opener. All decisions,
    # product search, and FAQ answers are unaffected -- they never used
    # the LLM. Lets the app run with a much smaller memory footprint if
    # needed. Default True (full quality).
    use_llm: bool = True

    embedding_model: str = "all-MiniLM-L6-v2"

    environment: str = "development"


settings = Settings()
