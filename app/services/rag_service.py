from app.core.logging import get_logger



logger = get_logger(__name__)

class RAGService:
    def __init__(
            self,
            llm_service,
            vector_store,
            embedding_service,
            cache=None,
            guardrails_service=None
    ):
        self.llm_service = llm_service
        self.vector_store = vector_store
        self.embedding_service = embedding_service
        self.cache=cache
        self.guardrails_service = guardrails_service


    async def query(self, question: str, top_k: int = 3, document_id: str | None = None):

        query_vector = await self.embedding_service.embed_text(question)

        if self.cache:
            cached = await self.cache.get(question, query_embedding=query_vector)
            if cached:
                logger.info(
                    "cache hit",
                    extra={"question": question}
                )
                return {
                    "answer": cached,
                    "sources": [],
                    "model_used": "cache",
                }

        results = await self.vector_store.search(query_vector, top_k, document_id)

        logger.info(
            "Retrieved chunks",
            extra={
                "chunk_count": len(results)
            }
        )

        context = "\n\n".join(r["text"] for r in results)
        system_prompt = f" با توجه به داکیومنت‌های زیر پاسخ بده:{context}"

        if self.guardrails_service:
            topic_result = await self.guardrails_service.check_topic(context)

            if topic_result:
                return {
                    "answer": topic_result,
                    "sources": [],
                    "model_used": "blocked",
                }
        answer = await self.llm_service.generate(question, system_prompt)

        if self.cache:
            await self.cache.set(
                question=question,
                answer=answer["content"],
                question_embedding=query_vector,
            )

        logger.info(
            "LLM response",
            extra={
                "model": answer["model"]
            }
        )
        return {
            "answer": answer["content"],
            "sources": results,
            "model_used": answer["model"]
        }








