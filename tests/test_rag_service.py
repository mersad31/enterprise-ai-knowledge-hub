import pytest



pytestmark = pytest.mark.asyncio

async def test_rag_query_without_cache(rag_service):
    service, mock_llm, mock_embedding, mock_vector_store = rag_service

    mock_embedding.embed_text.return_value = [0.1] * 768
    mock_vector_store.search.return_value = [
        {
            "text": "لپ‌تاپ ۵۰ میلیون",
            "score": 0.9,
            "metadata": {}
        }
    ]
    mock_llm.generate.return_value = {
        "content": "قیمت ۵۰ میلیون",
        "model": "test"
    }

    result = await service.query(question="قیمت لپتاپ", top_k=3)

    assert result["answer"] == "قیمت ۵۰ میلیون"
    assert result["model_used"] == "test"


async def test_rag_query_with_cache(rag_service_with_cache):
    service, mock_llm, mock_embedding, mock_vector_store, mock_cache = rag_service_with_cache

    mock_embedding.embed_text.return_value = [0.1] * 768
    mock_vector_store.search.return_value = [
        {
            "text": "لپ‌تاپ ۵۰ میلیون",
            "score": 0.9,
            "metadata": {}
        }
    ]
    mock_cache.get.return_value = "test string"


    result = await service.query(question="قیمت لپتاپ", top_k=3)

    assert  result["answer"] == "test string"
    assert result["model_used"] == "cache"
    mock_llm.generate.assert_not_called()


async def test_rag_query_with_guardrails(rag_service_with_guardrails):
    service, mock_llm, mock_embedding, mock_vector_store, mock_guardrails = rag_service_with_guardrails

    mock_embedding.embed_text.return_value = [0.1] * 768
    mock_vector_store.search.return_value = []
    mock_guardrails.check_topic.return_value = "سوال خارج از دامنه است"

    result = await service.query(question="قیمت لپتاپ", top_k=3)

    assert result["model_used"] == "blocked"
    mock_llm.generate.assert_not_called()