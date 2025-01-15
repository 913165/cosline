# app/models/vector_store.py
from pydantic import BaseModel, Field
from typing import List, Optional
from .distance import Distance
from .point import Point


class HNSWConfig(BaseModel):
    """Configuration settings for HNSW index."""
    M: int = 16
    ef_construction: int = 200
    ef_search: int = 50
    num_threads: int = 4


class VectorStore(BaseModel):
    """
    A class representing a vector store that holds points and distance calculation type.
    """
    size: int
    distance_type: Distance
    points: List[Point] = Field(default_factory=list)
    hnsw_config: Optional[HNSWConfig] = None

    def add_point(self, point: Point) -> None:
        """
        Add a Point to the store.

        Args:
            point: Point object to be added to the store
        """
        self.points.append(point)

    def __str__(self) -> str:
        """String representation of the VectorStore."""
        return (
            f"VectorStore("
            f"size={self.size}, "
            f"distance_type={self.distance_type}, "
            f"points_count={len(self.points)}, "
            f"hnsw_config={self.hnsw_config}"
            f")"
        )