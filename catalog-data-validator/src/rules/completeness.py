import pandas as pd
from typing import List, Dict, Any
from src.rules import ValidationRule

class CompletenessRule(ValidationRule):
    """
    Checks if specified columns contain null, NaN, empty strings, or string 'nan'.
    """
    def __init__(self, name: str, severity: str = "WARNING", params: Dict[str, Any] = None):
        super().__init__(name, severity, params)
        self.columns = self.params.get("columns", [])

    def validate(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        defects = []
        for col in self.columns:
            if col not in df.columns:
                defects.append({
                    "row_index": "ALL",
                    "column": col,
                    "rule": self.name,
                    "value": None,
                    "severity": "CRITICAL",
                    "message": f"Required column '{col}' is missing from the dataset."
                })
                continue

            # Identify null or empty strings
            is_missing = df[col].isna()
            
            # Treat empty strings or "nan" string representations as missing
            if pd.api.types.is_string_dtype(df[col]):
                clean_str = df[col].astype(str).str.strip()
                is_missing = is_missing | (clean_str == "") | (clean_str.str.lower() == "nan")

            defective_rows = df[is_missing]
            for idx, row in defective_rows.iterrows():
                val = row[col] if pd.notna(row[col]) else None
                # Use 'id' or 'sku' or 'asin' as row identifier if available, fallback to index
                row_id = row.get("id") or row.get("sku") or row.get("asin") or idx
                defects.append({
                    "row_index": row_id,
                    "column": col,
                    "rule": self.name,
                    "value": val,
                    "severity": self.severity,
                    "message": f"Value in column '{col}' is missing or empty."
                })
        return defects
