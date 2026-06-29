from functools import lru_cache

from qdrant_client import QdrantClient

from fastapi import Depends

from app.core.config import get_settings

from app.services.vector_store import QdrantVectorStore
from app.services.embedding_service import OllamaEmbedding
from app.services.llm_service import LLMService
from app.services.rag_service import RAGService
from app.services.document_parser import DocumentParser
from app.services.cache_service import SemanticCache


settings = get_settings()

@lru_cache
def get_qdrant_client() -> QdrantClient:
    """ Get cached Qdrant client instance. """
    return QdrantClient(
        url=settings.qdrant_url,
        api_key=settings.qdrant_api_key if settings.qdrant_api_key else None,
        timeout=30,
    )

@lru_cache
def get_vector_store() -> QdrantVectorStore:
    """
    Get QdrantVectorStore instance with dependency injection.

    This is a FastAPI dependency factory.
    """
    client = get_qdrant_client()
    return QdrantVectorStore(
        client=client,
        collection_name=settings.qdrant_collection,
    )


@lru_cache
def get_embedding_service() -> OllamaEmbedding:
    """Dependency injection for embedding service"""
    return OllamaEmbedding(
        base_url=settings.ollama_base_url,
        model="nomic-embed-text"
    )


@lru_cache
def get_llm_service() -> LLMService:
    """ Get LLMService instance with dependency injection. """
    return LLMService()


@lru_cache
def get_semantic_cache(
        embedding_service: OllamaEmbedding = Depends(get_embedding_service),
        vector_store: QdrantVectorStore = Depends(get_vector_store),
) -> SemanticCache:
    """ Get SemanticCache instance with dependency injection. """

    return SemanticCache(
        embedding_service=embedding_service,
        vector_store=vector_store
    )

@lru_cache
def get_rag_service(
        llm_service: LLMService = Depends(get_llm_service),
        vector_store: QdrantVectorStore = Depends(get_vector_store),
        embedding_service: OllamaEmbedding = Depends(get_embedding_service),
        cache: SemanticCache = Depends(get_semantic_cache),
) -> RAGService:
    """ Get RAGService instance with dependency injection. """
    from app.guardrails import GuardrailsService, get_guardrails_service

    guardrails_service: GuardrailsService = Depends(get_guardrails_service)

    return RAGService(
        llm_service=llm_service,
        vector_store=vector_store,
        embedding_service=embedding_service,
        cache=cache,
        guardrails_service=guardrails_service,
    )

@lru_cache
def get_document_parser() -> DocumentParser:
    """ Get DocumentParser instance with dependency injection. """
    return DocumentParser()

