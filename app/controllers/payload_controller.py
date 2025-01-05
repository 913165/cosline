# app/controllers/payload_controller.py

from typing import List, Dict, Optional

from fastapi import APIRouter, HTTPException, Query
from app.models import Payload,FilterCriteria
from app.models.filter import convert_to_filter_criteria
from app.services.payload_service import PayloadService
from fastapi import Depends
import logging
from app.utils.filters import filter_payload

router = APIRouter(
    prefix="/api/v1/collections",
    tags=["payloads"]
)
logging.basicConfig(level = logging.INFO)
logger = logging.getLogger(__name__)


# Service dependency
def get_payload_service():
    return PayloadService()


@router.post("/{vector_name}/payload", status_code=201)
async def add_payload(
        vector_name: str,
        payload: Payload,
        payload_service: PayloadService = Depends(get_payload_service)
):
    """
    Add a payload to a vector store .

    Args:
        vector_name: Name of the vector store
        payload: Payload object containing vector data
        payload_service: Injected payload service

    Returns:
        dict: Success message

    Raises:
        HTTPException: If vector store not found or other errors occur
    """

    logger.info(f"controller : Adding payload to VectorStore: {vector_name}")


    try:
        success = payload_service.add_payload_to_vector_store(vector_name, payload)

        return {"message": f"Payload added successfully to {vector_name}"}

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
        payload_service: PayloadService = Depends(get_payload_service)
):
    """Add multiple payloads to a vector store."""
    logger.info(f"Received batch of {len(payloads)} payloads for vector store: {vector_name}")

    try:
        payload_service.add_payloads_to_vector_store(vector_name, payloads)
        return {
            "message": f"Successfully added {len(payloads)} payloads to {vector_name}",
            "count": len(payloads)
        }

    except Exception as e:
        logger.error(f"Error processing payloads: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing payloads: {str(e)}"
        )

#
@router.get("/{vector_name}/payloads")
async def get_all_payloads(
        vector_name: str,
        payload_service: PayloadService = Depends(get_payload_service)
):
    # Get points from vector store
    points = payload_service.read_vector_store(vector_name)
    return points




