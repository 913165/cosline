# app/services/vector_store_service.py
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from app.models import Distance, VectorStore
import sqlite3


class IVectorStoreService(ABC):
    """Interface for vector store service implementations."""

    @abstractmethod
    def add_vector_store(self, name: str, size: int, distance: Distance) -> bool:
        """
        Create and add a new vector store to collections.

        Args:
            name: Name of the vector store
            size: Size of vectors
            distance: Distance metric type

        Returns:
            bool: True if successful

        Raises:
            ValueError: If name exists or parameters invalid
        """
        pass

    @abstractmethod
    def get_all_collections(self) -> List[Dict[str, Any]]:
        """
        Get all collections from storage.

        Returns:
            List of collection configurations
        """
        pass

    @abstractmethod
    def get_collection(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get a collection by name.

        Args:
            name: Name of collection

        Returns:
            Collection configuration or None if not found
        """
        pass

    @abstractmethod
    def delete_collection(self, store_name: str, conn: Optional[Any] = None) -> bool:
        """
        Delete a collection and its associated data.

        Args:
            store_name: Name of collection to delete
            conn: Optional connection for transaction coordination

        Returns:
            True if successful
        """
        pass

    @abstractmethod
    def update_collection(
            self,
            name: str,
            size: Optional[int] = None,
            distance: Optional[Distance] = None
    ) -> bool:
        """
        Update an existing collection's configuration.

        Args:
            name: Collection name
            size: Optional new size
            distance: Optional new distance metric

        Returns:
            True if successful
        """
        pass