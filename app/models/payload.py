# app/models/payload.py
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from uuid import UUID

class Payload(BaseModel):
    id: UUID
    content: str
    embedding: List[float]
    metadata: Optional[Dict[str, Any]] = None