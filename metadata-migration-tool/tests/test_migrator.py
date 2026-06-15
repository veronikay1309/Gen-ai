import os
import pytest
import pandas as pd
from src.migrator import MetadataMigrator

@pytest.fixture
def migration_setup(tmp_path):
    # 1. Create dummy legacy CSV
    legacy_csv = tmp_path / "legacy.csv"
    pd.DataFrame([
        {"item_sku": "LEGACY-123", "product_name": "Valid", "base_price": "10.0", "stock_count": 5, "dept": "Elec", "brand_name": "Sony", "short_desc": "Good"},
        {"item_sku": "LEGACY-456", "product_name": "Invalid Price", "base_price": "-5.0", "stock_count": 5, "dept": "App", "brand_name": "Nike", "short_desc": "Bad"}
    ]).to_csv(legacy_csv, index=False)

    # 2. Create config
    config_yaml = tmp_path / "config.yaml"
    config_yaml.write_text("""
migration:
  name: "Test Migration"
  primary_key: "item_sku"
  rules:
    direct:
      item_sku: sku
      product_name: title
      stock_count: inventory_level
    defaults:
      currency: "USD"
      status: "ACTIVE"
    computed:
      - target: price
        type: cast
        source: base_price
        to_type: float
      - target: full_description
        type: concat
        sources: [brand_name, product_name]
        separator: " "
      - target: category
        type: map_values
        source: dept
        mapping: {"Elec": "Electronics", "App": "Apparel"}
        default: "Other"
""")
    
    output_csv = tmp_path / "output.csv"
    return str(config_yaml), str(legacy_csv), str(output_csv)

def test_migrator_execution(migration_setup):
    config_path, source_csv, output_csv = migration_setup
    
    migrator = MetadataMigrator(config_path)
    migrator.run(source_csv, output_csv, dry_run=False)
    
    assert os.path.exists(output_csv), f"Output CSV not created. Validation errors: {migrator.auditor.errors}"
    df_out = pd.read_csv(output_csv)
    
    # Only 1 record should pass validation
    assert len(df_out) == 1
    assert df_out.iloc[0]["sku"] == "LEGACY-123"
    assert df_out.iloc[0]["price"] == 10.0
    
    # Check rollbacks
    assert len(migrator.auditor.rollback_records) == 1
    assert migrator.auditor.stats["validation_failed"] == 1
