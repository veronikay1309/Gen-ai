import os
import pytest
from src.ingestor import TicketIngestor
from src.sla_calculator import SLACalculator
from src.dashboard_generator import DashboardGenerator
from src.generate_sample_tickets import generate_tickets

@pytest.fixture
def integration_setup(tmp_path):
    csv_file = tmp_path / "tickets.csv"
    output_dir = tmp_path / "output"
    policies_file = tmp_path / "policies.json"
    
    # Generate 50 tickets
    generate_tickets(str(csv_file), count=50)
    
    import json
    policies_file.write_text(json.dumps({
        "policies": {
            "SEV1": {"limit_hours": 1},
            "SEV2": {"limit_hours": 4},
            "SEV3": {"limit_hours": 24},
            "SEV4": {"limit_hours": 168}
        },
        "at_risk_threshold": 0.8
    }))
    
    return str(csv_file), str(policies_file), str(output_dir)

def test_full_pipeline(integration_setup):
    csv_file, policies_file, output_dir = integration_setup
    
    ingestor = TicketIngestor(csv_file)
    df = ingestor.load_data()
    assert len(df) == 50
    
    calculator = SLACalculator(policies_file)
    df_processed = calculator.calculate(df)
    metrics = calculator.get_summary_metrics(df_processed)
    
    assert metrics['total_tickets'] == 50
    
    dashboard = DashboardGenerator(templates_dir=os.path.join(output_dir, "templates"))
    dashboard.generate(df_processed, metrics, output_dir)
    
    assert os.path.exists(os.path.join(output_dir, "sla_metrics.json"))
    assert os.path.exists(os.path.join(output_dir, "sla_dashboard.html"))
