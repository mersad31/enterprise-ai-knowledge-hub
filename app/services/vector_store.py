"""Vector store service for Qdrant operations."""
import asyncio

from typing import List, Dict, Any
from uuid import uuid4

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
)
from qdrant_client.http import models as qdrant_models

from app.core.logging import get_logger
from app.core.exceptions import VectorStoreError


logger = get_logger(__name__)

class QdrantVectorStore:
    """
    Async wrapper for Qdrant vector database operations.

    Handles:
    - Collection creation/management
    - Document chunking and indexing
    - Semantic search with metadata filtering
    """
    def __init__(
            self,
            client: QdrantClient,
            collection_name: str,
            vector_size: int = 768,
    ):
        """
            Initialize Qdrant vector store.

            Args:
                client: Qdrant client instance
                collection_name: Name of collection to use
                vector_size: Dimension of embedding vectors
        """
        self.client = client
        self.collection_name = collection_name
        self.vector_size = vector_size
        logger.info(
            "QdrantVectorStore initialized",
            extra={
                "collection": collection_name,
                "vector_size": vector_size,
            },
        )

    async def ensure_collection(self) -> None:
        """
            Ensure collection exists, create if not.

            Raises:
                VectorStoreError: If collection creation fails
        """
        try:
            collections = await asyncio.to_thread(
                self.client.get_collections
            )

            exists = any(
                col.name == self.collection_name
                for col in collections.collections
            )

            if not exists:
                logger.info(
                    "Creating collection",
                    extra={"collection": self.collection_name},
                )
                await asyncio.to_thread(
                    self.client.create_collection,
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.vector_size,
                        distance=Distance.COSINE,
                    ),
                )
                logger.info("Collection created successfully")
            else:
                logger.debug(
                    "Collection already exists",
                    extra={"collection": self.collection_name},
                )

        except Exception as e:
            logger.error(
                "Failed to ensure collection",
                extra={"error": str(e)},
            )
            raise VectorStoreError(
                f"Collection setup failed: {str(e)}"
            ) from e


    async def add_text(
            self,
            texts: List[str],
            embeddings: List[List[float]],
            metadatas: List[Dict[str, Any]],
    ) -> List[str]:
        """
            Add text chunks with embeddings to vector store.

            Args:
                texts: List of text chunks
                embeddings: Corresponding embedding vectors
                metadatas: Metadata for each chunk (must include document_id)

            Returns:
                List of generated chunk IDs

            Raises:
                VectorStoreError: If indexing fails
        """
        if not (len(texts) == len(embeddings) == len(metadatas)):
            raise VectorStoreError(
                "texts, embeddings, and metadatas must have same length"
            )

        try:
            # Generate unique IDs for chunks
            chunk_ids = [str(uuid4()) for _ in texts]

            # create points for Qdrant
            points = [
                PointStruct(
                    id=chunk_id,
                    vector=embedding,
                    payload={
                        "text": text,
                        **metadata,  # includes document_id, filename, etc.
                    },
                )
                for chunk_id, embedding, metadata, text in zip(
                    chunk_ids, embeddings, metadatas, texts
                )
            ]

            # Upsert to Qdrant
            await asyncio.to_thread(
                self.client.upsert,
                collection_name=self.collection_name,
                points=points,
            )

            logger.info(
                "Chunks indexed successfully",
                extra={
                    "chunk_count": len(chunk_ids),
                    "document_id": metadatas[0].get("document_id"),
                },
            )

            return chunk_ids

        except Exception as e:
            logger.error(
                "Failed to index chunks",
                extra={"error": str(e), "chunk_count": len(texts)},
            )
            raise VectorStoreError(
                f"Indexing failed: {str(e)}"
            ) from e


    async def search(
            self,
            query_embedding: List[float],
            top_k: int = 5,
            document_id: str | None = None,
    ) -> List[Dict[str, Any]]:
        """
            Search for similar chunks using vector similarity.

            Args:
                query_embedding: Query vector
                top_k: Number of results to return
                document_id: Optional filter by document_id

            Returns:
                List of dicts with keys: text, document_id, score, metadata

            Raises:
                VectorStoreError: If search fails
        """
        try:
            # Build filter if document_id provided
            query_filter = None
            if document_id:
                query_filter = qdrant_models.Filter(
                    must = [
                        qdrant_models.FieldCondition(
                            key="document_id",
                            match=qdrant_models.MatchValue(value=document_id),
                        )
                    ]
                )
            # Execute search
            results = await asyncio.to_thread(
                self.client.query_points,
                collection_name=self.collection_name,
                query=query_embedding,
                limit=top_k,
                query_filter=query_filter,
            )

            # Format results
            formatted = [
                {
                    "text": hit.payload.get("text", ""),
                    "document_id": hit.payload.get("document_id"),
                    "score": hit.score,
                    "metadata": {
                        k: v
                        for k, v in hit.payload.items()
                        if k not in ("text", "document_id")
                    },
                }
                for hit in results.points
            ]

            logger.info(
                "Search completed",
                extra={
                    "results_count": len(formatted),
                    "top_score": formatted[0]["score"] if formatted else None,
                },
            )
            return formatted

        except Exception as e:
            logger.error(
                "Search failed",
                extra={"error": str(e)},
            )
            raise VectorStoreError(
                f"Search failed: {str(e)}"
            ) from e


    async def delete_document(
            self,
            document_id: str
    ) -> int:

        """
            Delete all chunks belonging to a document.

            Args:
                document_id: ID of document to delete

            Returns:
                Number of chunks deleted

            Raises:
                VectorStoreError: If deletion fails
        """
        try:
            count_filter = qdrant_models.Filter(
                must=[
                    qdrant_models.FieldCondition(
                        key="document_id",
                        match=qdrant_models.MatchValue(
                            value=document_id,
                        )
                    )
                ]
            )

            count_result = await asyncio.to_thread(
                self.client.count,
                collection_name=self.collection_name,
                count_filter=count_filter,
                exact=True,
            )
            deleted_count = count_result.count

            # Delete by filter
            result = await asyncio.to_thread(
                self.client.delete,
                collection_name=self.collection_name,
                points_selector=qdrant_models.FilterSelector(
                    filter=qdrant_models.Filter(
                        must=[
                            qdrant_models.FieldCondition(
                                key="document_id",
                                match=qdrant_models.MatchValue(
                                    value=document_id
                                ),
                            )
                        ]
                    )
                ),
            )

            logger.info(
                "Document deleted",
                extra={
                    "document_id": document_id,
                    "status": result.status,
                },
            )

            return deleted_count

        except Exception as e:
            logger.error(
                "Failed to delete document",
                extra={
                    "error": str(e),
                    "document_id": document_id,
                },
            )
            raise VectorStoreError(
                f"Deletion failed: {str(e)}"
            ) from e
