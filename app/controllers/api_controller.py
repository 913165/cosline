# app/controllers/vector_store_controller.py
from fastapi import APIRouter, Header, HTTPException, Depends
from typing import Dict, Any, Optional
from pydantic import BaseModel
from app.models import Distance
from app.services.vector_store_service import VectorStoreServiceFile
from app.services.SQLiteVectorStoreService import VectorStoreService

router = APIRouter(
    prefix="/api/v1/collections",
    tags=["vector-stores"]
)

# Request model for vector store creation
class VectorStoreCreateRequest(BaseModel):
    size: int
    distance: str
    persist: Optional[str] = None

# Service dependency
def get_vector_store_service():
    return VectorStoreService()

@router.post("/{store_name}")
async def create_vector_store(
    store_name: str,
    request_body: VectorStoreCreateRequest,
    api_key: str = Header(..., alias="api-key"),
    vector_store_service: VectorStoreService = Depends(get_vector_store_service)
):
    """
    Endpoint to create a new VectorStore.

    Args:
        store_name: The name of the vector store to be created
        request_body: The request body containing the vector store configuration
        api_key: The API key for authentication
        vector_store_service: Injected service for vector store operations

    Returns:
        dict: A message indicating success or failure

    Raises:
        HTTPException: If the distance metric is invalid or other errors occur
    """
    print("request_body : ", request_body)
    try:
        # Convert distance metric to enum
        try:
            print("request_body.distance : ", request_body.distance)
            distance_type = Distance.from_string(request_body.distance)
            print("distance_type : ", distance_type)
        except KeyError:
            raise HTTPException(
                status_code=400,
                detail="Invalid distance metric"
            )

        # Create configuration from request body
        config = {
            "name": store_name,
            "size": request_body.size,
            "distance": distance_type,
            # Add other config parameters as needed
        }

        # Handle persistence based on the persist flag

        response = (vector_store_service.add_vector_store
            (
            store_name, request_body.size, distance_type
            ))

        return {
            "message": f"{store_name} VectorStore created successfully"
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error creating vector store: {str(e)}"
        )

@router.get("/")
async def list_all_collections(
    vector_store_service: VectorStoreService = Depends(get_vector_store_service)
):
    """
    Endpoint to list all vector store collections.

    Args:
        vector_store_service: Injected service for vector store operations

    Returns:
        list: A list of all vector store collections
    """
    try:
        collections = vector_store_service.get_all_collections()
        return collections
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving collections: {str(e)}"
        )

@router.get("/{store_name}")
async def get_collection(
    store_name: str,
    vector_store_service: VectorStoreService = Depends(get_vector_store_service)
):
    """
    Endpoint to get a vector store collection by name.

    Args:
        store_name: The name of the vector store collection
        vector_store_service: Injected service for vector store operations

    Returns:
        dict: The configuration of the vector store collection

    Raises:
        HTTPException: If the collection does not exist
    """
    try:
        collection = vector_store_service.get_collection(store_name)
        if collection:
            return collection
        else:
            raise HTTPException(
                status_code=404,
                detail=f"Collection {store_name} not found"
            )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving collection: {str(e)}"
        )

@router.delete("/{store_name}")
async def delete_collection(
    store_name: str,
    vector_store_service: VectorStoreService = Depends(get_vector_store_service)
):
    """
    Endpoint to delete a vector store collection by name.

    Args:
        store_name: The name of the vector store collection
        vector_store_service: Injected service for vector store operations

    Returns:
        dict: A message indicating success or failure

    Raises:
        HTTPException: If the collection does not exist or other errors occur
    """
    try:
        vector_store_service.delete_collection(store_name)
        return {
            "message": f"Collection {store_name} deleted successfully"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting collection: {str(e)}"
        )