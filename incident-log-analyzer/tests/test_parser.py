import pytest
from src.parser import LogParser
import tempfile
import os

@pytest.fixture
def log_parser():
    return LogParser()

def test_parse_valid_lines(log_parser):
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp:
        tmp.write("[2026-06-15 10:15:30] [ERROR] [checkout-api] - Payment failed (Code: 500)\n")
        tmp.write("[2026-06-15 10:15:31] [INFO] [auth-service] - User logged in\n") # No code
        filepath = tmp.name

    df = log_parser.parse_file(filepath)
    os.remove(filepath)

    assert len(df) == 2
    assert df.iloc[0]['severity'] == 'ERROR'
    assert df.iloc[0]['service'] == 'checkout-api'
    assert df.iloc[0]['error_code'] == '500'
    
    assert df.iloc[1]['severity'] == 'INFO'
    assert df.iloc[1]['error_code'] == 'None' # Filled None

def test_parse_invalid_lines(log_parser):
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp:
        tmp.write("Just some random text\n")
        tmp.write("Exception in thread main java.lang.NullPointerException\n")
        tmp.write("[2026-06-15 10:15:30] [ERROR] [checkout-api] - Payment failed (Code: 500)\n")
        filepath = tmp.name

    df = log_parser.parse_file(filepath)
    os.remove(filepath)

    # Should ignore first two, parse the third
    assert len(df) == 1
    assert df.iloc[0]['service'] == 'checkout-api'
