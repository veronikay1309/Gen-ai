import pytest
import pandas as pd
from datetime import datetime, timedelta
from src.analyzer import AnomalyAnalyzer

@pytest.fixture
def sample_df():
    now = datetime.now()
    data = []
    
    # Normal background errors (1 per minute)
    for i in range(20):
        data.append({
            "timestamp": now + timedelta(minutes=i),
            "severity": "ERROR",
            "service": "api",
            "message": "Normal error",
            "error_code": "500"
        })
        
    # Anomaly spike (10 errors in one minute)
    spike_time = now + timedelta(minutes=25)
    for i in range(10):
        data.append({
            "timestamp": spike_time,
            "severity": "ERROR",
            "service": "db",
            "message": "Connection Timeout",
            "error_code": "504"
        })
        
    return pd.DataFrame(data)

def test_get_top_errors(sample_df):
    analyzer = AnomalyAnalyzer()
    top = analyzer.get_top_errors(sample_df)
    
    # Normal error has 20, Connection Timeout has 10
    assert len(top) == 2
    assert top.iloc[0]['message'] == "Normal error"
    assert top.iloc[0]['count'] == 20
    assert top.iloc[1]['message'] == "Connection Timeout"
    assert top.iloc[1]['count'] == 10

def test_detect_spikes(sample_df):
    # Base rate is ~1 per minute. 10 per min is a 10x spike.
    analyzer = AnomalyAnalyzer(spike_threshold_multiplier=3.0)
    spikes = analyzer.detect_spikes(sample_df, window_minutes=1)
    
    assert len(spikes) >= 1
    # Check if our injected spike is detected
    spike = [s for s in spikes if s['error_count'] >= 10][0]
    assert spike['error_count'] == 10
    assert spike['severity'] == "CRITICAL"
