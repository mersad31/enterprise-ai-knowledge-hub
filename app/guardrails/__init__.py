from fastapi import Depends
from functools import lru_cache

from app.guardrails.service import GuardrailsService

from app.services.llm_service import LLMService
from app.services import get_llm_service

from app.core.logging import get_logger

_HAS_NEMO = False
try:
    from nemoguardrails import RailsApp
    _HAS_NEMO = True
except ImportError:
    pass






logger = get_logger(__name__)


@lru_cache
def get_guardrails_service(
        llm_service: LLMService = Depends(get_llm_service)
) -> GuardrailsService:

    if _HAS_NEMO:
        logger.info(
            "guardrails_service_initialized",
            extra={"enabled": _HAS_NEMO},
        )
        rails = RailsApp.from_path("app/guardrails/config")

        return GuardrailsService(
            llm_service=llm_service,
            enabled=True,
            rails_app=rails,
        )
    else:
        return GuardrailsService(
            llm_service=llm_service,
            enabled=False,
        )

