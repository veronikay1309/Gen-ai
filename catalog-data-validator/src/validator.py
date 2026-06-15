import os
import argparse
import pandas as pd
from typing import List, Dict, Any
from src.config_loader import load_config
from src.reporters.json_report import generate_json_report
from src.reporters.html_report import generate_html_report

class CatalogValidator:
    """
    Core engine that validates a catalog dataset using configured validation rules.
    """
    def __init__(self, rules_path: str):
        self.rules = load_config(rules_path)

    def load_data(self, file_path: str) -> pd.DataFrame:
        """
        Loads the catalog dataset from CSV or JSON.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Input file not found at: {file_path}")

        _, ext = os.path.splitext(file_path.lower())
        if ext == ".csv":
            # Set keep_default_na=False to avoid interpreting empty spaces as NaN automatically,
            # or handle it carefully. Actually, standard pandas NA behavior is good,
            # but we read empty strings as empty strings.
            return pd.read_csv(file_path)
        elif ext == ".json":
            return pd.read_json(file_path)
        else:
            raise ValueError(f"Unsupported file format: {ext}. Only CSV and JSON are supported.")

    def validate(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Runs all rules on the DataFrame and returns a comprehensive validation report.
        """
        all_defects = []
        total_records = len(df)

        for rule in self.rules:
            try:
                rule_defects = rule.validate(df)
                all_defects.extend(rule_defects)
            except Exception as e:
                # Catch failures in individual rules to prevent crashing the whole pipeline
                all_defects.append({
                    "row_index": "SYSTEM",
                    "column": "ALL",
                    "rule": rule.name,
                    "value": None,
                    "severity": "CRITICAL",
                    "message": f"Execution of rule '{rule.name}' failed: {str(e)}"
                })

        # Calculate metrics
        total_defects = len(all_defects)
        unique_defective_rows = len(set(d["row_index"] for d in all_defects if d["row_index"] not in ["SYSTEM", "ALL", "CONFIG"]))
        defect_rate = (unique_defective_rows / total_records) if total_records > 0 else 0.0

        # Severity breakdown
        severity_counts = {"CRITICAL": 0, "WARNING": 0, "INFO": 0}
        for d in all_defects:
            sev = d["severity"].upper()
            if sev in severity_counts:
                severity_counts[sev] += 1
            else:
                severity_counts[sev] = severity_counts.get(sev, 0) + 1

        # Defect breakdown by rule & column
        rule_counts = {}
        column_counts = {}
        for d in all_defects:
            rule_counts[d["rule"]] = rule_counts.get(d["rule"], 0) + 1
            column_counts[d["column"]] = column_counts.get(d["column"], 0) + 1

        report = {
            "summary": {
                "total_records": total_records,
                "total_defects": total_defects,
                "defective_records": unique_defective_rows,
                "defect_rate": defect_rate,
                "severity_breakdown": severity_counts,
                "rule_breakdown": rule_counts,
                "column_breakdown": column_counts
            },
            "defects": all_defects
        }
        return report

def main():
    parser = argparse.ArgumentParser(description="Catalog Data Validator - Automated Data Quality Engine")
    parser.add_argument("--input", required=True, help="Path to input catalog CSV/JSON file")
    parser.add_argument("--rules", required=True, help="Path to YAML rules configuration file")
    parser.add_argument("--output-dir", default="reports", help="Directory where validation reports will be saved")
    args = parser.parse_args()

    try:
        print(f"🔍 Loading validator rules from {args.rules}...")
        validator = CatalogValidator(args.rules)

        print(f"📦 Loading catalog dataset from {args.input}...")
        df = validator.load_data(args.input)

        print(f"⚡ Running {len(validator.rules)} validation rules against {len(df)} records...")
        report = validator.validate(df)

        # Ensure output directory exists
        os.makedirs(args.output_dir, exist_ok=True)

        # Save reports
        json_report_path = os.path.join(args.output_dir, "report.json")
        html_report_path = os.path.join(args.output_dir, "report.html")

        print(f"💾 Saving reports to {args.output_dir}/...")
        generate_json_report(report, json_report_path)
        generate_html_report(report, html_report_path)

        # Print quick summary
        summary = report["summary"]
        print("\n=================== VALIDATION SUMMARY ===================")
        print(f"✅ Total Records Validated:  {summary['total_records']:,}")
        print(f"⚠️  Total Defects Detected:  {summary['total_defects']:,}")
        print(f"🚨 Defective Records Count: {summary['defective_records']:,} ({summary['defect_rate']*100:.2f}%)")
        print("\nSeverity Breakdown:")
        for sev, count in summary["severity_breakdown"].items():
            print(f"  - {sev}: {count}")
        print("==========================================================")
        print(f"HTML dashboard generated: file://{os.path.abspath(html_report_path)}")

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        exit(1)

if __name__ == "__main__":
    main()
