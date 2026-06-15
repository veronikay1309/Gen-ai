import pandas as pd
import pytest
from src.rules.completeness import CompletenessRule
from src.rules.format import RegexFormatRule, NumericRangeRule
from src.rules.duplicates import DuplicatesRule
from src.rules.encoding import EncodingRule

def test_completeness_rule():
    df = pd.DataFrame([
        {"id": "1", "title": "Product A", "category": "Electronics"},
        {"id": "2", "title": "", "category": "Books"},          # Empty string
        {"id": "3", "title": "Product B", "category": "  "},    # Whitespace string
        {"id": "4", "title": "Product C", "category": None},    # None
    ])
    
    rule = CompletenessRule("check_complete", severity="WARNING", params={"columns": ["title", "category"]})
    defects = rule.validate(df)
    
    # defects expected on row index 2 (title is empty), 3 (category is whitespace), 4 (category is None)
    assert len(defects) == 3
    
    # Check details
    defect_rows = [d["row_index"] for d in defects]
    assert "2" in defect_rows
    assert "3" in defect_rows
    assert "4" in defect_rows

def test_completeness_missing_column():
    df = pd.DataFrame([{"id": "1", "title": "Product A"}])
    rule = CompletenessRule("check_complete", params={"columns": ["non_existent"]})
    defects = rule.validate(df)
    
    # Expected CRITICAL defect since the column is missing entirely
    assert len(defects) == 1
    assert defects[0]["row_index"] == "ALL"
    assert defects[0]["severity"] == "CRITICAL"

def test_regex_format_rule():
    df = pd.DataFrame([
        {"id": "1", "asin": "B01N123ABC"}, # Valid
        {"id": "2", "asin": "A01N123ABC"}, # Invalid (starts with A)
        {"id": "3", "asin": "B01N"},       # Invalid (too short)
        {"id": "4", "asin": None},         # Ignored (nulls handled by completeness)
    ])
    
    rule = RegexFormatRule("check_asin", severity="CRITICAL", params={"patterns": {"asin": "^B[A-Z0-9]{9}$"}})
    defects = rule.validate(df)
    
    assert len(defects) == 2
    defect_rows = [d["row_index"] for d in defects]
    assert "2" in defect_rows
    assert "3" in defect_rows
    assert defects[0]["severity"] == "CRITICAL"

def test_numeric_range_rule():
    df = pd.DataFrame([
        {"id": "1", "price": 10.0, "stock": 5},    # Valid
        {"id": "2", "price": -5.0, "stock": 10},   # Price out of range (< 0.01)
        {"id": "3", "price": 20.0, "stock": -2},   # Stock out of range (< 0)
        {"id": "4", "price": "invalid", "stock": 5} # Price not a number
    ])
    
    rule = NumericRangeRule("check_range", params={
        "ranges": {
            "price": {"min": 0.01, "max": 1000},
            "stock": {"min": 0}
        }
    })
    defects = rule.validate(df)
    
    assert len(defects) == 3
    
    defect_2 = [d for d in defects if d["row_index"] == "2"][0]
    assert "below minimum" in defect_2["message"]
    
    defect_3 = [d for d in defects if d["row_index"] == "3"][0]
    assert "below minimum" in defect_3["message"]
    
    defect_4 = [d for d in defects if d["row_index"] == "4"][0]
    assert "not a valid number" in defect_4["message"]
    assert defect_4["severity"] == "CRITICAL"

def test_duplicates_rule_exact():
    df = pd.DataFrame([
        {"id": "PROD-1", "asin": "B01", "title": "A"},
        {"id": "PROD-2", "asin": "B01", "title": "B"}, # Duplicate ASIN
        {"id": "PROD-1", "asin": "B02", "title": "C"}, # Duplicate ID
        {"id": "PROD-3", "asin": "B03", "title": "D"}  # Unique
    ])
    
    rule = DuplicatesRule("check_dups", params={"key_columns": ["id", "asin"]})
    defects = rule.validate(df)
    
    # We expect 4 exact duplicate defects (2 for id PROD-1, 2 for asin B01)
    assert len(defects) == 4

def test_duplicates_rule_fuzzy():
    df = pd.DataFrame([
        {"id": "1", "title": "Amazon Echo Dot 4th Gen Smart Speaker"},
        {"id": "2", "title": "Amazon Echo Dot 4th Gen Smart Speaker (Black)"}, # Fuzzy similar
        {"id": "3", "title": "Nike Men's Running Shoes Size 10"}
    ])
    
    rule = DuplicatesRule("check_dups", params={"fuzzy_column": "title", "fuzzy_threshold": 0.85})
    defects = rule.validate(df)
    
    # We expect 2 defects (one pointing to row 1, one pointing to row 2)
    assert len(defects) == 2
    assert "Fuzzy duplicate title detected" in defects[0]["message"]

def test_encoding_rule():
    df = pd.DataFrame([
        {"id": "1", "title": "Clean Title"},
        {"id": "2", "title": "Title with \ufffd character"}, # Unicode replacement char
        {"id": "3", "title": "Title with â€ mojibake"},    # Mojibake marker
        {"id": "4", "title": "Title with Café (non-ascii)"} # Non-ASCII
    ])
    
    # Test replacement and mojibake detection
    rule_moji = EncodingRule("check_encoding", params={"columns": ["title"], "detect_mojibake": True})
    defects_moji = rule_moji.validate(df)
    
    assert len(defects_moji) == 2 # row 2 and 3
    
    # Test ascii only validation
    rule_ascii = EncodingRule("check_ascii", params={"columns": ["title"], "ascii_only": True})
    defects_ascii = rule_ascii.validate(df)
    
    assert len(defects_ascii) == 3 # row 2, 3, and 4 (Café is non-ascii)
