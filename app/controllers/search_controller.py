# app/controllers/search_controller.py
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any
import logging
from app.models import Point, Payload, Distance
from app.services import ISearchService, SQLiteSearchService

router = APIRouter(
    prefix="/api/v1/collections",
    tags=["search"]
)

logger = logging.getLogger(__name__)


def get_search_service() -> ISearchService:
    """
    Dependency injection for search service.
    Can be easily modified to return different implementations.
    """
    return SQLiteSearchService()


@router.post("/{vector_name}/search")
async def search_vectors(
        vector_name: str,
        query_vector: List[float],
        top_k: int = 10,
        distance_type: Distance = Distance.Cosine,
        search_service: ISearchService = Depends(get_search_service)
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Search for similar vectors in a collection.

    Args:
        vector_name: Name of the vector collection
        query_vector: Query vector to search for
        top_k: Number of results to return (default: 10)
        distance_type: Distance metric to use (default: Cosine)
        search_service: Search service implementation

    Returns:
        dict: Search results with similarity scores

    Raises:
        HTTPException: If collection not found or search fails
    """
    try:
        logger.info(f"Searching in collection: {vector_name} with top_k={top_k}")

        if not query_vector:
            raise ValueError("Query vector cannot be empty")

        results = await search_service.search_vectors(
            vector_name,
            query_vector,
            top_k,
            distance_type
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
        point_id: str,
        top_k: int = 10,
        search_service: ISearchService = Depends(get_search_service)
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Search for similar vectors using an existing point's ID.

    Args:
        vector_name: Name of the vector collection
        point_id: ID of the point to use as query
        top_k: Number of results to return (default: 10)
        search_service: Search service implementation

    Returns:
        dict: Search results with similarity scores

    Raises:
        HTTPException: If point not found, collection not found, or search fails
    """
    try:
        logger.info(f"Searching by ID in collection: {vector_name}, point_id: {point_id}")

        if not point_id or not point_id.strip():
            raise ValueError("Point ID cannot be empty")

        results = await search_service.search_by_id(
            vector_name,
            point_id,
            top_k
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
    except ValueError as e:
        if "Point not found" in str(e):
            logger.error(f"Point not found: {point_id}")
            raise HTTPException(
                status_code=404,
                detail=f"Point with ID {point_id} not found"
            )
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Search by ID error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Search by ID failed: {str(e)}"
        )