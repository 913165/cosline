# app/services/payload_service.py
from app.models import Payload, Point

import json
import logging
from pathlib import Path
import os
from typing import Optional, List

logger = logging.getLogger(__name__)


ROOT_DIR = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))).parent

COLLECTIONS_DIR = ROOT_DIR / "collections"
CONFIG_DIR = ROOT_DIR / "config"
class PayloadServiceFile:
    def __init__(self):
        self.collections_dir = COLLECTIONS_DIR

    def ensure_collection_exists(self, vector_name: str) -> None:
        """Ensure the collection directory exists."""
        collection_path = self.collections_dir / vector_name
        try:
            # Create collection directory if it doesn't exist
            collection_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Ensured collection directory exists: {collection_path}")
        except Exception as e:
            logger.error(f"Failed to create collection directory: {str(e)}")
            raise RuntimeError(f"Failed to create collection directory: {str(e)}")

    def add_payload_to_vector_store(self, vector_name: str, payload: Payload) -> None:
        """
        Add payload to vector store as JSONL file.

        Args:
            vector_name: Name of the vector store
            point: Point object to be added

        Raises:
            RuntimeError: If failed to add payload
        """
        print("Adding payload to VectorStore: {vector_name}")


        try:
            # Ensure collection exists
            self.ensure_collection_exists(vector_name)

            # Define vector file path
            vector_path = self.collections_dir / vector_name / "vectors.jsonl"

            # Convert Point to dict for JSON serialization
            point_dict = {
                "id": str(payload.id),  # Convert UUID to string
                "content": payload.content,
                "vector": payload.embedding,
                "metadata": payload.metadata
            }

            # Append the point as a single line JSON
            # Use 'a' mode for append, create if doesn't exist
            with open(vector_path, 'a', encoding='utf-8') as f:
                json_line = json.dumps(point_dict) + "\n"
                f.write(json_line)
                print("Payload added successfully to VectorStore: {vector_name}")
        except Exception as e:
            error_msg = f"Failed to add payload: {str(e)}"
            print("error occurred ",error_msg)
            raise RuntimeError(f"Failed to add payload to VectorStore: {str(e)}")

    def add_payloads_to_vector_store(self, vector_name: str, payloads: List[Payload]) -> None:
        """
        Add multiple payloads to vector store as JSONL file.

        Args:
            vector_name: Name of the vector store
            payloads: List of Payload objects to be added

        Raises:
            RuntimeError: If failed to add payloads
        """
        print(f"Adding {len(payloads)} payloads to VectorStore: {vector_name}")

        try:
            # Ensure collection exists
            self.ensure_collection_exists(vector_name)

            # Define vector file path
            vector_path = self.collections_dir / vector_name / "vectors.jsonl"

            # Open file once for all payloads
            with open(vector_path, 'a', encoding='utf-8') as f:
                for payload in payloads:
                    # Convert Payload to dict for JSON serialization
                    point_dict = {
                        "id": str(payload.id),  # Convert UUID to string
                        "content": payload.content,
                        "vector": payload.embedding,
                        "metadata": payload.metadata
                    }

                    # Write each payload as a JSON line
                    json_line = json.dumps(point_dict) + "\n"
                    f.write(json_line)

            print(f"Successfully added {len(payloads)} payloads to VectorStore: {vector_name}")

        except Exception as e:
            error_msg = f"Failed to add payloads: {str(e)}"
            print(f"Error occurred: {error_msg}")
            raise RuntimeError(f"Failed to add payloads to VectorStore: {str(e)}")

        return None

    def read_vector_store(self, vector_name: str) -> list[Point]:
        """
        Read all points from a vector store.

        Args:
            vector_name: Name of the vector store

        Returns:
            List of Point objects

        Raises:
            RuntimeError: If failed to read vector store
        """
        vector_path = self.collections_dir / vector_name / "vectors.jsonl"

        try:
            if not vector_path.exists():
                return []

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

        except Exception as e:
            error_msg = f"Failed to read vector store: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)