from abc import ABC, abstractmethod
import pandas as pd
from typing import List, Dict, Any

class ValidationRule(ABC):
    """
    Abstract Base Class for all validation rules (Strategy Pattern).
    """
    def __init__(self, name: str, severity: str = "WARNING", params: Dict[str, Any] = None):
        self.name = name
        self.severity = severity
        self.params = params or {}

    @abstractmethod
    def validate(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Validates the input DataFrame and returns a list of defects.
        
        Each defect is a dictionary:
        {
            "row_index": Any,       # Index or primary key of the row (e.g. ASIN or index)
            "column": str,          # Name of the invalid column
            "rule": str,            # Name of this rule
            "value": Any,           # The invalid value found
            "severity": str,        # CRITICAL, WARNING, or INFO
            "message": str          # Descriptive error message
        }
        """
        pass
