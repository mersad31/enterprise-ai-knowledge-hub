from app.core.logging import get_logger
from uuid import uuid4

from app.services import QdrantVectorStore

logger = get_logger(__name__)


class SemanticCache:
    def __init__(self, vector_store, embedding_service):

        self.embedding_service = embedding_service
        self.cache_store = QdrantVectorStore(
            client = vector_store.client,
            collection_name = "cache",
            vector_size=vector_store.vector_size,
        )


    async def get(self, question: str, threshold: float = 0.91, query_embedding: list = None) -> str | None:

        if query_embedding:
            embedded_question = query_embedding
        else:
            embedded_question = await self.embedding_service.embed_text(question)

        results = await self.cache_store.search(
            query_embedding=embedded_question,
            top_k=1
        )

        if not results:
            logger.debug(
                "Cache miss",
                extra={
                    "question": question
                }
            )

            return None

        top = results[0]

        if top["score"] >= threshold:
            logger.info(
                "Cache hit",
                extra={
                    "score": top["score"]
                }
            )

            return top["metadata"].get("answer")

        logger.debug(
            "Cache below threshold",
            extra={"score": top["score"], "threshold": threshold}
        )

        return None


    async def set(self, question: str, answer: str, question_embedding: list):

        await self.cache_store.add_text(
            texts=[question],
            embeddings=[question_embedding],
            metadatas=[{
                "answer": answer
            }],
        )

        logger.info(
            "Cache entry stored",
            extra={
                "question": question
            }
        )
