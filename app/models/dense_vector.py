# app/models/dense_vector.py
from pydantic import BaseModel
from .distance import Distance

class DenseVector(BaseModel):
    """
    A class representing a dense vector with dimension and distance metric.
    """
    dim: int
    distance: Distance

    def __str__(self) -> str:
        """String representation of the DenseVector."""
        return f"DenseVector(dim={self.dim}, distance={self.distance})"