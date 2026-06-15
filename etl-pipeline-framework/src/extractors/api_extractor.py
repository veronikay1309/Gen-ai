import requests
import pandas as pd
import logging
import time
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class APIExtractor:
    """
    Extracts paginated JSON data from a REST API endpoint.
    Supports auth headers, query params, and simple pagination via offset/limit.
    """

    def __init__(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        page_size: int = 100,
        max_pages: int = 10,
        rate_limit_delay: float = 0.5,
        data_key: Optional[str] = None,
    ):
        self.url = url
        self.headers = headers or {}
        self.params = params or {}
        self.page_size = page_size
        self.max_pages = max_pages
        self.rate_limit_delay = rate_limit_delay
        # Key in JSON response that contains records (e.g., "items", "results", "data")
        self.data_key = data_key

    def extract(self) -> pd.DataFrame:
        """
        Fetches all pages from the API and returns a combined DataFrame.
        Stops when an empty page is returned or max_pages is reached.
        """
        all_records = []
        page = 0

        logger.info(f"Starting API extraction from: {self.url}")

        while page < self.max_pages:
            paginated_params = {**self.params, "limit": self.page_size, "offset": page * self.page_size}

            try:
                response = requests.get(self.url, headers=self.headers, params=paginated_params, timeout=10)
                response.raise_for_status()
            except requests.exceptions.Timeout:
                raise RuntimeError(f"API request timed out: {self.url}")
            except requests.exceptions.HTTPError as e:
                raise RuntimeError(f"API returned error {response.status_code}: {str(e)}")
            except requests.exceptions.ConnectionError:
                raise RuntimeError(f"Cannot connect to API: {self.url}")

            data = response.json()

            # Navigate to nested data key if configured
            if self.data_key:
                records = data.get(self.data_key, [])
            elif isinstance(data, list):
                records = data
            else:
                records = [data]

            if not records:
                logger.info(f"Empty page at offset {page * self.page_size} — extraction complete.")
                break

            all_records.extend(records)
            logger.info(f"Page {page + 1}: fetched {len(records)} records (total: {len(all_records)})")
            page += 1

            # Polite rate limiting between requests
            time.sleep(self.rate_limit_delay)

        if not all_records:
            logger.warning("No records extracted from API.")
            return pd.DataFrame()

        df = pd.DataFrame(all_records)
        logger.info(f"API extraction complete: {len(df)} total records.")
        return df
