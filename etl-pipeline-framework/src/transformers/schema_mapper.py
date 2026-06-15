import pandas as pd
import logging
from typing import Dict, Optional, List

logger = logging.getLogger(__name__)


class SchemaMapper:
    """
    Maps an input DataFrame schema to a target schema by:
    - Renaming columns based on a mapping dictionary
    - Keeping only specified columns (drops the rest)
    """

    def __init__(
        self,
        rename: Optional[Dict[str, str]] = None,
        keep_columns: Optional[List[str]] = None,
    ):
        # rename: {old_name: new_name}
        self.rename = rename or {}
        self.keep_columns = keep_columns

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()

        # Rename columns that exist (silently skip missing ones)
        existing_renames = {k: v for k, v in self.rename.items() if k in df.columns}
        if existing_renames:
            df = df.rename(columns=existing_renames)
            logger.info(f"SchemaMapper: renamed columns {list(existing_renames.keys())} → {list(existing_renames.values())}")

        # Keep only the specified columns
        if self.keep_columns:
            available = [c for c in self.keep_columns if c in df.columns]
            dropped = [c for c in self.keep_columns if c not in df.columns]
            if dropped:
                logger.warning(f"SchemaMapper: keep_columns not found and skipped: {dropped}")
            df = df[available]
            logger.info(f"SchemaMapper: retained {len(available)} columns.")

        return df
