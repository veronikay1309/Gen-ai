import pandas as pd
import pytest
from src.transformers.cleaner import DataCleaner
from src.transformers.deduplicator import Deduplicator
from src.transformers.schema_mapper import SchemaMapper


# ── DataCleaner ───────────────────────────────────────────────────────────────

def test_cleaner_strips_whitespace():
    df = pd.DataFrame([{"id": "1", "title": "  Hello World  ", "category": "  Electronics  "}])
    cleaner = DataCleaner(strip_whitespace=True)
    result = cleaner.transform(df)
    assert result.loc[0, "title"] == "Hello World"
    assert result.loc[0, "category"] == "Electronics"


def test_cleaner_lowercase_columns():
    df = pd.DataFrame([{"id": "1", "category": "Electronics", "brand": "SONY"}])
    cleaner = DataCleaner(lowercase_columns=["category", "brand"])
    result = cleaner.transform(df)
    assert result.loc[0, "category"] == "electronics"
    assert result.loc[0, "brand"] == "sony"


def test_cleaner_drops_nulls():
    df = pd.DataFrame([
        {"id": "1", "title": "Product A", "price": 10.0},
        {"id": "2", "title": None, "price": 20.0},  # Should be dropped
    ])
    cleaner = DataCleaner(drop_nulls_in=["title"])
    result = cleaner.transform(df)
    assert len(result) == 1
    assert result.iloc[0]["id"] == "1"


# ── Deduplicator ──────────────────────────────────────────────────────────────

def test_deduplicator_removes_exact_duplicates():
    df = pd.DataFrame([
        {"id": "PROD-1", "title": "A"},
        {"id": "PROD-2", "title": "B"},
        {"id": "PROD-1", "title": "A duplicate"},  # Duplicate id
    ])
    dedup = Deduplicator(key_columns=["id"])
    result = dedup.transform(df)
    assert len(result) == 2
    assert list(result["id"]) == ["PROD-1", "PROD-2"]


def test_deduplicator_missing_key_column():
    df = pd.DataFrame([{"id": "1", "title": "A"}])
    dedup = Deduplicator(key_columns=["nonexistent"])
    result = dedup.transform(df)
    # Should return DataFrame unchanged
    assert len(result) == 1


# ── SchemaMapper ──────────────────────────────────────────────────────────────

def test_schema_mapper_renames_columns():
    df = pd.DataFrame([{"prod_id": "1", "prod_title": "A", "price": 10.0}])
    mapper = SchemaMapper(rename={"prod_id": "id", "prod_title": "title"})
    result = mapper.transform(df)
    assert "id" in result.columns
    assert "title" in result.columns
    assert "prod_id" not in result.columns


def test_schema_mapper_keeps_columns():
    df = pd.DataFrame([{"id": "1", "title": "A", "price": 10.0, "extra": "drop_me"}])
    mapper = SchemaMapper(keep_columns=["id", "title"])
    result = mapper.transform(df)
    assert list(result.columns) == ["id", "title"]
    assert "extra" not in result.columns
    assert "price" not in result.columns


def test_schema_mapper_skips_missing_keeps():
    df = pd.DataFrame([{"id": "1", "title": "A"}])
    mapper = SchemaMapper(keep_columns=["id", "title", "nonexistent"])
    result = mapper.transform(df)
    # Should keep only existing columns without raising
    assert list(result.columns) == ["id", "title"]
