import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.core.logging import get_logger
from app.core.logging import setup_logging
from app.core import tracing

from app.api.routes import documents, query, chat

from app.services import get_vector_store, get_semantic_cache, get_embedding_service



logger = get_logger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup & shutdown events"""
    setup_logging(debug=settings.debug)

    vector_store = get_vector_store()
    await vector_store.ensure_collection()

    cache = get_semantic_cache()
    await cache.cache_store.ensure_collection()

    logger.info("Starting application", extra={"env": settings.app_env})
    yield
    embed_service = get_embedding_service()
    await embed_service.client.aclose()
    logger.info("🛑 Shutting down application")


app = FastAPI(
    title="Enterprise AI Knowledge Hub",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(documents.router, prefix="/api/v1")
app.include_router(query.router, prefix="/api/v1")
app.include_router(chat.router, prefix="/api/v1")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    return {"status": "ok", "env": settings.app_env}


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.perf_counter()
    try:
        response = await call_next(request)
    finally:
        process_time = time.perf_counter() - start_time

    logger.info(
        "request_timing",
        extra={
            "path": request.url.path,
            "duration": process_time
        }
    )

    response.headers["X-Process-Time"] = str(process_time)
    return response

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "خطای داخلی سرور رخ داده است. لطفاً لاگ‌ها را بررسی کنید."},
    )