import argparse
import logging
import os
from src.ingestor import TicketIngestor
from src.sla_calculator import SLACalculator
from src.dashboard_generator import DashboardGenerator

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description="SLA Ticket Tracker")
    parser.add_argument("--tickets-csv", required=True, help="Path to tickets CSV")
    parser.add_argument("--policies", required=True, help="Path to SLA policies JSON")
    parser.add_argument("--output-dir", default="output", help="Directory for reports")
    
    args = parser.parse_args()

    if not os.path.exists(args.tickets_csv):
        logger.error(f"Tickets file not found: {args.tickets_csv}")
        return

    # 1. Ingest Data
    ingestor = TicketIngestor(args.tickets_csv)
    df = ingestor.load_data()
    
    if df.empty:
        logger.warning("No data to process.")
        return

    # 2. Calculate SLAs
    calculator = SLACalculator(args.policies)
    df_processed = calculator.calculate(df)
    metrics = calculator.get_summary_metrics(df_processed)

    # 3. Generate Dashboards
    dashboard = DashboardGenerator()
    dashboard.generate(df_processed, metrics, args.output_dir)
    
    logger.info("✅ SLA processing complete.")

if __name__ == "__main__":
    main()
