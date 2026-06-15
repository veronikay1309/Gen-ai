import argparse
import logging
import os
from src.parser import LogParser
from src.analyzer import AnomalyAnalyzer
from src.reporter import ReportGenerator

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description="Incident Log Analyzer")
    parser.add_argument("--log-file", required=True, help="Path to raw log file")
    parser.add_argument("--output-dir", default="output", help="Directory for reports")
    parser.add_argument("--spike-threshold", type=float, default=3.0, help="Multiplier for anomaly detection")
    
    args = parser.parse_args()

    if not os.path.exists(args.log_file):
        logger.error(f"Log file not found: {args.log_file}")
        return

    # 1. Parse
    log_parser = LogParser()
    df = log_parser.parse_file(args.log_file)
    
    if df.empty:
        logger.warning("No records parsed. Exiting.")
        return

    # 2. Analyze
    analyzer = AnomalyAnalyzer(spike_threshold_multiplier=args.spike_threshold)
    stats = analyzer.generate_summary_stats(df)
    incidents = analyzer.detect_spikes(df, window_minutes=5)
    top_errors = analyzer.get_top_errors(df, limit=10)

    # 3. Report
    reporter = ReportGenerator()
    reporter.generate(stats, incidents, top_errors, args.output_dir)
    
    logger.info("✅ Analysis Complete.")

if __name__ == "__main__":
    main()
