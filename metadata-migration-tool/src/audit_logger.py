import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class AuditLogger:
    """
    Handles logging of migration statistics, validation errors, and generates
    rollback files containing the original state of migrated records.
    """
    def __init__(self, output_dir: str = "rollbacks"):
        self.output_dir = output_dir
        self.stats = {
            "total_processed": 0,
            "successfully_migrated": 0,
            "validation_failed": 0
        }
        self.errors = []
        self.rollback_records = []
        os.makedirs(self.output_dir, exist_ok=True)

    def record_success(self, legacy_record: Dict[str, Any]):
        self.stats["successfully_migrated"] += 1
        self.rollback_records.append(legacy_record)

    def record_failure(self, primary_key: str, error_msg: str):
        self.stats["validation_failed"] += 1
        self.errors.append({"pk": primary_key, "error": error_msg})

    def increment_processed(self):
        self.stats["total_processed"] += 1

    def generate_report(self) -> str:
        report = []
        report.append("\n=================== MIGRATION AUDIT REPORT ===================")
        report.append(f"  Total Records Processed: {self.stats['total_processed']}")
        report.append(f"  Successfully Migrated:   {self.stats['successfully_migrated']}")
        report.append(f"  Validation Failures:     {self.stats['validation_failed']}")
        report.append("==============================================================")
        
        if self.errors:
            report.append("\nTop 5 Validation Failures:")
            for err in self.errors[:5]:
                report.append(f"  - Record [{err['pk']}]: {err['error']}")
            if len(self.errors) > 5:
                report.append(f"  ... and {len(self.errors) - 5} more.")
                
        report_str = "\n".join(report)
        logger.info(report_str)
        return report_str

    def save_rollback(self, migration_name: str) -> str:
        """Saves successfully migrated legacy records so the migration can be reverted."""
        if not self.rollback_records:
            return ""

        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        safe_name = migration_name.replace(" ", "_").lower()
        filename = f"rollback_{safe_name}_{timestamp}.jsonl"
        filepath = os.path.join(self.output_dir, filename)

        with open(filepath, "w") as f:
            for rec in self.rollback_records:
                # Handle NaN/inf for JSON serialization
                cleaned_rec = {k: (v if v == v else None) for k, v in rec.items()}
                f.write(json.dumps(cleaned_rec, default=str) + "\n")

        logger.info(f"💾 Rollback file generated: {filepath} ({len(self.rollback_records)} records)")
        return filepath
