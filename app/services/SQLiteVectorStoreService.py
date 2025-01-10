import sqlite3
from typing import Dict, List, Optional, Any
from app.models import Distance, VectorStore
import json
import logging
from app.services.payload_service_db import PayloadService

logger = logging.getLogger(__name__)


class VectorStoreService:
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

                # Create collections table
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

    def add_vector_store(self, name: str, size: int, distance: Distance):
        """Create and add a new vector store to collections."""
        try:
            if size <= 0:
                raise ValueError("Size must be positive")
            if not name or not name.strip():
                raise ValueError("Name cannot be empty")

            # Create vector store instance
            vector_store = VectorStore(
                size=size,
                distance_type=distance
            )

            # Prepare config data
            config_data = {
                "collectionName": name,
                "size": size,
                "distance": distance.name,
                "persist": True
            }

            # Store in SQLite
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
        """Get all collections from the database."""
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
        """Get a collection by name."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT config FROM collections WHERE name = ?", (name,))
                row = cursor.fetchone()
                return json.loads(row[0]) if row else None
        except sqlite3.Error as e:
            logger.error(f"Error retrieving collection {name}: {e}")
            return None

    def delete_collection(self, store_name: str, conn=None) -> bool:
        """Delete a collection and its associated files."""
        try:
            from app.services.payload_service_db import PayloadService
            payload_service = PayloadService()

            # Use provided connection or create new one
            should_close = conn is None
            if conn is None:
                conn = sqlite3.connect(self.db_path)

            cursor = conn.cursor()
            try:
                # Start a transaction
                cursor.execute("BEGIN TRANSACTION")

                # Delete from database
                cursor.execute("DELETE FROM collections WHERE name = ?", (store_name,))
                deleted = cursor.rowcount > 0

                if deleted:
                    # Delete payloads for this collection using PayloadService
                    try:
                        # Pass the same connection to payload service
                        payload_service.delete_vector_store(store_name, conn)
                    except Exception as e:
                        cursor.execute("ROLLBACK")
                        logger.error(f"Failed to delete payloads for collection {store_name}: {e}")
                        return False

                    # Clean up in-memory collection
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

    def update_collection(self, name: str, size: Optional[int] = None,
                          distance: Optional[Distance] = None) -> bool:
        """Update an existing collection's configuration."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Get current config
                cursor.execute("SELECT config FROM collections WHERE name = ?", (name,))
                row = cursor.fetchone()
                if not row:
                    return False

                config = json.loads(row[0])

                # Update config with new values
                if size is not None:
                    config["size"] = size
                if distance is not None:
                    config["distance"] = distance.name

                # Update database
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
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.collections.clear()