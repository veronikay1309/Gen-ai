import re
from typing import Dict, Any, List
import pandas as pd
import logging

logger = logging.getLogger(__name__)

class LogParser:
    """
    Parses unstructured log files into structured DataFrames.
    Standard Format: [YYYY-MM-DD HH:MM:SS] [SEVERITY] [SERVICE_NAME] - Message (Code: X)
    Example: [2026-06-15 10:15:30] [ERROR] [checkout-api] - Payment failed (Code: 500)
    """
    def __init__(self):
        # Regex to capture Timestamp, Severity, Service, Message, and optional Error Code
        self.log_pattern = re.compile(
            r"^\[(?P<timestamp>\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2})\]\s"
            r"\[(?P<severity>[A-Z]+)\]\s"
            r"\[(?P<service>[a-zA-Z0-9_-]+)\]\s-\s"
            r"(?P<message>.*?)"
            r"(?:\s\(Code:\s(?P<error_code>\d+)\))?$"
        )

    def parse_file(self, filepath: str) -> pd.DataFrame:
        """Reads a log file line-by-line and returns a structured DataFrame."""
        parsed_records = []
        unparsable_lines = 0

        logger.info(f"Parsing log file: {filepath}")
        
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                    
                match = self.log_pattern.match(line)
                if match:
                    record = match.groupdict()
                    parsed_records.append(record)
                else:
                    unparsable_lines += 1

        if unparsable_lines > 0:
            logger.warning(f"Failed to parse {unparsable_lines} lines.")

        df = pd.DataFrame(parsed_records)
        
        # Convert types
        if not df.empty:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df['error_code'] = df['error_code'].fillna('None')

        logger.info(f"Successfully parsed {len(df)} log entries.")
        return df
