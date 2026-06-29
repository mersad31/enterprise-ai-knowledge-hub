import litellm

try:
    from langfuse import Langfuse
    from langfuse.callback import CallbackHandler
    HAS_LANGFUSE = True
except ImportError:
    HAS_LANGFUSE = False

from app.core.config import get_settings


settings = get_settings()


langfuse = Langfuse(
    public_key=settings.langfuse_public_key,
    secret_key=settings.langfuse_secret_key,
    host=settings.langfuse_host,
)

if settings.langfuse_public_key:
    langfuse_handler = CallbackHandler(langfuse=langfuse)
    litellm.callback = [langfuse_handler]