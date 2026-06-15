import pytest
from src.mapping_engine import MappingEngine

def test_direct_mapping():
    rules = {
        "direct": {
            "old_id": "new_id",
            "old_title": "title"
        }
    }
    engine = MappingEngine(rules)
    legacy = {"old_id": "123", "old_title": "Test", "ignored_col": "foo"}
    migrated = engine.transform(legacy)
    
    assert migrated == {"new_id": "123", "title": "Test"}

def test_default_values():
    rules = {
        "defaults": {
            "currency": "USD",
            "status": "ACTIVE"
        }
    }
    engine = MappingEngine(rules)
    legacy = {"some_col": "val"}
    migrated = engine.transform(legacy)
    
    assert migrated["currency"] == "USD"
    assert migrated["status"] == "ACTIVE"

def test_computed_concat():
    rules = {
        "computed": [
            {
                "target": "full_desc",
                "type": "concat",
                "sources": ["brand", "name"],
                "separator": " - "
            }
        ]
    }
    engine = MappingEngine(rules)
    legacy = {"brand": "Apple", "name": "iPhone"}
    migrated = engine.transform(legacy)
    
    assert migrated["full_desc"] == "Apple - iPhone"

def test_computed_cast():
    rules = {
        "computed": [
            {
                "target": "price",
                "type": "cast",
                "source": "old_price",
                "to_type": "float"
            }
        ]
    }
    engine = MappingEngine(rules)
    legacy = {"old_price": "19.99"}
    migrated = engine.transform(legacy)
    
    assert migrated["price"] == 19.99
    assert isinstance(migrated["price"], float)

def test_computed_map_values():
    rules = {
        "computed": [
            {
                "target": "category",
                "type": "map_values",
                "source": "dept",
                "mapping": {"Elec": "Electronics"},
                "default": "Other"
            }
        ]
    }
    engine = MappingEngine(rules)
    assert engine.transform({"dept": "Elec"})["category"] == "Electronics"
    assert engine.transform({"dept": "Unknown"})["category"] == "Other"
