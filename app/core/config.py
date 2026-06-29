from functools import lru_cache
from typing import Literal, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "CV-Project"
    app_env: Literal["development", "staging", "production"] = "development"
    debug: bool = False

    api_host: str = "0.0.0.0"
    api_port: int = 8000

    llm_proxy_url: str
    llm_api_key: str = Field(..., repr=False)
    llm_default_model: str = "gpt-4o-mini"

    ollama_base_url: str = "http://localhost:11434"
    ollama_fallback_model: str = "llama3"

    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: Optional[str] = None
    qdrant_collection: str = "documents"

    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""
    langfuse_host: str = "https://cloud.langfuse.com"

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"
    

@lru_cache
def get_settings() -> Settings:
    return Settings()