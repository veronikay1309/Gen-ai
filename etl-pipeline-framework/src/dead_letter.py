import os
import json
import logging
import pandas as pd
from datetime import datetime
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class DeadLetterQueue:
    """
    Captures failed records during pipeline execution and writes them to
    a dead-letter folder with full error context for manual review or reprocessing.

    Each run creates a timestamped JSONL file with all failed records + reasons.
    """

    def __init__(self, output_dir: str = "dead_letter"):
        self.output_dir = output_dir
        self.failed_records: List[Dict[str, Any]] = []

    def add(self, record: Dict[str, Any], error: str, stage: str):
        """
        Adds a single failed record to the in-memory dead-letter queue.

        Args:
            record: The row dict that failed processing.
            error:  The error message or exception string.
            stage:  The pipeline stage where it failed (e.g., 'cleaner', 'loader').
        """
        self.failed_records.append({
            "stage": stage,
            "error": error,
            "timestamp": datetime.utcnow().isoformat(),
            "record": record,
        })

    def add_dataframe(self, df: pd.DataFrame, error: str, stage: str):
        """
        Adds all rows of a DataFrame to the dead-letter queue with the same error.
        Used when an entire batch fails (e.g., a loader failure).
        """
        for _, row in df.iterrows():
            self.add(row.to_dict(), error, stage)

    def flush(self) -> int:
        """
        Writes all queued failed records to a timestamped JSONL file.
        Returns the number of records written.
        Clears the in-memory queue after writing.
        """
        if not self.failed_records:
            logger.info("DeadLetterQueue: no failed records to flush.")
            return 0

        os.makedirs(self.output_dir, exist_ok=True)
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(self.output_dir, f"failed_{timestamp}.jsonl")

        with open(output_path, "w") as f:
            for entry in self.failed_records:
                f.write(json.dumps(entry, default=str) + "\n")

        count = len(self.failed_records)
        logger.warning(f"DeadLetterQueue: flushed {count} failed records to {output_path}")
        self.failed_records = []
        return count

    def count(self) -> int:
        return len(self.failed_records)
