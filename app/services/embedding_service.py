import httpx

from typing import List
from app.core.config import get_settings
from app.core.exceptions import EmbeddingError
from app.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


class OllamaEmbedding:
    """Embedding service using Ollama local models"""

    def __init__(
            self,
            base_url: str,
            model: str = "nomic-embed-text"
    ):
        self.base_url = base_url.strip('/')
        self.model = model
        self.client = httpx.AsyncClient(timeout=30.0)
        logger.info(
            "Initialized Ollama embedding",
            extra={
                "base_url": base_url,
                "model": model,
            }
        )

    async def embed_text(self, text: str) -> List[float]:
            """Generate embedding for a single text"""
            try:
                response = await self.client.post(
                    f"{self.base_url}/api/embeddings",
                    json={
                        "model": self.model,
                        "prompt": text
                    }
                )
                response.raise_for_status()
                data = response.json()
                return data["embedding"]

            except Exception as e:
                logger.error(
                    "Ollama embedding failed",
                    extra={
                        "error": str(e),
                        "text_length": len(text)
                    }
                )
                raise EmbeddingError(f"Ollama embedding failed: {e}")


    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
            """Generate embeddings for multiple texts"""
            embeddings = []
            for text in texts:
                emb = await self.embed_text(text)
                embeddings.append(emb)
            logger.info(
                "Generated embeddings",
                extra={
                    "batch_size": len(texts)
                }
            )
            return embeddings


    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()


