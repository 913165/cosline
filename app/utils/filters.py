# app/utils/filters.py
from app.models import Payload, FilterCriteria
from typing import List


def filter_payload(payload: Payload, filters: List[FilterCriteria]) -> bool:
    """
    Filter payload based on metadata criteria.
    Returns True if payload matches all filters.
    """
    if not filters:
        return True

    if not payload.metadata:
        return False

    for filter_criteria in filters:
        metadata_value = payload.metadata.get(filter_criteria.key)
        if metadata_value != filter_criteria.value:
            return False

    return True