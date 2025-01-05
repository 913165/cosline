# app/controllers/search_controller.py
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from app.models import Point, Payload
from app.services.search_service import SearchService
import logging

router = APIRouter(
    prefix="/api/v1/collections",
    tags=["search"]
)

logger = logging.getLogger(__name__)


def get_search_service():
    return SearchService()


@router.post("/{vector_name}/search")
async def search_vectors(
        vector_name: str,
        query_vector: List[float],
        top_k: int = 10,
        search_service: SearchService = Depends(get_search_service)
):
    """
    Search for similar vectors in a collection.

    Args:
        vector_name: Name of the vector collection
        query_vector: Vector to search for
        top_k: Number of results to return
        search_service: Injected search service
    """
    try:
        logger.info(f"Searching in collection: {vector_name}")
        results = await search_service.search_vectors(vector_name, query_vector, top_k)
        return {"results": results}

    except Exception as e:
        logger.error(f"Search error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Search failed: {str(e)}"
        )


@router.post("/{vector_name}/search_by_id")
async def search_by_id(
        vector_name: str,
        point_id: str,
        top_k: int = 10,
        search_service: SearchService = Depends(get_search_service)
):
    """
    Search for similar vectors using an existing point's ID.
    """
    try:
        results = await search_service.search_by_id(vector_name, point_id, top_k)
        return {"results": results}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Search by ID failed: {str(e)}"
        )