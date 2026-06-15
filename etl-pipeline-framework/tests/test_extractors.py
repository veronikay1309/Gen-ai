import os
import tempfile
import pandas as pd
import pytest
from src.extractors.csv_extractor import CSVExtractor


@pytest.fixture
def sample_csv(tmp_path):
    df = pd.DataFrame([
        {"id": "1", "title": "Product A", "price": 10.0},
        {"id": "2", "title": "Product B", "price": 20.0},
    ])
    path = str(tmp_path / "test.csv")
    df.to_csv(path, index=False)
    return path


def test_csv_extractor_basic(sample_csv):
    extractor = CSVExtractor(path=sample_csv)
    df = extractor.extract()
    assert len(df) == 2
    assert list(df.columns) == ["id", "title", "price"]


def test_csv_extractor_column_selection(sample_csv):
    extractor = CSVExtractor(path=sample_csv, columns=["id", "title"])
    df = extractor.extract()
    assert list(df.columns) == ["id", "title"]
    assert "price" not in df.columns


def test_csv_extractor_missing_column(sample_csv):
    extractor = CSVExtractor(path=sample_csv, columns=["id", "nonexistent"])
    with pytest.raises(ValueError, match="not found"):
        extractor.extract()


def test_csv_extractor_file_not_found():
    extractor = CSVExtractor(path="/nonexistent/path/file.csv")
    with pytest.raises(FileNotFoundError):
        extractor.extract()
