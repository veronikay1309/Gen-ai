import json
from typing import Dict, Any

def generate_json_report(report: Dict[str, Any], output_path: str):
    """
    Saves the validation report metrics and defects list as a JSON file.
    """
    with open(output_path, "w") as f:
        json.dump(report, f, indent=4, default=str)
