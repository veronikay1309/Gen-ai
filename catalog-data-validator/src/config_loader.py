import yaml
from typing import List, Dict, Any
from pydantic import BaseModel, Field
from src.rules import ValidationRule
from src.rules.completeness import CompletenessRule
from src.rules.format import RegexFormatRule, NumericRangeRule
from src.rules.duplicates import DuplicatesRule
from src.rules.encoding import EncodingRule

class RuleConfig(BaseModel):
    type: str
    name: str
    severity: str = "WARNING"
    params: Dict[str, Any] = Field(default_factory=dict)

class ConfigSchema(BaseModel):
    rules: List[RuleConfig]

RULE_CLASS_MAP = {
    "completeness": CompletenessRule,
    "regex_format": RegexFormatRule,
    "numeric_range": NumericRangeRule,
    "duplicates": DuplicatesRule,
    "encoding": EncodingRule,
}

def load_config(config_path: str) -> List[ValidationRule]:
    """
    Loads YAML config, validates the structure using Pydantic, 
    and returns instantiated ValidationRule objects.
    """
    with open(config_path, "r") as f:
        raw_config = yaml.safe_load(f)

    if not raw_config or "rules" not in raw_config:
        raise ValueError(f"Configuration file {config_path} is empty or missing a 'rules' section.")

    # Validate with Pydantic
    config_data = ConfigSchema.model_validate(raw_config)

    rules = []
    for rc in config_data.rules:
        rule_type = rc.type.lower().strip()
        if rule_type not in RULE_CLASS_MAP:
            raise ValueError(f"Unknown rule type '{rc.type}' in rule '{rc.name}'. Available types are: {list(RULE_CLASS_MAP.keys())}")
        
        rule_class = RULE_CLASS_MAP[rule_type]
        rule_instance = rule_class(name=rc.name, severity=rc.severity, params=rc.params)
        rules.append(rule_instance)

    return rules
