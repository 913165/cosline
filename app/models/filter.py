# app/models/filter.py
from pydantic import BaseModel
from typing import Any, Dict, List

class FilterCriteria(BaseModel):
    key: str
    value: Any

def convert_to_filter_criteria(metadata: Dict[str, List[str]]) -> List[FilterCriteria]:
    """Convert query parameters to filter criteria."""
    filters = []
    for key, values in metadata.items():
        for value in values:
            filters.append(FilterCriteria(key=key, value=value))
    return filters