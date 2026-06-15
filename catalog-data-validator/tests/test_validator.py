import os
import tempfile
import pandas as pd
import pytest
from src.config_loader import load_config
from src.validator import CatalogValidator
from src.reporters.json_report import generate_json_report
from src.reporters.html_report import generate_html_report

@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir

@pytest.fixture
def sample_config_path(temp_dir):
    config_content = """
rules:
  - type: completeness
    name: req_fields
    severity: CRITICAL
    params:
      columns: [id, title]
  - type: numeric_range
    name: price_range
    severity: WARNING
    params:
      ranges:
        price:
          min: 0.1
    """
    path = os.path.join(temp_dir, "rules.yaml")
    with open(path, "w") as f:
        f.write(config_content)
    return path

@pytest.fixture
def sample_csv_path(temp_dir):
    df = pd.DataFrame([
        {"id": "PROD-1", "title": "Product 1", "price": 10.0}, # Valid
        {"id": "PROD-2", "title": "", "price": 15.0},          # Empty title (defect)
        {"id": "PROD-3", "title": "Product 3", "price": 0.0},  # Price too low (defect)
    ])
    path = os.path.join(temp_dir, "catalog.csv")
    df.to_csv(path, index=False)
    return path

def test_config_loader(sample_config_path):
    rules = load_config(sample_config_path)
    assert len(rules) == 2
    assert rules[0].name == "req_fields"
    assert rules[0].severity == "CRITICAL"
    assert rules[1].name == "price_range"
    assert rules[1].severity == "WARNING"

def test_config_loader_invalid_type(temp_dir):
    config_content = """
rules:
  - type: invalid_type_name
    name: test_rule
    """
    path = os.path.join(temp_dir, "bad_rules.yaml")
    with open(path, "w") as f:
        f.write(config_content)
    
    with pytest.raises(ValueError, match="Unknown rule type"):
        load_config(path)

def test_catalog_validator(sample_config_path, sample_csv_path):
    validator = CatalogValidator(sample_config_path)
    df = validator.load_data(sample_csv_path)
    report = validator.validate(df)
    
    # Check loaded data size
    assert len(df) == 3
    
    # Check summary metrics
    summary = report["summary"]
    assert summary["total_records"] == 3
    assert summary["total_defects"] == 2
    assert summary["defective_records"] == 2
    assert summary["defect_rate"] == (2 / 3)
    
    # Check breakdown
    assert summary["severity_breakdown"]["CRITICAL"] == 1
    assert summary["severity_breakdown"]["WARNING"] == 1
    
    # Check detailed defects
    defects = report["defects"]
    assert len(defects) == 2
    
    # Verify contents of defects
    defect_rows = [d["row_index"] for d in defects]
    assert "PROD-2" in defect_rows
    assert "PROD-3" in defect_rows

def test_report_generation(temp_dir, sample_config_path, sample_csv_path):
    validator = CatalogValidator(sample_config_path)
    df = validator.load_data(sample_csv_path)
    report = validator.validate(df)
    
    json_path = os.path.join(temp_dir, "report.json")
    html_path = os.path.join(temp_dir, "report.html")
    
    generate_json_report(report, json_path)
    generate_html_report(report, html_path)
    
    assert os.path.exists(json_path)
    assert os.path.exists(html_path)
    
    # Verify HTML contains title and some data
    with open(html_path, "r") as f:
        html_content = f.read()
        assert "Catalog Data Quality Report" in html_content
        assert "PROD-2" in html_content
