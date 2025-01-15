# app/controllers/payload_controller.py
from typing import List, Dict, Optional
from fastapi import APIRouter, HTTPException, Query, Depends
import logging
from app.models import Payload, Point, FilterCriteria
from app.models.filter import convert_to_filter_criteria
from app.services import IPayloadService, SQLitePayloadService
from app.utils.filters import filter_payload

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/collections",
    tags=["payloads"]
)


def get_payload_service() -> IPayloadService:
    """
    Dependency injection for payload service.
    Can be easily modified to return different implementations.
    """
    return SQLitePayloadService()


@router.post("/{vector_name}/payload", status_code=201)
async def add_payload(
        vector_name: str,
        payload: Payload,
        payload_service: IPayloadService = Depends(get_payload_service)
) -> Dict[str, str]:
    """
    Add a single payload to a vector store.

    Args:
        vector_name: Name of the vector store
        payload: Payload object containing vector data
        payload_service: Payload service implementation

    Returns:
        dict: Success message

    Raises:
        HTTPException: If error occurs while adding payload
    """
    logger.info(f"Adding payload to vector store: {vector_name}")
    try:
        payload_service.add_payload_to_vector_store(vector_name, payload)
        return {"message": f"Payload added successfully to {vector_name}"}

    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except FileNotFoundError:
        logger.error(f"Vector store not found: {vector_name}")
        raise HTTPException(
            status_code=404,
            detail=f"Vector store {vector_name} not found"
        )
    except Exception as e:
        logger.error(f"Error processing payload: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing payload: {str(e)}"
        )


@router.post("/{vector_name}/payloads/batch")
async def add_payloads(
        vector_name: str,
        payloads: List[Payload],
        payload_service: IPayloadService = Depends(get_payload_service)
) -> Dict[str, str]:
    """
    Add multiple payloads to a vector store in batch.

    Args:
        vector_name: Name of the vector store
        payloads: List of payload objects to add
        payload_service: Payload service implementation

    Returns:
        dict: Success message with count
    """
    logger.info(f"Received batch of {len(payloads)} payloads for vector store: {vector_name}")

    try:
        if not payloads:
            raise ValueError("No payloads provided")

        payload_service.add_payloads_to_vector_store(vector_name, payloads)
        return {
            "message": f"Successfully added {len(payloads)} payloads to {vector_name}",
            "count": str(len(payloads))  # Convert count to string
        }

    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except FileNotFoundError:
        logger.error(f"Vector store not found: {vector_name}")
        raise HTTPException(
            status_code=404,
            detail=f"Vector store {vector_name} not found"
        )
    except Exception as e:
        logger.error(f"Error processing payloads: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing payloads: {str(e)}"
        )


@router.get("/{vector_name}/payloads")
async def get_all_payloads(
        vector_name: str,
        payload_service: IPayloadService = Depends(get_payload_service)
) -> List[Point]:
    """
    Get all payloads from a vector store.

    Args:
        vector_name: Name of the vector store
        payload_service: Payload service implementation

    Returns:
        List[Point]: List of points from the vector store

    Raises:
        HTTPException: If vector store not found or error occurs while fetching
    """
    try:
        points = payload_service.read_vector_store(vector_name)
        if not points:
            logger.info(f"No points found in vector store: {vector_name}")
            return []

        return points

    except FileNotFoundError:
        logger.error(f"Vector store not found: {vector_name}")
        raise HTTPException(
            status_code=404,
            detail=f"Vector store {vector_name} not found"
        )
    except Exception as e:
        logger.error(f"Error fetching payloads: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching payloads: {str(e)}"
        )