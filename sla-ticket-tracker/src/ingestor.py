import pandas as pd
import logging

logger = logging.getLogger(__name__)

class TicketIngestor:
    """Reads support tickets from a data source."""
    
    def __init__(self, filepath: str):
        self.filepath = filepath

    def load_data(self) -> pd.DataFrame:
        """Loads and cleans the ticket data."""
        logger.info(f"Loading tickets from {self.filepath}...")
        
        try:
            df = pd.read_csv(self.filepath)
        except Exception as e:
            logger.error(f"Failed to read CSV: {e}")
            return pd.DataFrame()
            
        required_cols = ['ticket_id', 'severity', 'status', 'created_at']
        for col in required_cols:
            if col not in df.columns:
                logger.error(f"Missing required column: {col}")
                return pd.DataFrame()

        # Parse dates
        df['created_at'] = pd.to_datetime(df['created_at'])
        if 'resolved_at' in df.columns:
            df['resolved_at'] = pd.to_datetime(df['resolved_at'])
        else:
            df['resolved_at'] = pd.NaT

        # Normalize status
        df['status'] = df['status'].str.upper()

        logger.info(f"Successfully loaded {len(df)} tickets.")
        return df
