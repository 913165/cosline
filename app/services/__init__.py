# app/services/__init__.py

# Interfaces
from .payload_service import IPayloadService
from .search_service import ISearchService, SearchResult
from .vector_store_service import IVectorStoreService

# JSONL Implementations
from .jsonl_payload_service import JSONLPayloadService
from .jsonl_vector_store_service import JSONLVectorStoreService

# SQLite Implementations
from .sqlite_payload_service import SQLitePayloadService
from .sqlite_search_service import SQLiteSearchService
from .sqlite_vector_store_service import SQLiteVectorStoreService

# Backwards compatibility aliases
VectorStoreServiceFile = JSONLVectorStoreService
VectorStoreService = SQLiteVectorStoreService
PayloadServiceFile = JSONLPayloadService
PayloadService = SQLitePayloadService
SearchService = SQLiteSearchService

__all__ = [
    # Interfaces
    'IPayloadService',
    'ISearchService',
    'IVectorStoreService',
    'SearchResult',

    # JSONL implementations
    'JSONLPayloadService',
    'JSONLVectorStoreService',

    # SQLite implementations
    'SQLitePayloadService',
    'SQLiteSearchService',
    'SQLiteVectorStoreService',

    # Legacy names for backwards compatibility
    'VectorStoreServiceFile',
    'VectorStoreService',
    'PayloadServiceFile',
    'PayloadService',
    'SearchService'
]