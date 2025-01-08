import json
from app.models import Distance, VectorStore
from typing import Dict, Any
from pathlib import Path
import os
import shutil

# Define root directories
ROOT_DIR = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))).parent

COLLECTIONS_DIR = ROOT_DIR / "collections"
CONFIG_DIR = ROOT_DIR / "config"

class VectorStoreServiceFile:
    def __init__(self):
        self.collections: Dict[str, VectorStore] = {}

    def add_vector_store(self, name: str, size: int, distance: Distance):
        """Create and add a new vector store to collections."""
        print(f"Adding vector store {name} with size {size} and distance {distance}")
        vector_store = VectorStore(
            size=size,
            distance_type=distance
        )

        (COLLECTIONS_DIR / name).mkdir(parents=True, exist_ok=True)
        print(f"Collections directory ensured at: {COLLECTIONS_DIR / name}")

        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        (CONFIG_DIR / name).mkdir(parents=True, exist_ok=True)
        print(f"Config directory ensured at: {CONFIG_DIR / name}")

        # Create config data
        config_data = {
            "collectionName": name,
            "size": size,
            "distance": distance.name,
            "persist": True  # Assuming persist is always true for this example
        }

        # Write config data to JSON file
        config_file_path = CONFIG_DIR / name / "config.json"
        with open(config_file_path, "w") as config_file:
            json.dump(config_data, config_file, indent=4)
        print(f"Config file created at: {config_file_path}")

        self.collections[name] = vector_store

    def get_all_collections(self):
        """Get all collections inside the config directory."""
        collections = []
        for collection_dir in CONFIG_DIR.iterdir():
            if collection_dir.is_dir():
                config_file_path = collection_dir / "config.json"
                if config_file_path.exists():
                    with open(config_file_path, "r") as config_file:
                        config_data = json.load(config_file)
                        collections.append(config_data)
        return collections

    def get_collection(self, name: str):
        """Get a collection by name."""
        collection_dir = CONFIG_DIR / name
        config_file_path = collection_dir / "config.json"
        if config_file_path.exists():
            with open(config_file_path, "r") as config_file:
                config_data = json.load(config_file)
                return config_data
        return None

    def delete_collection(self, store_name: str):
        """Delete a collection by name."""
        collection_dir = COLLECTIONS_DIR / store_name
        if collection_dir.exists():
            shutil.rmtree(collection_dir)
            print(f"Collection directory {collection_dir} deleted.")
        config_dir = CONFIG_DIR / store_name
        if config_dir.exists():
            shutil.rmtree(config_dir)
            print(f"Config directory {config_dir} deleted.")
            return True

        print(f"Collection {store_name} not found.")
        return False

