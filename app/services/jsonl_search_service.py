# app/services/search_service.py
from app.models import Point, Distance

from typing import List, Dict, Any, Optional
import numpy as np
import json
import logging
from pathlib import Path
import os

ROOT_DIR = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))).parent

COLLECTIONS_DIR = ROOT_DIR / "collections"
CONFIG_DIR = ROOT_DIR / "config"
logger = logging.getLogger(__name__)


class SearchResult:
    def __init__(self, point: Point, score: float):
        self.point = point
        self.score = score


class SearchService:
    def __init__(self):
        self.collections_dir = ROOT_DIR / "collections"

    async def compute_similarity(
            self,
            query_vector: List[float],
            point_vector: List[float],
            distance_type: Distance = Distance.Cosine
    ) -> float:
        """
        Compute similarity between two vectors based on distance type.
        """
        query = np.array(query_vector)
        vector = np.array(point_vector)

        if distance_type == Distance.Cosine:
            return np.dot(query, vector) / (np.linalg.norm(query) * np.linalg.norm(vector))
        elif distance_type == Distance.Euclidean:
            return -np.linalg.norm(query - vector)  # Negative because smaller distance = more similar
        elif distance_type == Distance.Dot:
            return np.dot(query, vector)
        elif distance_type == Distance.Manhattan:
            return -np.sum(np.abs(query - vector))  # Negative because smaller distance = more similar
        else:
            raise ValueError(f"Unsupported distance type: {distance_type}")

    async def load_points(self, vector_name: str) -> List[Point]:
        """Load points from vector store."""
        vector_path = self.collections_dir / vector_name / "vectors.jsonl"

        if not vector_path.exists():
            raise FileNotFoundError(f"Vector store not found: {vector_name}")

        points = []
        with open(vector_path, 'r', encoding='utf-8') as f:
            for line in f:
                point_dict = json.loads(line.strip())
                point = Point(
                    id=point_dict['id'],
                    content=point_dict['content'],
                    vector=point_dict['vector'],
                    metadata=point_dict.get('metadata')
                )
                points.append(point)

        return points

    async def search_vectors(
            self,
            vector_name: str,
            query_vector: List[float],
            top_k: int = 10,
            distance_type: Distance = Distance.Cosine
    ) -> List[Dict[str, Any]]:
        """
        Search for similar vectors in a collection.
        """
        try:
            # Load points from vector store
            points = await self.load_points(vector_name)

            # Compute similarities
            results = []
            for point in points:
                similarity = await self.compute_similarity(
                    query_vector,
                    point.vector,
                    distance_type
                )
                results.append({
                    "id": str(point.id),
                    "content": point.content,
                    "metadata": point.metadata,
                    "score": float(similarity)
                })

            # Sort by similarity score
            results.sort(key=lambda x: x["score"], reverse=True)

            # Return top k results
            return results[:top_k]

        except Exception as e:
            logger.error(f"Search error: {str(e)}")
            raise

    async def search_by_id(
            self,
            vector_name: str,
            point_id: str,
            top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search for similar vectors using an existing point's ID.
        """
        try:
            # Load points
            points = await self.load_points(vector_name)

            # Find query point
            query_point = next(
                (p for p in points if str(p.id) == point_id),
                None
            )

            if not query_point:
                raise ValueError(f"Point not found with ID: {point_id}")

            # Use the found point's vector to search
            return await self.search_vectors(
                vector_name,
                query_point.vector,
                top_k
            )

        except Exception as e:
            logger.error(f"Search by ID error: {str(e)}")
            raise