import pandas as pd
import logging
from typing import Optional, List

logger = logging.getLogger(__name__)


class CSVExtractor:
    """
    Extracts data from a CSV file into a pandas DataFrame.
    Supports configurable encoding and optional column selection.
    """

    def __init__(self, path: str, encoding: str = "utf-8", columns: Optional[List[str]] = None):
        self.path = path
        self.encoding = encoding
        self.columns = columns

    def extract(self) -> pd.DataFrame:
        """
        Reads the CSV file and returns a DataFrame.
        Raises FileNotFoundError if the path does not exist.
        """
        logger.info(f"Extracting CSV from: {self.path}")
        try:
            df = pd.read_csv(self.path, encoding=self.encoding)
        except FileNotFoundError:
            raise FileNotFoundError(f"CSV source file not found: {self.path}")
        except Exception as e:
            raise RuntimeError(f"Failed to read CSV '{self.path}': {str(e)}")

        # Optionally select specific columns only
        if self.columns:
            missing = [c for c in self.columns if c not in df.columns]
            if missing:
                raise ValueError(f"Requested columns not found in CSV: {missing}")
            df = df[self.columns]

        logger.info(f"Extracted {len(df)} records, {len(df.columns)} columns from CSV.")
        return df
