import pandas as pd
from typing import Dict, Any, Tuple, List
import logging

logger = logging.getLogger(__name__)

class AnomalyAnalyzer:
    """
    Analyzes structured log data for spikes, recurring errors, and incidents.
    """
    def __init__(self, spike_threshold_multiplier: float = 3.0):
        # Spike if error rate in a window is 3x the average
        self.spike_threshold = spike_threshold_multiplier

    def get_top_errors(self, df: pd.DataFrame, limit: int = 5) -> pd.DataFrame:
        """Returns the most frequent error messages and their counts."""
        errors_df = df[df['severity'].isin(['ERROR', 'FATAL'])]
        if errors_df.empty:
            return pd.DataFrame()
            
        summary = errors_df.groupby(['service', 'message', 'error_code']).size().reset_index(name='count')
        summary = summary.sort_values('count', ascending=False).head(limit)
        return summary

    def detect_spikes(self, df: pd.DataFrame, window_minutes: int = 10) -> List[Dict[str, Any]]:
        """
        Detects anomalies by analyzing error counts in rolling time windows.
        Returns a list of incident windows where error rate spiked.
        """
        errors_df = df[df['severity'].isin(['ERROR', 'FATAL'])].copy()
        if errors_df.empty:
            return []

        # Set timestamp as index and sort
        errors_df.set_index('timestamp', inplace=True)
        errors_df.sort_index(inplace=True)

        # Resample into time windows
        window_str = f"{window_minutes}min"
        # Since pandas 2.2, 'min' is the preferred string, but 'T' or 'min' works.
        counts = errors_df.resample(window_str).size()
        
        if len(counts) < 3:
            return [] # Not enough data for baseline

        mean_errors = counts.mean()
        threshold = max(mean_errors * self.spike_threshold, 5) # At least 5 errors to be a spike

        spikes = counts[counts > threshold]
        
        incidents = []
        for timestamp, count in spikes.items():
            incidents.append({
                "window_start": timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                "error_count": int(count),
                "baseline_mean": round(mean_errors, 2),
                "severity": "CRITICAL" if count > mean_errors * 5 else "HIGH"
            })
            
        logger.info(f"Detected {len(incidents)} anomalous spikes.")
        return incidents

    def generate_summary_stats(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculates basic summary statistics."""
        if df.empty:
            return {}
            
        total_logs = len(df)
        error_logs = len(df[df['severity'].isin(['ERROR', 'FATAL'])])
        services = df['service'].nunique()
        
        return {
            "total_logs": total_logs,
            "error_rate_percent": round((error_logs / total_logs) * 100, 2) if total_logs > 0 else 0,
            "total_errors": error_logs,
            "unique_services_affected": services
        }
