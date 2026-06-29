import pytest

from app.guardrails.service import GuardrailsService
from unittest.mock import AsyncMock

from app.services.llm_service import LLMService

from app.services.rag_service import RAGService

@pytest.fixture
def guardrails_service():
    """Create a GuardrailsService with a fake LLM for testing."""
    fake_llm = AsyncMock()
    return GuardrailsService(
        llm_service=fake_llm,
        enabled=True,
    )

@pytest.fixture
def enabled_guardrails():
    return GuardrailsService(llm_service=AsyncMock(), enabled=True)

@pytest.fixture
def disabled_guardrails():
    return GuardrailsService(llm_service=AsyncMock(), enabled=False)

@pytest.fixture
def service():
    return LLMService()

@pytest.fixture
def rag_service():
    mock_llm = AsyncMock()
    mock_embedding =  AsyncMock()
    mock_vector_store = AsyncMock()

    service = RAGService(
        llm_service=mock_llm,
        vector_store=mock_vector_store,
        embedding_service=mock_embedding,
        cache=None,
        guardrails_service=None,
    )
    return service, mock_llm, mock_embedding, mock_vector_store

@pytest.fixture
def rag_service_with_cache():
    mock_llm = AsyncMock()
    mock_embedding = AsyncMock()
    mock_vector_store = AsyncMock()
    mock_cache= AsyncMock()

    service = RAGService(
        llm_service=mock_llm,
        vector_store=mock_vector_store,
        embedding_service=mock_embedding,
        cache=mock_cache,
        guardrails_service=None,
    )
    return service, mock_llm, mock_embedding, mock_vector_store, mock_cache

@pytest.fixture
def rag_service_with_guardrails():
    mock_llm = AsyncMock()
    mock_embedding = AsyncMock()
    mock_vector_store = AsyncMock()
    mock_guardrails = AsyncMock()

    service = RAGService(
        llm_service=mock_llm,
        vector_store=mock_vector_store,
        embedding_service=mock_embedding,
        cache=None,
        guardrails_service=mock_guardrails,
    )
    return service, mock_llm, mock_embedding, mock_vector_store, mock_guardrails
