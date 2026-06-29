import pytest

from unittest.mock import AsyncMock, patch






pytestmark = pytest.mark.asyncio


@patch("app.services.llm_service.litellm.acompletion")
async def test_generate_success(mock_completion, service):
    mock_response = AsyncMock()
    mock_response.choices = [AsyncMock()]
    mock_response.choices[0].message.content = "test answer"
    mock_response.model = "test-model"
    mock_completion.return_value = mock_response

    result = await service.generate(prompt="hello", system_prompt="you are helpful")

    assert result["content"] == "test answer"
    assert result["model"] == "test-model"


@patch("app.services.llm_service.litellm.acompletion")
async def test_generate_fallback(mock_completion, service):
    mock_response = AsyncMock()
    mock_response.choices = [AsyncMock()]
    mock_response.choices[0].message.content = "test answer"
    mock_response.model = "test-model"

    mock_completion.side_effect = [Exception("fall_back model failed"), mock_response]

    result = await service.generate(prompt="hello", system_prompt="you are helpful")

    assert result["content"] == "test answer"
    assert result["model"] == "test-model"
