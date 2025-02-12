# sqlite_payload_service.py
import sqlite3
import json
import logging
from typing import List, Optional
from app.models import Payload, Point
from .payload_service import IPayloadService

logger = logging.getLogger(__name__)


class SQLitePayloadService(IPayloadService):
    """SQLite implementation of the PayloadService interface."""

    def __init__(self, db_path: str = "vector_stores.db"):
        self.db_path = db_path
        self._initialize_db()

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

    def add_payload_to_vector_store(self, vector_name: str, payload: Payload) -> None:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                vector_bytes = json.dumps(payload.embedding).encode()
                cursor.execute("""
                    INSERT INTO vectors (id, vector_store_name, content, embedding, metadata)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    str(payload.id),
                    vector_name,
                    payload.content,
                    vector_bytes,
                    json.dumps(payload.metadata) if payload.metadata else None
                ))
                conn.commit()
                logger.info(f"Payload {payload.id} added to vector store {vector_name}")
        except sqlite3.Error as e:
            error_msg = f"Failed to add payload to vector store: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)

    def add_payloads_to_vector_store(self, vector_name: str, payloads: List[Payload]) -> None:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                payload_data = [
                    (
                        str(payload.id),
                        vector_name,
                        payload.content,
                        json.dumps(payload.embedding).encode(),
                        json.dumps(payload.metadata) if payload.metadata else None
                    )
                    for payload in payloads
                ]
                cursor.executemany("""
                    INSERT INTO vectors (id, vector_store_name, content, embedding, metadata)
                    VALUES (?, ?, ?, ?, ?)
                """, payload_data)
                conn.commit()
                logger.info(f"Successfully added {len(payloads)} payloads to vector store {vector_name}")
        except sqlite3.Error as e:
            error_msg = f"Failed to add payloads to vector store: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)

    def read_vector_store(self, vector_name: str) -> List[Point]:
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
                return points
        except sqlite3.Error as e:
            error_msg = f"Failed to read vector store: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)

    def delete_vector_store(self, vector_name: str, conn: Optional[sqlite3.Connection] = None) -> bool:
        logger.info(f"Deleting vector store {vector_name}")
        try:
            should_close = conn is None
            if conn is None:
                conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            try:
                cursor.execute("DELETE FROM vectors WHERE vector_store_name = ?", (vector_name,))
                deleted = cursor.rowcount > 0
                if not conn.in_transaction:
                    conn.commit()
                return True
            finally:
                if should_close:
                    conn.close()
        except sqlite3.Error as e:
            logger.error(f"Error deleting vector store {vector_name} from database: {e}")
            return False

    def get_vector_count(self, vector_name: str) -> int:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM vectors 
                    WHERE vector_store_name = ?
                """, (vector_name,))
                return cursor.fetchone()[0]
        except sqlite3.Error as e:
            logger.error(f"Error counting vectors for store {vector_name}: {e}")
            return 0