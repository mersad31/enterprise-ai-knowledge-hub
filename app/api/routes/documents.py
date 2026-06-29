from uuid import uuid4

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from pydantic import BaseModel, Field

from app.services import get_vector_store, get_embedding_service, get_document_parser
from app.services.vector_store import QdrantVectorStore
from app.services.embedding_service import OllamaEmbedding
from app.services.document_parser import DocumentParser

from app.models.document import DocumentOut, DocumentIn

from app.core.logging import get_logger



logger = get_logger(__name__)
router = APIRouter(prefix="/documents", tags=["documents"])


def chunk_text(text: str, size: int = 500, overlap: int = 50) -> list[str]:
    chunks = []
    start = 0
    while start < len(text):
        end = start + size
        chunks.append(text[start:end])
        start = end - overlap
    return chunks


@router.post("", response_model=DocumentOut)
async def add_document(
        doc: DocumentIn,
        store: QdrantVectorStore = Depends(get_vector_store),
        embedder: OllamaEmbedding = Depends(get_embedding_service),
):
    await store.ensure_collection()

    chunks = chunk_text(doc.text)
    embeddings = await embedder.embed_batch(chunks)

    document_id = str(uuid4())
    metadatas = [
        {
            "document_id": document_id,
            "filename": doc.filename,
            "chunk_index": i,
        }
        for i in range(len(chunks))
    ]

    chunk_ids = await store.add_text(chunks, embeddings, metadatas)

    logger.info(
        "Creating document",
        extra={
            "document_id": document_id,
            "chunk_count": len(chunks)
        }
    )

    return DocumentOut(
        document_id=document_id,
        chunk_count=len(chunk_ids),
        chunk_ids=chunk_ids,
    )


@router.post("/upload", response_model=DocumentOut)
async def upload_document(
        file: UploadFile = File(...),
        parser: DocumentParser = Depends(get_document_parser),
        store: QdrantVectorStore = Depends(get_vector_store),
        embedder: OllamaEmbedding = Depends(get_embedding_service),
):
    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Empty file")

    logger.info(
        "File uploaded",
        extra={
            "filename": file.filename,
            "size": len(file_bytes)
        }
    )

    try:
        text = await parser.parse(file_bytes, file.filename)
        if not text:
            raise HTTPException(status_code=400, detail="No text found in document")

        await store.ensure_collection()

        chunks = chunk_text(text)

        embeddings = await embedder.embed_batch(chunks)

        document_id = str(uuid4())
        metadatas = [
            {
                "document_id": document_id,
                "filename": file.filename,
                "chunk_index": i,
            }
            for i in range(len(chunks))
        ]

        chunk_ids = await store.add_text(chunks, embeddings, metadatas)

        logger.info(
            "Document stored",
            extra={
                "document_id": document_id,
                "chunks": len(chunks)
            }
        )

        return DocumentOut(
            document_id=document_id,
            chunk_count=len(chunk_ids),
            chunk_ids=chunk_ids,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@router.delete("/{document_id}")
async def delete_document(
        document_id: str,
        store: QdrantVectorStore = Depends(get_vector_store),
):
    await store.delete_document(document_id)

    logger.info(
        "Document deleted",
        extra={
            "document_id": document_id
        }
    )

    return {
        "document_id": document_id,
        "status": "deleted"
    }
