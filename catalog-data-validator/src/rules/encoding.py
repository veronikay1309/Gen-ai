import pandas as pd
from typing import List, Dict, Any
from src.rules import ValidationRule

class EncodingRule(ValidationRule):
    """
    Checks for encoding issues in text columns.
    Detects:
    1. Unicode replacement character '' (indicating bad decoding).
    2. Common Mojibake sequences (e.g., 'â€', 'Ã©').
    3. Non-ASCII characters in columns expected to be purely ASCII.
    """
    def __init__(self, name: str, severity: str = "WARNING", params: Dict[str, Any] = None):
        super().__init__(name, severity, params)
        self.columns = self.params.get("columns", [])
        self.ascii_only = self.params.get("ascii_only", False)
        self.detect_mojibake = self.params.get("detect_mojibake", True)

        # Common mojibake regex markers
        self.mojibake_markers = ["â\x80", "â\x84", "Ã\x83", "Ã\x82", "Ã\x89", "Ã\xa9", "ï¿½", "â€", "â\u20ac"]

    def validate(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        defects = []
        for col in self.columns:
            if col not in df.columns:
                continue

            non_null_series = df[col].dropna()
            for idx, raw_val in non_null_series.items():
                val = str(raw_val)
                row_id = df.loc[idx].get("id") or df.loc[idx].get("sku") or df.loc[idx].get("asin") or idx
                
                # 1. Check for Unicode replacement character
                if "\ufffd" in val:
                    defects.append({
                        "row_index": row_id,
                        "column": col,
                        "rule": self.name,
                        "value": raw_val,
                        "severity": self.severity,
                        "message": f"Contains Unicode replacement character '' (likely decoding error)."
                    })
                    continue

                # 2. Check for common Mojibake markers
                if self.detect_mojibake:
                    has_mojibake = False
                    for marker in self.mojibake_markers:
                        if marker in val:
                            has_mojibake = True
                            break
                    if has_mojibake:
                        defects.append({
                            "row_index": row_id,
                            "column": col,
                            "rule": f"{self.name}_mojibake",
                            "value": raw_val,
                            "severity": self.severity,
                            "message": f"Contains potential Mojibake patterns (e.g., bad encoding conversion)."
                        })
                        continue

                # 3. Check for ASCII-only if configured
                if self.ascii_only:
                    try:
                        val.encode("ascii")
                    except UnicodeEncodeError:
                        defects.append({
                            "row_index": row_id,
                            "column": col,
                            "rule": f"{self.name}_non_ascii",
                            "value": raw_val,
                            "severity": self.severity,
                            "message": f"Contains non-ASCII characters in an ASCII-only column."
                        })

        return defects
