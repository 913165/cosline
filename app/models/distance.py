# app/models/distance.py
from enum import Enum
from typing import Optional


class Distance(Enum):
    """
    Enum to represent different types of distance measures with corresponding numeric values.

    References:
        - Cosine Similarity: https://en.wikipedia.org/wiki/Cosine_similarity
        - Euclidean Distance: https://en.wikipedia.org/wiki/Euclidean_distance
        - Dot Product: https://en.wikipedia.org/wiki/Dot_product
        - Manhattan Distance: https://simple.wikipedia.org/wiki/Manhattan_distance
    """
    Cosine = 1  # Cosine similarity
    Euclidean = 2  # Euclidean distance
    Dot = 3  # Dot product
    Manhattan = 4  # Manhattan distance

    @property
    def value(self) -> int:
        """Get the numeric value of the distance measure."""
        return super().value

    @classmethod
    def from_string(cls, distance_str: str) -> Optional['Distance']:
        """
        Get Distance enum from string value.

        Args:
            distance_str: String representation of distance metric

        Returns:
            Distance enum value if found, None otherwise
        """
        try:
            return cls[distance_str]
        except KeyError:
            # Handle case-insensitive matching
            distance_str_upper = distance_str.upper()
            for distance in cls:
                if distance.name.upper() == distance_str_upper:
                    return distance
            return None


if __name__ == "__main__":
    # Test the Distance enum
    test_strings = ["Cosine", "cosine", "COSINE", "euclidean", "Invalid"]

    for test_str in test_strings:
        distance = Distance.from_string(test_str)
        if distance:
            print(f"String: {test_str} -> Distance: {distance.name} (value: {distance.value})")
        else:
            print(f"String: {test_str} -> Invalid distance metric")