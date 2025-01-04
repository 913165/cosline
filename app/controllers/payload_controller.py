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
    print('payload : ', payload)


    try:
        success = payload_service.add_payload_to_vector_store(vector_name, payload)

        return {"message": f"Payload added successfully to {vector_name}"}

    except Exception as e:
        logger.error(f"Error processing payload: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing payload: {str(e)}"
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




