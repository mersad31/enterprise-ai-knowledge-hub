from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.services import get_vector_store, get_embedding_service as get_embedding
from app.services.vector_store import QdrantVectorStore
from app.services.embedding_service import OllamaEmbedding

from app.models.query import QueryResponse, QueryRequest

from app.core.logging import get_logger

from app.guardrails import GuardrailsService, get_guardrails_service

logger = get_logger(__name__)
router = APIRouter(prefix="/query", tags=["query"])



@router.post("", response_model=QueryResponse)
async def query(
    req: QueryRequest,
    store: QdrantVectorStore = Depends(get_vector_store),
    embedder: OllamaEmbedding = Depends(get_embedding),
    guardrails_service: GuardrailsService = Depends(get_guardrails_service)
):

    logger.info(
        "Query request",
        extra={
            "query": req.query[:100],
            "top_k": req.top_k
        }
    )


    input_result = await guardrails_service.check_input(req.query)

    if input_result:
         raise HTTPException(status_code=400, detail=input_result)

    query_vec = await embedder.embed_text(req.query)

    results = await store.search(
        query_embedding=query_vec,
        top_k=req.top_k,
        document_id=req.document_id,
    )

    logger.info(
        "Query results",
        extra={
            "results_count": len(results)
        }
    )

    return QueryResponse(results=results)