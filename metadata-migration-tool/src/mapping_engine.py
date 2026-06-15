from typing import Dict, Any, List
import logging
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

class MappingEngine:
    """
    Applies declarative YAML rules to transform a legacy record into the new schema.
    """
    def __init__(self, rules: Dict[str, Any]):
        self.rules = rules

    def transform(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transforms a single dictionary record based on the rules.
        """
        migrated = {}

        # 1. Direct Mappings
        direct_rules = self.rules.get("direct", {})
        for old_col, new_col in direct_rules.items():
            if old_col in record and pd.notna(record[old_col]):
                migrated[new_col] = record[old_col]

        # 2. Default Values
        default_rules = self.rules.get("defaults", {})
        for col, default_val in default_rules.items():
            if col not in migrated or pd.isna(migrated.get(col)):
                migrated[col] = default_val

        # 3. Computed Mappings
        computed_rules = self.rules.get("computed", [])
        for comp in computed_rules:
            target = comp.get("target")
            comp_type = comp.get("type")

            if comp_type == "concat":
                sources = comp.get("sources", [])
                sep = comp.get("separator", "")
                parts = [str(record.get(s, "")) for s in sources if pd.notna(record.get(s))]
                migrated[target] = sep.join(parts).strip(sep).strip()

            elif comp_type == "cast":
                source = comp.get("source")
                to_type = comp.get("to_type")
                val = record.get(source)
                if pd.notna(val):
                    try:
                        if to_type == "float":
                            migrated[target] = float(val)
                        elif to_type == "int":
                            migrated[target] = int(float(val))
                        elif to_type == "str":
                            migrated[target] = str(val)
                    except (ValueError, TypeError):
                        logger.warning(f"Failed to cast {val} to {to_type} for field {target}")
                        migrated[target] = val

            elif comp_type == "map_values":
                source = comp.get("source")
                mapping = comp.get("mapping", {})
                default_val = comp.get("default")
                val = record.get(source)
                migrated[target] = mapping.get(val, default_val)

        # Remove any NaN/None values from final migrated record (so Pydantic defaults/validators handle them)
        return {k: v for k, v in migrated.items() if pd.notna(v)}
