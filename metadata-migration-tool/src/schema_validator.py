from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field, ValidationError
import logging

logger = logging.getLogger(__name__)

class V2ProductSchema(BaseModel):
    """
    Strict target schema for V2 Product Metadata.
    Migrated records MUST pass this validation.
    """
    sku: str = Field(..., min_length=3, description="Unique product identifier")
    title: str = Field(..., min_length=1, description="Product title")
    price: float = Field(..., ge=0.0, description="Product price in target currency")
    inventory_level: int = Field(..., ge=0, description="Available stock count")
    currency: str = Field(..., min_length=3, max_length=3, description="Currency code (e.g. USD)")
    status: str = Field(..., description="Product status (e.g. ACTIVE, INACTIVE)")
    full_description: str = Field(..., description="Combined detailed description")
    category: str = Field(..., description="Product category")


class SchemaValidator:
    def __init__(self):
        self.schema_class = V2ProductSchema

    def validate_record(self, record: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        Validates a single record against the target schema.
        Returns (is_valid, error_message).
        """
        try:
            self.schema_class(**record)
            return True, None
        except ValidationError as e:
            # Flatten pydantic errors into a readable string
            errors = []
            for err in e.errors():
                loc = ".".join(map(str, err.get('loc', [])))
                msg = err.get('msg', 'Unknown error')
                errors.append(f"[{loc}]: {msg}")
            return False, "; ".join(errors)
