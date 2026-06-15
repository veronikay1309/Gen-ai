import pandas as pd
import logging
from sqlalchemy import create_engine, text
from typing import Literal

logger = logging.getLogger(__name__)


class SQLiteLoader:
    """
    Loads a DataFrame into a SQLite database table using SQLAlchemy.
    Supports replace, append, and upsert (insert-or-replace) modes.
    Idempotent: re-running with 'replace' or 'upsert' won't create duplicates.
    """

    def __init__(self, db_path: str, table: str, if_exists: Literal["replace", "append", "upsert"] = "replace"):
        self.db_path = db_path
        self.table = table
        self.if_exists = if_exists
        self.engine = create_engine(f"sqlite:///{db_path}")

    def load(self, df: pd.DataFrame) -> int:
        """
        Loads the DataFrame into the configured SQLite table.
        Returns the number of records successfully written.
        """
        if df.empty:
            logger.warning("SQLiteLoader: received empty DataFrame — nothing to load.")
            return 0

        if self.if_exists == "upsert":
            return self._upsert(df)
        else:
            # 'replace' drops and recreates the table; 'append' adds rows
            df.to_sql(self.table, con=self.engine, if_exists=self.if_exists, index=False)
            logger.info(f"SQLiteLoader: loaded {len(df)} records into '{self.table}' (mode={self.if_exists}).")
            return len(df)

    def _upsert(self, df: pd.DataFrame) -> int:
        """
        Performs an INSERT OR REPLACE into SQLite (idempotent upsert).
        Requires the table to already have a PRIMARY KEY defined.
        Falls back to replace mode if table doesn't exist yet.
        """
        with self.engine.connect() as conn:
            # Check if table exists
            result = conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name=:name"),
                {"name": self.table}
            ).fetchone()

            if result is None:
                # Table doesn't exist yet — create it via pandas
                df.to_sql(self.table, con=conn, if_exists="replace", index=False)
                logger.info(f"SQLiteLoader (upsert): created table '{self.table}' with {len(df)} records.")
            else:
                # Table exists — use INSERT OR REPLACE for idempotent upsert
                cols = ", ".join(df.columns)
                placeholders = ", ".join([f":{c}" for c in df.columns])
                sql = text(f"INSERT OR REPLACE INTO {self.table} ({cols}) VALUES ({placeholders})")
                records = df.to_dict(orient="records")
                conn.execute(sql, records)
                conn.commit()
                logger.info(f"SQLiteLoader (upsert): upserted {len(df)} records into '{self.table}'.")

        return len(df)
