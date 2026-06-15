import pandas as pd
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)


class DataCleaner:
    """
    Cleans a DataFrame by:
    - Stripping leading/trailing whitespace from string columns
    - Standardising column casing (lowercase)
    - Dropping rows with nulls in critical columns
    """

    def __init__(
        self,
        strip_whitespace: bool = True,
        lowercase_columns: Optional[List[str]] = None,
        drop_nulls_in: Optional[List[str]] = None,
    ):
        self.strip_whitespace = strip_whitespace
        self.lowercase_columns = lowercase_columns or []
        self.drop_nulls_in = drop_nulls_in or []

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        initial_count = len(df)
        df = df.copy()

        # Strip whitespace from all string columns
        if self.strip_whitespace:
            str_cols = df.select_dtypes(include="object").columns
            for col in str_cols:
                df[col] = df[col].astype(str).str.strip()
                # Treat "nan" strings (from str conversion of NaN) as actual NaN
                df[col] = df[col].replace("nan", pd.NA)

        # Lowercase specified columns
        for col in self.lowercase_columns:
            if col in df.columns:
                df[col] = df[col].str.lower()

        # Drop rows missing critical values
        if self.drop_nulls_in:
            existing = [c for c in self.drop_nulls_in if c in df.columns]
            df = df.dropna(subset=existing)

        dropped = initial_count - len(df)
        if dropped:
            logger.info(f"DataCleaner: dropped {dropped} rows with nulls in critical columns.")
        logger.info(f"DataCleaner: {len(df)} records after cleaning.")
        return df
