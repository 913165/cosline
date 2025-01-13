# app/controllers/vector_store_controller.py
from fastapi import APIRouter, Header, HTTPException, Depends
from typing import Dict, Any, Optional
from pydantic import BaseModel
from app.models import Distance
from app.services import IVectorStoreService, SQLiteVectorStoreService

router = APIRouter(
    prefix="/api/v1/collections",
    tags=["vector-stores"]
)


class VectorStoreCreateRequest(BaseModel):
    size: int
    distance: str
    persist: Optional[str] = None


def get_vector_store_service() -> IVectorStoreService:
    """
    Dependency injection for vector store service.
    Can be easily modified to return different implementations.
    """
    return SQLiteVectorStoreService()


@router.post("/{store_name}")
async def create_vector_store(
        store_name: str,
        request_body: VectorStoreCreateRequest,
        api_key: str = Header(..., alias="api-key"),
        vector_store_service: IVectorStoreService = Depends(get_vector_store_service)
):
    """
    Create a new vector store.

    Args:
        store_name: Name of the vector store
        request_body: Vector store configuration
        api_key: API key for authentication
        vector_store_service: Vector store service implementation

    Returns:
        dict: Success message
    """
    try:
        try:
            distance_type = Distance.from_string(request_body.distance)
        except KeyError:
            raise HTTPException(
                status_code=400,
                detail="Invalid distance metric"
            )

        success = vector_store_service.add_vector_store(
            store_name,
            request_body.size,
            distance_type
        )

        if not success:
            raise HTTPException(
                status_code=500,
                detail="Failed to create vector store"
            )

        return {
            "message": f"{store_name} VectorStore created successfully"
        }

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error creating vector store: {str(e)}"
        )


@router.get("/")
async def list_all_collections(
        vector_store_service: IVectorStoreService = Depends(get_vector_store_service)
):
    """
    List all vector store collections.

    Args:
        vector_store_service: Vector store service implementation

    Returns:
        list: All vector store collections
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
        vector_store_service: IVectorStoreService = Depends(get_vector_store_service)
):
    """
    Get a vector store collection by name.

    Args:
        store_name: Name of the vector store collection
        vector_store_service: Vector store service implementation

    Returns:
        dict: Vector store configuration
    """
    try:
        collection = vector_store_service.get_collection(store_name)
        if collection:
            return collection

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
        vector_store_service: IVectorStoreService = Depends(get_vector_store_service)
):
    """
    Delete a vector store collection.

    Args:
        store_name: Name of the vector store collection
        vector_store_service: Vector store service implementation

    Returns:
        dict: Success message
    """
    try:
        success = vector_store_service.delete_collection(store_name)
        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Collection {store_name} not found"
            )

        return {
            "message": f"Collection {store_name} deleted successfully"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting collection: {str(e)}"
        )