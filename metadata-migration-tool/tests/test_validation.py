import pytest
from src.schema_validator import SchemaValidator

def test_valid_record():
    validator = SchemaValidator()
    record = {
        "sku": "SKU-123",
        "title": "Valid Product",
        "price": 10.50,
        "inventory_level": 100,
        "currency": "USD",
        "status": "ACTIVE",
        "full_description": "A very good product",
        "category": "Electronics"
    }
    is_valid, err = validator.validate_record(record)
    assert is_valid is True
    assert err is None

def test_invalid_negative_price():
    validator = SchemaValidator()
    record = {
        "sku": "SKU-123",
        "title": "Valid Product",
        "price": -5.00,  # Invalid
        "inventory_level": 100,
        "currency": "USD",
        "status": "ACTIVE",
        "full_description": "A very good product",
        "category": "Electronics"
    }
    is_valid, err = validator.validate_record(record)
    assert is_valid is False
    assert "price" in err

def test_missing_required_field():
    validator = SchemaValidator()
    record = {
        "sku": "SKU-123"
        # missing everything else
    }
    is_valid, err = validator.validate_record(record)
    assert is_valid is False
    assert "title" in err
    assert "price" in err
