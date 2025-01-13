# payload_service.py
from abc import ABC, abstractmethod
from typing import List, Optional
from app.models import Payload, Point


class IPayloadService(ABC):
    """Interface defining contract for payload service implementations."""

    @abstractmethod
    def add_payload_to_vector_store(self, vector_name: str, payload: Payload) -> None:
        """Add a single payload to the vector store."""
        pass

    @abstractmethod
    def add_payloads_to_vector_store(self, vector_name: str, payloads: List[Payload]) -> None:
        """Add multiple payloads to the vector store."""
        pass

    @abstractmethod
    def read_vector_store(self, vector_name: str) -> List[Point]:
        """Read all points from a vector store."""
        pass

    @abstractmethod
    def delete_vector_store(self, vector_name: str, conn: Optional = None) -> bool:
        """Delete all vectors for a given vector store."""
        pass

    @abstractmethod
    def get_vector_count(self, vector_name: str) -> int:
        """Get the number of vectors in a store."""
        pass