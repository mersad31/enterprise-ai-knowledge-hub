"""
Custom exceptions for the application.
Provides specific error types for different service failures.
"""

class AppBaseException(Exception):
    """Base exception for all application errors"""
    pass

class VectorStoreError(AppBaseException):
    """Raised when vector store operations fail"""
    pass


class LLMError(AppBaseException):
    """Raised when LLM service operations fail"""
    pass


class EmbeddingError(AppBaseException):
    """Raised when embedding generation fails"""
    pass


class DocumentProcessingError(AppBaseException):
    """Raised when document processing fails"""
    pass