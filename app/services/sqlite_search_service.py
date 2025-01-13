# app/services/sqlite_search_service.py
import numpy as np
import sqlite3
import json
import logging
from pathlib import Path
import os
from typing import List, Dict, Any
from app.models import Point, Distance
from .search_service import ISearchService, SearchResult

logger = logging.getLogger(__name__)


class SQLiteSearchService(ISearchService):
    """SQLite implementation of the SearchService interface."""

    def __init__(self, db_path: str = "vector_stores.db"):
        self.db_path = db_path
        self._initialize_db()

    def _initialize_db(self):
        """Initialize SQLite database with required tables."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS vectors (
                        id TEXT PRIMARY KEY,
                        vector_store_name TEXT NOT NULL,
                        content TEXT,
                        embedding BLOB NOT NULL,
                        metadata JSON,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (vector_store_name) REFERENCES collections(name)
                    )
                """)
                conn.commit()
                logger.info("Database initialized successfully")
        except sqlite3.Error as e:
            logger.error(f"Error initializing database: {e}")
            raise

    async def compute_similarity(
            self,
            query_vector: List[float],
            point_vector: List[float],
            distance_type: Distance = Distance.Cosine
    ) -> float:
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
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, content, embedding, metadata
                    FROM vectors
                    WHERE vector_store_name = ?
                """, (vector_name,))

                points = []
                for row in cursor.fetchall():
                    vector = json.loads(row[2].decode())
                    metadata = json.loads(row[3]) if row[3] else None
                    point = Point(
                        id=row[0],
                        content=row[1],
                        vector=vector,
                        metadata=metadata
                    )
                    points.append(point)

                if not points:
                    raise FileNotFoundError(f"Vector store not found or empty: {vector_name}")

                return points

        except sqlite3.Error as e:
            logger.error(f"Database error while loading points: {e}")
            raise RuntimeError(f"Failed to load points from database: {e}")

    async def search_vectors(
            self,
            vector_name: str,
            query_vector: List[float],
            top_k: int = 10,
            distance_type: Distance = Distance.Cosine
    ) -> List[Dict[str, Any]]:
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
        try:
            # First find the specific point
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, content, embedding, metadata
                    FROM vectors
                    WHERE vector_store_name = ? AND id = ?
                """, (vector_name, point_id))

                row = cursor.fetchone()
                if not row:
                    raise ValueError(f"Point not found with ID: {point_id}")

                vector = json.loads(row[2].decode())

                # Use the found point's vector to search
                return await self.search_vectors(
                    vector_name,
                    vector,
                    top_k
                )

        except sqlite3.Error as e:
            logger.error(f"Database error in search_by_id: {e}")
            raise RuntimeError(f"Database error: {e}")
        except Exception as e:
            logger.error(f"Search by ID error: {str(e)}")
            raise