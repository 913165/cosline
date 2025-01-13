# app/services/search_service.py
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from pathlib import Path
from app.models import Point, Distance


class SearchResult:
    def __init__(self, point: Point, score: float):
        self.point = point
        self.score = score


class ISearchService(ABC):
    """Interface defining contract for search service implementations."""

    @abstractmethod
    async def compute_similarity(
            self,
            query_vector: List[float],
            point_vector: List[float],
            distance_type: Distance = Distance.Cosine
    ) -> float:
        """
        Compute similarity between two vectors based on distance type.

        Args:
            query_vector: Query vector to compare
            point_vector: Point vector to compare against
            distance_type: Type of distance metric to use

        Returns:
            Similarity score between the vectors

        Raises:
            ValueError: If distance type is not supported
        """
        pass

    @abstractmethod
    async def load_points(self, vector_name: str) -> List[Point]:
        """
        Load points from vector store.

        Args:
            vector_name: Name of the vector store

        Returns:
            List of Point objects

        Raises:
            FileNotFoundError: If vector store not found
        """
        pass

    @abstractmethod
    async def search_vectors(
            self,
            vector_name: str,
            query_vector: List[float],
            top_k: int = 10,
            distance_type: Distance = Distance.Cosine
    ) -> List[Dict[str, Any]]:
        """
        Search for similar vectors in a collection.

        Args:
            vector_name: Name of the vector store
            query_vector: Vector to search for
            top_k: Number of results to return
            distance_type: Type of distance metric to use

        Returns:
            List of dictionaries containing search results with id, content, metadata, and score
        """
        pass

    @abstractmethod
    async def search_by_id(
            self,
            vector_name: str,
            point_id: str,
            top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search for similar vectors using an existing point's ID.

        Args:
            vector_name: Name of the vector store
            point_id: ID of the point to use as query
            top_k: Number of results to return

        Returns:
            List of dictionaries containing search results with id, content, metadata, and score

        Raises:
            ValueError: If point with given ID not found
        """
        pass