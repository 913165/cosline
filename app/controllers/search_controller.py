# app/controllers/search_controller.py
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Dict, Any
import logging
from uuid import UUID
from app.models import Point, Distance
from app.services import ISearchService, SQLiteSearchService
from pydantic import BaseModel

router = APIRouter(
    prefix="/api/v1/collections",
    tags=["search"]
)

logger = logging.getLogger(__name__)


class SearchQuery(BaseModel):
    query_vector: List[float]
    top_k: int = 10
    distance_type: Distance = Distance.Cosine


class SearchByIdQuery(BaseModel):
    point_id: str
    top_k: int = 10


def get_search_service() -> ISearchService:
    """
    Dependency injection for search service.
    Can be easily modified to return different implementations.
    """
    return SQLiteSearchService()


@router.post("/{vector_name}/search")
async def search_vectors(
        vector_name: str,
        search_query: SearchQuery,
        search_service: ISearchService = Depends(get_search_service)
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Search for similar vectors in a collection.

    Args:
        vector_name: Name of the vector collection
        search_query: Search parameters including query vector and options
        search_service: Search service implementation

    Returns:
        dict: Search results with similarity scores

    Raises:
        HTTPException: If collection not found or search fails
    """
    try:
        logger.info(f"Searching in collection: {vector_name} with top_k={search_query.top_k}")

        if not search_query.query_vector:
            raise ValueError("Query vector cannot be empty")

        results = await search_service.search_vectors(
            vector_name,
            search_query.query_vector,
            search_query.top_k,
            search_query.distance_type
        )
        return {"results": results}

    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except FileNotFoundError:
        logger.error(f"Collection not found: {vector_name}")
        raise HTTPException(
            status_code=404,
            detail=f"Collection {vector_name} not found"
        )
    except Exception as e:
        logger.error(f"Search error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Search failed: {str(e)}"
        )


@router.post("/{vector_name}/search_by_id")
async def search_by_id(
        vector_name: str,
        query: SearchByIdQuery,
        search_service: ISearchService = Depends(get_search_service)
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Search for similar vectors using an existing point's ID.

    Args:
        vector_name: Name of the vector collection
        query: Search parameters including point ID and top_k
        search_service: Search service implementation

    Returns:
        dict: Search results with similarity scores

    Raises:
        HTTPException: If point not found, collection not found, or search fails
    """
    try:
        logger.info(f"Searching by ID in collection: {vector_name}, point_id: {query.point_id}")

        if not query.point_id or not query.point_id.strip():
            raise ValueError("Point ID cannot be empty")

        results = await search_service.search_by_id(
            vector_name,
            query.point_id,
            query.top_k
        )
        return {"results": results}

    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except FileNotFoundError:
        logger.error(f"Collection not found: {vector_name}")
        raise HTTPException(
            status_code=404,
            detail=f"Collection {vector_name} not found"
        )
    except RuntimeError as e:
        if "Point not found" in str(e):
            logger.error(f"Point not found: {query.point_id}")
            raise HTTPException(
                status_code=404,
                detail=f"Point with ID {query.point_id} not found"
            )
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Search by ID error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Search by ID failed: {str(e)}"
        )


@router.get("/{vector_name}/similarity")
async def compute_similarity(
        vector_name: str,
        vector1: List[float] = Query(..., title="First vector"),
        vector2: List[float] = Query(..., title="Second vector"),
        distance_type: Distance = Query(Distance.Cosine, title="Distance metric"),
        search_service: ISearchService = Depends(get_search_service)
) -> Dict[str, float]:
    """
    Compute similarity between two vectors.

    Args:
        vector_name: Name of the vector collection (for validation)
        vector1: First vector
        vector2: Second vector
        distance_type: Distance metric to use
        search_service: Search service implementation

    Returns:
        dict: Similarity score between vectors
    """
    try:
        similarity = await search_service.compute_similarity(
            vector1,
            vector2,
            distance_type
        )
        return {"similarity": similarity}

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error computing similarity: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to compute similarity: {str(e)}"
        )