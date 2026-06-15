import pytest
import pandas as pd
from datetime import datetime, timedelta, timezone
from src.sla_calculator import SLACalculator
import json

@pytest.fixture
def temp_policies(tmp_path):
    policy_file = tmp_path / "policies.json"
    policy_file.write_text(json.dumps({
        "policies": {
            "SEV1": {"limit_hours": 1},
            "SEV2": {"limit_hours": 4}
        },
        "at_risk_threshold": 0.8
    }))
    return str(policy_file)

def test_sla_breach_calculation(temp_policies):
    calculator = SLACalculator(temp_policies)
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    
    # 1. Breached closed ticket (SEV1, closed after 2 hours)
    # 2. Safe open ticket (SEV2, open for 1 hour)
    # 3. At-risk open ticket (SEV1, open for 0.9 hours)
    
    df = pd.DataFrame([
        {"ticket_id": "T-1", "severity": "SEV1", "status": "CLOSED", "created_at": now - timedelta(hours=2), "resolved_at": now},
        {"ticket_id": "T-2", "severity": "SEV2", "status": "OPEN", "created_at": now - timedelta(hours=1), "resolved_at": pd.NaT},
        {"ticket_id": "T-3", "severity": "SEV1", "status": "IN_PROGRESS", "created_at": now - timedelta(hours=0.9), "resolved_at": pd.NaT}
    ])
    
    result = calculator.calculate(df)
    
    assert bool(result.iloc[0]['is_breached']) is True
    assert bool(result.iloc[0]['is_at_risk']) is False
    
    assert bool(result.iloc[1]['is_breached']) is False
    assert bool(result.iloc[1]['is_at_risk']) is False
    
    assert bool(result.iloc[2]['is_breached']) is False
    assert bool(result.iloc[2]['is_at_risk']) is True
    
def test_get_summary_metrics(temp_policies):
    calculator = SLACalculator(temp_policies)
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    
    df = pd.DataFrame([
        {"ticket_id": "T-1", "severity": "SEV1", "status": "CLOSED", "created_at": now - timedelta(hours=2), "resolved_at": now}, # Breach
        {"ticket_id": "T-2", "severity": "SEV2", "status": "OPEN", "created_at": now - timedelta(hours=1), "resolved_at": pd.NaT}  # Open
    ])
    
    result = calculator.calculate(df)
    metrics = calculator.get_summary_metrics(result)
    
    assert metrics['total_tickets'] == 2
    assert metrics['open_tickets'] == 1
    assert metrics['closed_tickets'] == 1
    assert metrics['breached_count'] == 1
    assert metrics['breach_rate'] == 50.0
