import argparse
import logging
import yaml
import pandas as pd
import os

from src.mapping_engine import MappingEngine
from src.schema_validator import SchemaValidator
from src.audit_logger import AuditLogger

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s"
)
logger = logging.getLogger(__name__)

class MetadataMigrator:
    def __init__(self, config_path: str):
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Config file not found: {config_path}")
            
        with open(config_path, "r") as f:
            self.config = yaml.safe_load(f).get("migration", {})
            
        self.mapper = MappingEngine(self.config.get("rules", {}))
        self.validator = SchemaValidator()
        self.auditor = AuditLogger()
        self.primary_key = self.config.get("primary_key", "id")

    def run(self, source_csv: str, output_csv: str, dry_run: bool = False):
        logger.info(f"🚀 Starting migration: '{self.config.get('name')}'")
        logger.info(f"Mode: {'DRY RUN' if dry_run else 'EXECUTE'}")

        # Load legacy data
        try:
            df_legacy = pd.read_csv(source_csv)
            logger.info(f"Loaded {len(df_legacy)} legacy records from {source_csv}")
        except Exception as e:
            logger.error(f"Failed to read source file: {e}")
            return

        migrated_records = []

        # Process record by record
        for _, row in df_legacy.iterrows():
            self.auditor.increment_processed()
            legacy_dict = row.to_dict()
            pk_val = legacy_dict.get(self.primary_key, "UNKNOWN")

            # 1. Transform
            migrated_dict = self.mapper.transform(legacy_dict)

            # 2. Validate against Target Schema
            is_valid, error_msg = self.validator.validate_record(migrated_dict)

            if is_valid:
                self.auditor.record_success(legacy_dict)
                migrated_records.append(migrated_dict)
            else:
                self.auditor.record_failure(str(pk_val), error_msg)

        # Generate Audit Report
        self.auditor.generate_report()

        if dry_run:
            logger.info("🛑 DRY RUN complete. No files were written.")
            return

        # Write Migrated Data
        if migrated_records:
            os.makedirs(os.path.dirname(output_csv), exist_ok=True)
            df_migrated = pd.DataFrame(migrated_records)
            
            # Ensure columns match schema definition order if possible
            schema_fields = list(self.validator.schema_class.model_fields.keys())
            cols = [c for c in schema_fields if c in df_migrated.columns]
            df_migrated = df_migrated[cols]
            
            df_migrated.to_csv(output_csv, index=False)
            logger.info(f"✅ Wrote {len(migrated_records)} migrated records to {output_csv}")
            
            # Generate Rollback File
            self.auditor.save_rollback(self.config.get("name", "migration"))
        else:
            logger.warning("No valid records to write.")

def main():
    parser = argparse.ArgumentParser(description="Metadata Migration Tool")
    parser.add_argument("--config", required=True, help="Path to migration rules YAML")
    parser.add_argument("--source", required=True, help="Path to legacy CSV")
    parser.add_argument("--output", required=True, help="Path to output migrated CSV")
    parser.add_argument("--dry-run", action="store_true", help="Run without writing files")
    
    args = parser.parse_args()
    
    migrator = MetadataMigrator(args.config)
    migrator.run(args.source, args.output, dry_run=args.dry_run)

if __name__ == "__main__":
    main()
