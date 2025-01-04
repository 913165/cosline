# app/models/vector_store.py
from pydantic import BaseModel
from typing import List
from .distance import Distance
from .point import Point


class VectorStore(BaseModel):
    """
    A class representing a vector store that holds points and distance calculation type.
    """
    size: int
    distance_type: Distance
    points: List[Point] = []  # Initialize with empty list by default

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
            f"points_count={len(self.points)}"
            f")"
        )