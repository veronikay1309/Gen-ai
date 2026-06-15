import os
import argparse
import logging
import yaml
import pandas as pd
from typing import Any, Dict

from src.extractors.csv_extractor import CSVExtractor
from src.extractors.api_extractor import APIExtractor
from src.transformers.cleaner import DataCleaner
from src.transformers.deduplicator import Deduplicator
from src.transformers.schema_mapper import SchemaMapper
from src.loaders.sqlite_loader import SQLiteLoader
from src.loaders.csv_loader import CSVLoader
from src.dead_letter import DeadLetterQueue
from src.metrics import PipelineMetrics
from src.retry import with_retry

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s"
)
logger = logging.getLogger(__name__)


def load_config(config_path: str) -> Dict[str, Any]:
    """Loads and returns the YAML pipeline configuration."""
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def build_extractor(source_cfg: Dict):
    """Factory: instantiates the correct extractor based on config type."""
    source_type = source_cfg.get("type", "csv").lower()
    if source_type == "csv":
        return CSVExtractor(
            path=source_cfg["path"],
            encoding=source_cfg.get("encoding", "utf-8"),
            columns=source_cfg.get("columns"),
        )
    elif source_type == "api":
        return APIExtractor(
            url=source_cfg["url"],
            headers=source_cfg.get("headers"),
            params=source_cfg.get("params"),
            page_size=source_cfg.get("page_size", 100),
            max_pages=source_cfg.get("max_pages", 10),
            data_key=source_cfg.get("data_key"),
        )
    else:
        raise ValueError(f"Unsupported source type: '{source_type}'. Use 'csv' or 'api'.")


def build_transformers(transformer_cfgs: list):
    """Factory: builds a list of transformer instances from config."""
    transformers = []
    for cfg in transformer_cfgs:
        t_type = cfg.get("type", "").lower()
        params = cfg.get("params", {})
        if t_type == "cleaner":
            transformers.append(DataCleaner(
                strip_whitespace=params.get("strip_whitespace", True),
                lowercase_columns=params.get("lowercase_columns", []),
                drop_nulls_in=params.get("drop_nulls_in", []),
            ))
        elif t_type == "deduplicator":
            transformers.append(Deduplicator(key_columns=params.get("key_columns", [])))
        elif t_type == "schema_mapper":
            transformers.append(SchemaMapper(
                rename=params.get("rename", {}),
                keep_columns=params.get("keep_columns"),
            ))
        else:
            logger.warning(f"Unknown transformer type '{t_type}' — skipping.")
    return transformers


def build_loader(dest_cfg: Dict):
    """Factory: instantiates the correct loader based on config type."""
    dest_type = dest_cfg.get("type", "sqlite").lower()
    if dest_type == "sqlite":
        os.makedirs(os.path.dirname(dest_cfg.get("path", "output/db.sqlite")), exist_ok=True)
        return SQLiteLoader(
            db_path=dest_cfg["path"],
            table=dest_cfg.get("table", "records"),
            if_exists=dest_cfg.get("if_exists", "replace"),
        )
    elif dest_type == "csv":
        return CSVLoader(output_path=dest_cfg["path"])
    else:
        raise ValueError(f"Unsupported destination type: '{dest_type}'. Use 'sqlite' or 'csv'.")


def run_pipeline(config_path: str):
    """
    Main pipeline orchestrator.
    Loads config → extract → transform → load → metrics → dead-letter flush.
    """
    config = load_config(config_path)
    pipeline_cfg = config.get("pipeline", {})
    pipeline_name = pipeline_cfg.get("name", "unnamed-pipeline")

    retry_cfg = config.get("retry", {})
    max_attempts = retry_cfg.get("max_attempts", 3)
    backoff_factor = retry_cfg.get("backoff_factor", 2)

    dlq_cfg = config.get("dead_letter", {})
    dlq = DeadLetterQueue(output_dir=dlq_cfg.get("path", "dead_letter")) if dlq_cfg.get("enabled", True) else None

    metrics = PipelineMetrics(pipeline_name=pipeline_name)

    logger.info(f"🚀 Starting pipeline: '{pipeline_name}'")

    # ── EXTRACT ──────────────────────────────────────────────────────────────
    extractor = build_extractor(config["pipeline"]["source"])

    @with_retry(max_attempts=max_attempts, backoff_factor=backoff_factor)
    def extract():
        return extractor.extract()

    try:
        df = extract()
    except Exception as e:
        logger.error(f"❌ Extraction failed after {max_attempts} attempts: {e}")
        if dlq:
            dlq.add({"source": config["pipeline"]["source"].get("path", "unknown")}, str(e), "extractor")
            dlq.flush()
        metrics.finish()
        metrics.print_summary()
        return

    metrics.records_extracted = len(df)
    logger.info(f"✅ Extracted {metrics.records_extracted:,} records.")

    # ── TRANSFORM ─────────────────────────────────────────────────────────────
    transformers = build_transformers(config["pipeline"].get("transformers", []))
    for transformer in transformers:
        try:
            df = transformer.transform(df)
        except Exception as e:
            stage_name = type(transformer).__name__
            logger.error(f"❌ Transformer '{stage_name}' failed: {e}")
            if dlq:
                dlq.add_dataframe(df, str(e), stage_name)

    metrics.records_after_transform = len(df)
    logger.info(f"✅ {metrics.records_after_transform:,} records after transformations.")

    # ── LOAD ──────────────────────────────────────────────────────────────────
    loader = build_loader(config["pipeline"]["destination"])

    @with_retry(max_attempts=max_attempts, backoff_factor=backoff_factor)
    def load():
        return loader.load(df)

    try:
        loaded = load()
        metrics.records_loaded = loaded
        logger.info(f"✅ Loaded {metrics.records_loaded:,} records to destination.")
    except Exception as e:
        logger.error(f"❌ Loader failed after {max_attempts} attempts: {e}")
        metrics.records_failed = len(df)
        if dlq:
            dlq.add_dataframe(df, str(e), "loader")

    # ── DEAD LETTER FLUSH ─────────────────────────────────────────────────────
    if dlq and dlq.count() > 0:
        failed_count = dlq.flush()
        metrics.records_failed += failed_count

    # ── METRICS ───────────────────────────────────────────────────────────────
    metrics.finish()
    metrics.print_summary()


def main():
    parser = argparse.ArgumentParser(description="ETL Pipeline Framework")
    parser.add_argument("--config", required=True, help="Path to pipeline YAML config file")
    args = parser.parse_args()
    run_pipeline(args.config)


if __name__ == "__main__":
    main()
