import pandas as pd
import logging
from typing import List

logger = logging.getLogger(__name__)


class Deduplicator:
    """
    Removes exact duplicate rows from a DataFrame based on specified key columns.
    Keeps the first occurrence and drops subsequent duplicates.
    """

    def __init__(self, key_columns: List[str]):
        self.key_columns = key_columns

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        initial_count = len(df)
        df = df.copy()

        # Only deduplicate on columns that exist in the DataFrame
        existing_keys = [c for c in self.key_columns if c in df.columns]

        if not existing_keys:
            logger.warning(f"Deduplicator: none of the key columns {self.key_columns} exist — skipping.")
            return df

        df = df.drop_duplicates(subset=existing_keys, keep="first")
        removed = initial_count - len(df)

        if removed:
            logger.info(f"Deduplicator: removed {removed} duplicate rows on keys {existing_keys}.")
        else:
            logger.info("Deduplicator: no duplicates found.")

        return df
