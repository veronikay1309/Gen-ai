import pandas as pd
from typing import List, Dict, Any
from difflib import SequenceMatcher
from src.rules import ValidationRule

class DuplicatesRule(ValidationRule):
    """
    Detects duplicate records in the catalog.
    Supports:
    1. Exact duplicates on specific key columns (e.g. 'asin' or 'sku').
    2. Fast fuzzy deduplication on a text column (e.g. 'title') using a sorted sliding-window approach.
    """
    def __init__(self, name: str, severity: str = "WARNING", params: Dict[str, Any] = None):
        super().__init__(name, severity, params)
        self.key_columns = self.params.get("key_columns", [])
        self.fuzzy_column = self.params.get("fuzzy_column")
        self.fuzzy_threshold = self.params.get("fuzzy_threshold", 0.90)
        self.fuzzy_window = self.params.get("fuzzy_window", 5) # Number of adjacent sorted rows to compare

    def validate(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        defects = []
        
        # 1. Exact Duplicate Check
        for col in self.key_columns:
            if col not in df.columns:
                continue

            # Find all duplicated values (excluding nulls)
            non_null_series = df[col].dropna()
            duplicates = non_null_series[non_null_series.duplicated(keep=False)]
            
            # Group by duplicate value to find all rows sharing it
            duplicate_groups = duplicates.groupby(duplicates)
            for value, indices in duplicate_groups.groups.items():
                # Report all rows in the duplicate group
                for idx in indices:
                    row = df.loc[idx]
                    row_id = row.get("id") or row.get("sku") or row.get("asin") or idx
                    defects.append({
                        "row_index": row_id,
                        "column": col,
                        "rule": self.name,
                        "value": value,
                        "severity": self.severity,
                        "message": f"Duplicate key value '{value}' found in column '{col}'."
                    })

        # 2. Fast Fuzzy Duplicate Check (e.g. on 'title')
        if self.fuzzy_column and self.fuzzy_column in df.columns:
            # Safely select only columns that exist to prevent KeyErrors
            cols_to_select = [self.fuzzy_column]
            for optional_col in ["id", "sku", "asin"]:
                if optional_col in df.columns:
                    cols_to_select.append(optional_col)
            # We sort the dataframe by the target fuzzy column to bring similar titles adjacent to each other
            sorted_df = df[cols_to_select].dropna(subset=[self.fuzzy_column]).copy()
            sorted_df["clean_text"] = sorted_df[self.fuzzy_column].astype(str).str.lower().str.strip()
            sorted_df = sorted_df.sort_values(by="clean_text").reset_index()

            n = len(sorted_df)
            reported_pairs = set()

            for i in range(n):
                text_i = sorted_df.loc[i, "clean_text"]
                id_i = sorted_df.loc[i, "id"] or sorted_df.loc[i, "sku"] or sorted_df.loc[i, "asin"] or sorted_df.loc[i, "index"]
                original_title_i = sorted_df.loc[i, self.fuzzy_column]

                # Compare with the next 'fuzzy_window' adjacent items
                for j in range(i + 1, min(i + 1 + self.fuzzy_window, n)):
                    text_j = sorted_df.loc[j, "clean_text"]
                    id_j = sorted_df.loc[j, "id"] or sorted_df.loc[j, "sku"] or sorted_df.loc[j, "asin"] or sorted_df.loc[j, "index"]
                    original_title_j = sorted_df.loc[j, self.fuzzy_column]

                    # Skip self-comparison or already reported pairs
                    if id_i == id_j or (id_i, id_j) in reported_pairs or (id_j, id_i) in reported_pairs:
                        continue

                    # Calculate string similarity ratio
                    ratio = SequenceMatcher(None, text_i, text_j).ratio()
                    if ratio >= self.fuzzy_threshold:
                        reported_pairs.add((id_i, id_j))
                        defects.append({
                            "row_index": id_i,
                            "column": self.fuzzy_column,
                            "rule": f"{self.name}_fuzzy",
                            "value": original_title_i,
                            "severity": self.severity,
                            "message": f"Fuzzy duplicate title detected (similarity {ratio:.2f}) with ID '{id_j}': '{original_title_j}'"
                        })
                        defects.append({
                            "row_index": id_j,
                            "column": self.fuzzy_column,
                            "rule": f"{self.name}_fuzzy",
                            "value": original_title_j,
                            "severity": self.severity,
                            "message": f"Fuzzy duplicate title detected (similarity {ratio:.2f}) with ID '{id_i}': '{original_title_i}'"
                        })

        return defects
