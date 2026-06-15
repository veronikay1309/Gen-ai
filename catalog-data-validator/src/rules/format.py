import pandas as pd
import re
from typing import List, Dict, Any
from src.rules import ValidationRule

class RegexFormatRule(ValidationRule):
    """
    Validates that string values in specified columns match a regular expression pattern.
    """
    def __init__(self, name: str, severity: str = "WARNING", params: Dict[str, Any] = None):
        super().__init__(name, severity, params)
        # mapping of column -> regex pattern
        self.patterns = self.params.get("patterns", {})

    def validate(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        defects = []
        for col, pattern_str in self.patterns.items():
            if col not in df.columns:
                continue

            try:
                pattern = re.compile(pattern_str)
            except re.error as e:
                # If regex is invalid, log or add critical rule configuration defect
                defects.append({
                    "row_index": "CONFIG",
                    "column": col,
                    "rule": self.name,
                    "value": pattern_str,
                    "severity": "CRITICAL",
                    "message": f"Invalid regex pattern '{pattern_str}' configured: {str(e)}"
                })
                continue

            # We only validate non-null values
            non_null_mask = df[col].notna() & (df[col].astype(str).str.strip() != "")
            
            for idx, row in df[non_null_mask].iterrows():
                val = str(row[col])
                if not pattern.match(val):
                    row_id = row.get("id") or row.get("sku") or row.get("asin") or idx
                    defects.append({
                        "row_index": row_id,
                        "column": col,
                        "rule": self.name,
                        "value": row[col],
                        "severity": self.severity,
                        "message": f"Value '{val}' does not match the required format pattern: {pattern_str}"
                    })
        return defects


class NumericRangeRule(ValidationRule):
    """
    Validates that numeric values fall within a specified min and/or max range.
    """
    def __init__(self, name: str, severity: str = "WARNING", params: Dict[str, Any] = None):
        super().__init__(name, severity, params)
        # mapping of column -> {min: float, max: float}
        self.ranges = self.params.get("ranges", {})

    def validate(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        defects = []
        for col, bounds in self.ranges.items():
            if col not in df.columns:
                continue

            min_val = bounds.get("min")
            max_val = bounds.get("max")

            # We only validate non-null values
            non_null_mask = df[col].notna()
            
            for idx, row in df[non_null_mask].iterrows():
                try:
                    val = float(row[col])
                except (ValueError, TypeError):
                    row_id = row.get("id") or row.get("sku") or row.get("asin") or idx
                    defects.append({
                        "row_index": row_id,
                        "column": col,
                        "rule": self.name,
                        "value": row[col],
                        "severity": "CRITICAL",
                        "message": f"Value in '{col}' is not a valid number."
                    })
                    continue

                is_out_of_range = False
                msg = ""
                if min_val is not None and val < min_val:
                    is_out_of_range = True
                    msg = f"Value {val} is below minimum allowed ({min_val})."
                elif max_val is not None and val > max_val:
                    is_out_of_range = True
                    msg = f"Value {val} is above maximum allowed ({max_val})."

                if is_out_of_range:
                    row_id = row.get("id") or row.get("sku") or row.get("asin") or idx
                    defects.append({
                        "row_index": row_id,
                        "column": col,
                        "rule": self.name,
                        "value": row[col],
                        "severity": self.severity,
                        "message": msg
                    })
        return defects
