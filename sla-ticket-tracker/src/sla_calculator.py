import pandas as pd
import numpy as np
from datetime import datetime, timezone
import json
import logging

logger = logging.getLogger(__name__)

class SLACalculator:
    """Calculates resolution times and SLA breaches based on severity policies."""
    
    def __init__(self, policies_file: str):
        with open(policies_file, 'r') as f:
            config = json.load(f)
            self.policies = config.get("policies", {})
            self.at_risk_threshold = config.get("at_risk_threshold", 0.8)

    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculates SLA metrics for each ticket."""
        if df.empty:
            return df

        # Current time for calculating open tickets
        now = datetime.now(timezone.utc).replace(tzinfo=None)

        # 1. Map SLA limits to the dataframe
        df['sla_limit_hours'] = df['severity'].map(lambda x: self.policies.get(x, {}).get("limit_hours", 24))

        # 2. Calculate time elapsed
        # For closed tickets: resolved_at - created_at
        # For open tickets: now - created_at
        df['end_time'] = df['resolved_at'].fillna(now)
        df['elapsed_hours'] = (df['end_time'] - df['created_at']).dt.total_seconds() / 3600.0

        # 3. Determine if breached
        df['is_breached'] = df['elapsed_hours'] > df['sla_limit_hours']

        # 4. Determine if At-Risk (Open tickets where elapsed > threshold * limit)
        is_open = df['status'] != 'CLOSED'
        is_near_limit = df['elapsed_hours'] > (df['sla_limit_hours'] * self.at_risk_threshold)
        df['is_at_risk'] = is_open & is_near_limit & ~df['is_breached']

        return df

    def get_summary_metrics(self, df: pd.DataFrame) -> dict:
        """Generates summary metrics for the dashboard."""
        if df.empty:
            return {}

        total_tickets = len(df)
        closed_tickets = df[df['status'] == 'CLOSED']
        open_tickets = df[df['status'] != 'CLOSED']
        
        breached = len(df[df['is_breached']])
        at_risk = len(df[df['is_at_risk']])
        
        # Average resolution time by severity
        avg_res_time = closed_tickets.groupby('severity')['elapsed_hours'].mean().round(2).to_dict()

        return {
            "total_tickets": total_tickets,
            "open_tickets": len(open_tickets),
            "closed_tickets": len(closed_tickets),
            "breached_count": breached,
            "breach_rate": round((breached / total_tickets) * 100, 2) if total_tickets > 0 else 0,
            "at_risk_count": at_risk,
            "avg_resolution_time_hrs": avg_res_time
        }
