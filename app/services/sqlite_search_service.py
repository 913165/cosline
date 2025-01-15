# app/services/sqlite_search_service.py
import faiss
import numpy as np
import json
import sqlite3
import logging
from typing import List, Dict, Any

from app.models import Point, Distance
from app.services import ISearchService

logger = logging.getLogger(__name__)


class SQLiteSearchService(ISearchService):
    def __init__(self, db_path: str = "vector_stores.db"):
        self.db_path = db_path
        self._initialize_db()
        self.index_cache = {}

    def _initialize_db(self):
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
        query = np.array(query_vector).astype('float32')
        vector = np.array(point_vector).astype('float32')

        if distance_type == Distance.Cosine:
            # Normalize vectors for cosine similarity
            query = query / np.linalg.norm(query)
            vector = vector / np.linalg.norm(vector)
            return np.dot(query, vector)
        elif distance_type == Distance.Euclidean:
            return -np.linalg.norm(query - vector)
        elif distance_type == Distance.Dot:
            return np.dot(query, vector)
        elif distance_type == Distance.Manhattan:
            return -np.sum(np.abs(query - vector))
        else:
            raise ValueError(f"Unsupported distance type: {distance_type}")

    async def _get_vector_store_config(self, vector_name: str) -> Dict[str, Any]:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT config FROM collections WHERE name = ?", (vector_name,))
                row = cursor.fetchone()
                if row:
                    return json.loads(row[0])
                raise FileNotFoundError(f"Vector store not found: {vector_name}")
        except sqlite3.Error as e:
            logger.error(f"Database error: {e}")
            raise

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
                        embedding=vector,
                        metadata=metadata
                    )
                    points.append(point)

                if not points:
                    raise FileNotFoundError(f"Vector store not found or empty: {vector_name}")

                return points

        except sqlite3.Error as e:
            logger.error(f"Database error while loading points: {e}")
            raise RuntimeError(f"Failed to load points from database: {e}")

    async def _build_index(self, vector_name: str, points: List[Point], config: Dict):
        if not points:
            return

        # Get dimension from first vector
        dim = len(points[0].embedding)

        # Get distance type from config
        distance_type = config.get('distance', 'Cosine')

        # Select appropriate FAISS metric based on distance type
        if distance_type == 'Cosine':
            metric = faiss.METRIC_INNER_PRODUCT
        elif distance_type in ['Euclidean', 'Manhattan']:
            metric = faiss.METRIC_L2
        else:
            metric = faiss.METRIC_INNER_PRODUCT  # Default to inner product for Dot product

        # Get HNSW parameters from config
        hnsw_config = config.get('hnsw_config', {})
        M = hnsw_config.get('M', 16)
        ef_construction = hnsw_config.get('ef_construction', 200)
        ef_search = hnsw_config.get('ef_search', 50)

        # Create and configure FAISS index
        index = faiss.IndexHNSWFlat(dim, M, metric)
        index.hnsw.efConstruction = ef_construction
        index.hnsw.efSearch = ef_search

        # Prepare vectors
        vectors = np.array([point.embedding for point in points]).astype('float32')

        # Normalize vectors for cosine similarity
        if distance_type == 'Cosine':
            faiss.normalize_L2(vectors)

        # Train and add vectors
        try:
            index.train(vectors)
        except Exception as e:
            logger.warning(f"Training failed, but continuing as some FAISS indices don't require training: {e}")

        index.add(vectors)

        # Cache index and point mapping
        self.index_cache[vector_name] = {
            'index': index,
            'points': points,
            'id_mapping': {i: point for i, point in enumerate(points)},
            'distance_type': distance_type
        }

        logger.info(f"Built FAISS HNSW index for {vector_name} with {len(points)} vectors")

    async def search_vectors(
            self,
            vector_name: str,
            query_vector: List[float],
            top_k: int = 10,
            distance_type: Distance = Distance.Cosine
    ) -> List[Dict[str, Any]]:
        try:
            # Load points if not in cache
            if vector_name not in self.index_cache:
                points = await self.load_points(vector_name)
                config = await self._get_vector_store_config(vector_name)
                await self._build_index(vector_name, points, config)

            index_data = self.index_cache[vector_name]

            # Prepare query vector
            query = np.array([query_vector]).astype('float32')

            # Normalize query if using cosine similarity
            if index_data['distance_type'] == 'Cosine':
                faiss.normalize_L2(query)

            # Search
            distances, indices = index_data['index'].search(query, min(top_k, len(index_data['points'])))

            # Format results
            results = []
            for idx, dist in zip(indices[0], distances[0]):
                if idx < 0:  # FAISS may return -1 for not enough results
                    continue

                point = index_data['id_mapping'][idx]

                # Convert distance to similarity score based on distance type
                if index_data['distance_type'] == 'Cosine':
                    score = float((1 + dist) / 2)  # Convert cosine distance to similarity (0-1 range)
                else:
                    score = float(1 / (1 + dist))  # Convert euclidean/manhattan distance to similarity

                results.append({
                    "id": str(point.id),
                    "content": point.content,
                    "metadata": point.metadata,
                    "score": score
                })

            return results

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
                    SELECT embedding
                    FROM vectors
                    WHERE vector_store_name = ? AND id = ?
                """, (vector_name, point_id))

                row = cursor.fetchone()
                if not row:
                    raise ValueError(f"Point not found with ID: {point_id}")

                vector = json.loads(row[0].decode())

                # Use the found point's vector to search
                return await self.search_vectors(
                    vector_name,
                    vector,
                    top_k
                )

        except sqlite3.Error as e:
            logger.error(f"Database error in search_by_id: {e}")
            raise RuntimeError(f"Database error: {e}")