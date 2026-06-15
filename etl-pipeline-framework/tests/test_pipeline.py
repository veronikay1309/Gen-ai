import os
import pytest
import pandas as pd
from src.pipeline import run_pipeline, build_extractor, build_transformers, build_loader
from src.metrics import PipelineMetrics
from src.dead_letter import DeadLetterQueue
from src.retry import with_retry


# ── Retry decorator ───────────────────────────────────────────────────────────

def test_retry_succeeds_on_first_attempt():
    call_count = {"n": 0}

    @with_retry(max_attempts=3, backoff_factor=0)
    def always_succeeds():
        call_count["n"] += 1
        return "ok"

    result = always_succeeds()
    assert result == "ok"
    assert call_count["n"] == 1


def test_retry_retries_on_failure():
    call_count = {"n": 0}

    @with_retry(max_attempts=3, backoff_factor=0)
    def fails_twice_then_succeeds():
        call_count["n"] += 1
        if call_count["n"] < 3:
            raise ValueError("temporary failure")
        return "success"

    result = fails_twice_then_succeeds()
    assert result == "success"
    assert call_count["n"] == 3


def test_retry_raises_after_max_attempts():
    @with_retry(max_attempts=2, backoff_factor=0)
    def always_fails():
        raise RuntimeError("permanent error")

    with pytest.raises(RuntimeError, match="permanent error"):
        always_fails()


# ── Dead Letter Queue ─────────────────────────────────────────────────────────

def test_dead_letter_add_and_flush(tmp_path):
    dlq = DeadLetterQueue(output_dir=str(tmp_path))
    dlq.add({"id": "1", "title": "Bad record"}, "encoding error", "cleaner")
    dlq.add({"id": "2", "title": "Another bad"}, "null key", "loader")

    assert dlq.count() == 2
    flushed = dlq.flush()
    assert flushed == 2
    assert dlq.count() == 0

    files = os.listdir(str(tmp_path))
    assert len(files) == 1
    assert files[0].startswith("failed_")
    assert files[0].endswith(".jsonl")


def test_dead_letter_empty_flush(tmp_path):
    dlq = DeadLetterQueue(output_dir=str(tmp_path))
    count = dlq.flush()
    assert count == 0


# ── Metrics ───────────────────────────────────────────────────────────────────

def test_metrics_calculation():
    m = PipelineMetrics(pipeline_name="test-pipeline")
    m.records_extracted = 1000
    m.records_after_transform = 950
    m.records_loaded = 900
    m.records_failed = 50
    m.finish()

    assert m.success_rate == 90.0
    assert m.duration_seconds >= 0
    assert m.records_per_second >= 0


# ── Full Pipeline Integration ─────────────────────────────────────────────────

@pytest.fixture
def full_pipeline_config(tmp_path):
    # Create sample CSV source
    df = pd.DataFrame([
        {"prod_id": "PROD-1", "prod_title": "  Widget A  ", "price": 10.0,
         "category": "Electronics", "brand": "SONY", "stock": 5, "asin": "B000000001"},
        {"prod_id": "PROD-2", "prod_title": "  Gadget B  ", "price": 20.0,
         "category": "BOOKS", "brand": "Apple", "stock": 3, "asin": "B000000002"},
        {"prod_id": "PROD-1", "prod_title": "Duplicate", "price": 10.0,
         "category": "Electronics", "brand": "Sony", "stock": 5, "asin": "B000000003"},
    ])
    csv_path = str(tmp_path / "raw.csv")
    df.to_csv(csv_path, index=False)

    db_path = str(tmp_path / "output" / "catalog.db")

    config_content = f"""
pipeline:
  name: test-pipeline
  source:
    type: csv
    path: {csv_path}
  transformers:
    - type: cleaner
      params:
        strip_whitespace: true
        lowercase_columns: [category, brand]
        drop_nulls_in: [prod_id]
    - type: deduplicator
      params:
        key_columns: [prod_id]
    - type: schema_mapper
      params:
        rename:
          prod_id: id
          prod_title: title
        keep_columns: [id, title, price, category, brand, stock, asin]
  destination:
    type: sqlite
    path: {db_path}
    table: products
    if_exists: replace

retry:
  max_attempts: 1
  backoff_factor: 0

dead_letter:
  enabled: true
  path: {str(tmp_path / "dead_letter")}
"""
    config_path = str(tmp_path / "config.yaml")
    with open(config_path, "w") as f:
        f.write(config_content)
    return config_path, db_path


def test_full_pipeline_run(full_pipeline_config):
    config_path, db_path = full_pipeline_config
    run_pipeline(config_path)

    # Verify output DB was created
    assert os.path.exists(db_path)

    # Verify records loaded
    import sqlite3
    conn = sqlite3.connect(db_path)
    cursor = conn.execute("SELECT COUNT(*) FROM products")
    count = cursor.fetchone()[0]
    conn.close()

    # 3 records input → 1 duplicate removed → 2 unique records loaded
    assert count == 2
