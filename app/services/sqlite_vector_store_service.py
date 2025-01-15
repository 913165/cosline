# app/services/sqlite_vector_store_service.py
import sqlite3
import json
import logging
from typing import Dict, List, Optional, Any
from app.models import Distance, VectorStore
from .vector_store_service import IVectorStoreService
from app.services.sqlite_payload_service import SQLitePayloadService

logger = logging.getLogger(__name__)


class SQLiteVectorStoreService(IVectorStoreService):
    """SQLite implementation of the vector store service."""

    def __init__(self, db_path: str = "vector_stores.db"):
        """Initialize the SQLite-based vector store service."""
        self.db_path = db_path
        self.collections: Dict[str, VectorStore] = {}
        self._initialize_db()

    def _initialize_db(self):
        """Initialize SQLite database with required tables."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS collections (
                        name TEXT PRIMARY KEY,
                        size INTEGER NOT NULL,
                        distance TEXT NOT NULL,
                        config JSON NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                conn.commit()
                logger.info("Database initialized successfully")
        except sqlite3.Error as e:
            logger.error(f"Error initializing database: {e}")
            raise

    def add_vector_store(self, name: str, size: int, distance: Distance) -> bool:
        try:
            if size <= 0:
                raise ValueError("Size must be positive")
            if not name or not name.strip():
                raise ValueError("Name cannot be empty")

            vector_store = VectorStore(
                size=size,
                distance_type=distance,
                points=[]  # Initialize with empty list
            )

            config_data = {
                "collectionName": name,
                "size": size,
                "distance": distance.name,
                "persist": True
            }

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO collections (name, size, distance, config)
                    VALUES (?, ?, ?, ?)
                """, (name, size, distance.name, json.dumps(config_data)))
                conn.commit()

            self.collections[name] = vector_store
            logger.info(f"Vector store {name} added successfully")
            return True

        except sqlite3.IntegrityError:
            logger.error(f"Collection {name} already exists")
            raise ValueError(f"Collection {name} already exists")
        except Exception as e:
            logger.error(f"Error adding vector store: {e}")
            raise

    def get_all_collections(self) -> List[Dict[str, Any]]:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT config FROM collections")
                rows = cursor.fetchall()
                return [json.loads(row[0]) for row in rows]
        except sqlite3.Error as e:
            logger.error(f"Error retrieving collections: {e}")
            return []

    def get_collection(self, name: str) -> Optional[Dict[str, Any]]:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT config FROM collections WHERE name = ?", (name,))
                row = cursor.fetchone()
                return json.loads(row[0]) if row else None
        except sqlite3.Error as e:
            logger.error(f"Error retrieving collection {name}: {e}")
            return None

    def delete_collection(self, store_name: str, conn: Optional[sqlite3.Connection] = None) -> bool:
        try:
            payload_service = SQLitePayloadService()
            should_close = conn is None

            if conn is None:
                conn = sqlite3.connect(self.db_path)

            cursor = conn.cursor()
            try:
                cursor.execute("BEGIN TRANSACTION")
                cursor.execute("DELETE FROM collections WHERE name = ?", (store_name,))
                deleted = cursor.rowcount > 0

                if deleted:
                    try:
                        payload_service.delete_vector_store(store_name, conn)
                    except Exception as e:
                        cursor.execute("ROLLBACK")
                        logger.error(f"Failed to delete payloads for collection {store_name}: {e}")
                        return False

                    if store_name in self.collections:
                        del self.collections[store_name]

                    cursor.execute("COMMIT")
                    logger.info(f"Collection {store_name} and its payloads deleted successfully")
                    return True
                else:
                    cursor.execute("ROLLBACK")
                    logger.info(f"Collection {store_name} not found in database")
                    return False

            finally:
                if should_close:
                    conn.close()

        except sqlite3.Error as e:
            logger.error(f"Database error deleting collection {store_name}: {e}")
            return False

    def update_collection(
            self,
            name: str,
            size: Optional[int] = None,
            distance: Optional[Distance] = None
    ) -> bool:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute("SELECT config FROM collections WHERE name = ?", (name,))
                row = cursor.fetchone()
                if not row:
                    return False

                config = json.loads(row[0])

                if size is not None:
                    config["size"] = size
                if distance is not None:
                    config["distance"] = distance.name

                cursor.execute("""
                    UPDATE collections 
                    SET size = ?, distance = ?, config = ?
                    WHERE name = ?
                """, (
                    config["size"],
                    config["distance"],
                    json.dumps(config),
                    name
                ))

                conn.commit()
                logger.info(f"Collection {name} updated successfully")
                return True

        except sqlite3.Error as e:
            logger.error(f"Error updating collection {name}: {e}")
            return False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.collections.clear()