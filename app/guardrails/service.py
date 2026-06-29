from __future__ import annotations
import re

from app.core.logging import get_logger



logger = get_logger(__name__)

class GuardrailsService:

    MAX_INPUT_CHARS = 4000

    def __init__(self, llm_service, enabled: bool = True, rails_app = None):
        self.llm_service = llm_service
        self.enabled = enabled
        self.rails_app = rails_app

        # Simple prompt-injection / jailbreak indicators
        self._injection_patterns = [
            re.compile(r"ignore\s+previous\s+instructions", re.IGNORECASE),
            re.compile(r"disregard\s+all\s+prior\s+instructions", re.IGNORECASE),
            re.compile(r"reveal\s+(your|the)\s+system\s+prompt", re.IGNORECASE),
            re.compile(r"show\s+(your|the)\s+hidden\s+instructions", re.IGNORECASE),
            re.compile(r"act\s+as\s+an?\s+unrestricted", re.IGNORECASE),
            re.compile(r"bypass\s+safety", re.IGNORECASE),
            re.compile(r"developer\s+message", re.IGNORECASE),
            re.compile(r"system\s+prompt", re.IGNORECASE),
        ]

        # Basic sensitive-information patterns
        self._sensitive_patterns = [
            re.compile(r"\b\d{16}\b"),  # possible card-like number
            re.compile(
                r"\b(password|passwd|رمز\s*عبور|کلمه\s*عبور)\b",
                re.IGNORECASE,
            ),
            re.compile(
                r"\b(api[\s\-_]?key|secret[\s\-_]?key|token)\b",
                re.IGNORECASE,
            ),
        ]

        # Output filtering patterns
        self._unsafe_output_patterns = [
            re.compile(
                r"\b(api[\s\-_]?key|secret[\s\-_]?key|access[\s\-_]?token)\b",
                re.IGNORECASE,
            ),
            re.compile(r"sk-[A-Za-z0-9]{10,}", re.IGNORECASE),
        ]

    async def check_input(self, prompt: str) -> str | None:

        if not self.enabled:
            return None

        if prompt is None:
            logger.warning("Guardrails blocked null input")
            return "متن ورودی نامعتبر است."

        cleaned = prompt.strip()

        if not cleaned:
            logger.info("Guardrails blocked empty input")
            return "لطفاً سوال یا درخواست خود را وارد کنید."

        if len(cleaned) > self.MAX_INPUT_CHARS:
            logger.info(
                "Guardrails blocked overlong input",
                extra={"length": len(cleaned)},
            )
            return "متن ورودی خیلی طولانی است. لطفاً خلاصه‌تر بنویس."

        for pattern in self._injection_patterns:
            if pattern.search(cleaned):
                logger.warning(
                    "Guardrails blocked suspected prompt injection",
                    extra={"pattern": pattern.pattern},
                )
                return (
                    "این درخواست قابل پردازش نیست. "
                    "لطفاً سوال خود را به‌صورت مستقیم و عادی مطرح کن."
                )

        for pattern in self._sensitive_patterns:
            if pattern.search(cleaned):
                logger.warning(
                    "Guardrails blocked suspected sensitive input",
                    extra={"pattern": pattern.pattern},
                )
                return (
                    "لطفاً اطلاعات حساس مانند رمز عبور، توکن، "
                    "یا داده‌های محرمانه را ارسال نکن."
                )

        if self.rails_app:
            is_safe = await self.rails_app.actions.async_call(
                "self_check_input", user_message=prompt
            )
            if not is_safe:
                return "این درخواست قابل پردازش نیست."

        return None


    async def check_output(self, response: str) -> str | None:

        if not self.enabled:
            return None

        if response is None:
            logger.warning("Guardrails filtered null output")
            return "متأسفم، در تولید پاسخ مشکلی پیش آمد."

        cleaned = response.strip()

        if not cleaned:
            logger.info("Guardrails filtered empty output")
            return "متأسفم، پاسخی برای این درخواست تولید نشد."

        for pattern in self._unsafe_output_patterns:
            if pattern.search(cleaned):
                logger.error(
                    "Guardrails filtered unsafe output",
                    extra={"pattern": pattern.pattern},
                )
                return (
                    "متأسفم، امکان نمایش این بخش از پاسخ وجود ندارد."
                )
        if self.rails_app:
            is_safe = await self.rails_app.actions.async_call(
                "self_check_output", bot_response=response
            )
            if not is_safe:
                return "متأسفم، امکان نمایش این پاسخ وجود ندارد."

        return None


    async def check_topic(self, context: str) -> str | None:

        if not self.enabled:
            return None

        if context is None:
            logger.info("Guardrails blocked out-of-scope request: null context")
            return (
                "سوال شما خارج از محدوده اطلاعات موجود است. "
                "لطفاً سوالی مرتبط با محتوای بارگذاری‌شده بپرس."
            )

        cleaned = context.strip()

        if not cleaned:
            logger.info("Guardrails blocked out-of-scope request: empty context")
            return (
                "برای این سوال اطلاعات مرتبطی پیدا نشد. "
                "لطفاً سوالی مرتبط با محتوای بارگذاری‌شده بپرس."
            )

        if len(cleaned) < 50:
            logger.info(
                "Guardrails blocked out-of-scope request: context too short",
                extra={"context_length": len(cleaned)},
            )
            return (
                "اطلاعات بازیابی‌شده برای پاسخ کافی نیست. "
                "احتمالاً سوال خارج از دامنه است یا ارتباط کمی با اسناد دارد."
            )

        return None