from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from uuid import UUID

class Point(BaseModel):
    id: UUID
    content: str
    embedding: List[float]
    metadata: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True