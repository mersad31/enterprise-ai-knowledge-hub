from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.services import get_rag_service
from app.services.rag_service import RAGService

from app.models.chat import ChatResponse, ChatRequest

from app.core.logging import get_logger

from app.guardrails import GuardrailsService, get_guardrails_service



logger = get_logger(__name__)
router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
async def ask(
        req: ChatRequest,
        rag_service: RAGService = Depends(get_rag_service),
        guardrails_service: GuardrailsService = Depends(get_guardrails_service)
):
    logger.info(
        "Chat request",
        extra={
            "query": req.query[:100],
            "top_k": req.top_k
        }
    )

    input_result = await guardrails_service.check_input(req.query)
    if input_result:
        raise HTTPException(status_code=400, detail=input_result)


    result = await rag_service.query(
        question=req.query,
        top_k=req.top_k,
        document_id=req.document_id
    )

    logger.info(
        "Chat response",
        extra={
            "model": result["model_used"],
            "sources_count": len(result["sources"])
        }
    )
    output_result = await guardrails_service.check_output(result["answer"])
    if output_result:
        result["answer"] = output_result
        result["model_used"] = "filtered"

    return ChatResponse(
        answer=result["answer"],
        sources=result["sources"],
        model_used=result["model_used"]
    )
