import litellm

from app.core.config import get_settings
from app.core.exceptions import LLMError
from app.core.logging import get_logger


logger = get_logger(__name__)
settings = get_settings()


class LLMService:
    """Central LLM gateway with model routing and fallback."""
    def __init__(self):
        self.primary_model = settings.llm_default_model
        self.fallback_model = f"ollama/{settings.ollama_fallback_model}"

    async def generate(self, prompt: str, system_prompt: str | None = None) -> dict:
        messages = []
        if system_prompt:
            messages.append({
                "role": "system",
                "content": system_prompt
            })
        messages.append({
            "role": "user",
            "content": prompt
        })

        try:
            response = await litellm.acompletion(
                model = self.primary_model,
                messages = messages,
            )

            logger.info(
                "LLM response",
                extra={
                    "model": response.model,
                    "prompt_tokens": response.usage.prompt_tokens
                }
            )

            return {
                "content": response.choices[0].message.content,
                "model": response.model
            }

        except Exception as primary_error:
            logger.warning(
                "Primary model failed, trying fallback...",
                     extra={
                         "primary_model": self.primary_model,
                         "error": str(primary_error),
                     }
            )

            try:
                fallback_response = await litellm.acompletion(
                    model = self.fallback_model,
                    messages = messages,
                )

                logger.info(
                    "LLM response",
                         extra={
                             "model": fallback_response.model,
                             "prompt_tokens": fallback_response.usage.prompt_tokens
                         }
                )

                return {
                    "content": fallback_response.choices[0].message.content,
                    "model": fallback_response.model
                }

            except Exception as fallback_error:
                logger.error(
                    "fallback model failed!",
                    extra= {
                        "fallback_model": self.fallback_model,
                        "error": str(fallback_error)
                    }
                )
                raise LLMError(
                    f"All LLM models failed. Primary: {self.primary_model}, "
                    f"Fallback: {self.fallback_model}. Last error: {str(fallback_error)}"
                )


