import pandas as pd
import logging
import os

logger = logging.getLogger(__name__)


class CSVLoader:
    """
    Writes a transformed DataFrame to a CSV output file.
    Useful for inspection, downstream handoff, or debugging.
    """

    def __init__(self, output_path: str, encoding: str = "utf-8"):
        self.output_path = output_path
        self.encoding = encoding

    def load(self, df: pd.DataFrame) -> int:
        if df.empty:
            logger.warning("CSVLoader: received empty DataFrame — nothing to write.")
            return 0

        os.makedirs(os.path.dirname(self.output_path), exist_ok=True)
        df.to_csv(self.output_path, index=False, encoding=self.encoding)
        logger.info(f"CSVLoader: wrote {len(df)} records to {self.output_path}.")
        return len(df)
