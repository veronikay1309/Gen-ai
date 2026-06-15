import os
import json
from jinja2 import Environment, FileSystemLoader
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class ReportGenerator:
    """Generates JSON and HTML reports from analysis results."""
    def __init__(self, templates_dir: str = "templates"):
        self.templates_dir = templates_dir
        os.makedirs(self.templates_dir, exist_ok=True)
        self._create_default_template()
        self.env = Environment(loader=FileSystemLoader(self.templates_dir))

    def _create_default_template(self):
        """Creates the default HTML template if it doesn't exist."""
        template_path = os.path.join(self.templates_dir, 'report.html.j2')
        if not os.path.exists(template_path):
            html = """
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <title>Incident Log Analysis</title>
                <style>
                    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; margin: 40px; color: #333; background-color: #f9f9f9; }
                    .card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 20px; }
                    h1, h2 { color: #2c3e50; }
                    .stats { display: flex; gap: 20px; }
                    .stat-box { background: #ecf0f1; padding: 15px; border-radius: 6px; flex: 1; text-align: center; }
                    .stat-box.critical { background: #fee2e2; color: #991b1b; }
                    table { width: 100%; border-collapse: collapse; margin-top: 10px; }
                    th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
                    th { background-color: #f8f9fa; }
                    tr:hover { background-color: #f1f5f9; }
                    .badge { padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; }
                    .badge.HIGH { background: #fef08a; color: #854d0e; }
                    .badge.CRITICAL { background: #fca5a5; color: #991b1b; }
                </style>
            </head>
            <body>
                <h1>🚨 Incident Log Analysis Report</h1>
                
                <div class="stats">
                    <div class="stat-box">
                        <h3>Total Logs Analyzed</h3>
                        <h2>{{ stats.total_logs }}</h2>
                    </div>
                    <div class="stat-box critical">
                        <h3>Error Rate</h3>
                        <h2>{{ stats.error_rate_percent }}%</h2>
                    </div>
                    <div class="stat-box">
                        <h3>Total Errors</h3>
                        <h2>{{ stats.total_errors }}</h2>
                    </div>
                </div>

                <div class="card">
                    <h2>📈 Detected Anomalies (Error Spikes)</h2>
                    {% if incidents %}
                    <table>
                        <tr><th>Time Window</th><th>Error Count</th><th>Baseline Mean</th><th>Severity</th></tr>
                        {% for inc in incidents %}
                        <tr>
                            <td>{{ inc.window_start }}</td>
                            <td>{{ inc.error_count }}</td>
                            <td>{{ inc.baseline_mean }}</td>
                            <td><span class="badge {{ inc.severity }}">{{ inc.severity }}</span></td>
                        </tr>
                        {% endfor %}
                    </table>
                    {% else %}
                    <p>No anomalous error spikes detected. System looks healthy.</p>
                    {% endif %}
                </div>

                <div class="card">
                    <h2>🔥 Top Recurring Errors</h2>
                    <table>
                        <tr><th>Service</th><th>Message</th><th>HTTP/Error Code</th><th>Occurrences</th></tr>
                        {% for err in top_errors %}
                        <tr>
                            <td>{{ err.service }}</td>
                            <td>{{ err.message }}</td>
                            <td>{{ err.error_code }}</td>
                            <td>{{ err.count }}</td>
                        </tr>
                        {% endfor %}
                    </table>
                </div>
            </body>
            </html>
            """
            with open(template_path, 'w', encoding='utf-8') as f:
                f.write(html)

    def generate(self, stats: Dict[str, Any], incidents: list, top_errors_df, output_dir: str):
        """Generates the JSON and HTML reports."""
        os.makedirs(output_dir, exist_ok=True)
        
        top_errors_list = top_errors_df.to_dict('records') if not top_errors_df.empty else []

        # 1. JSON Report
        report_data = {
            "summary_stats": stats,
            "detected_anomalies": incidents,
            "top_recurring_errors": top_errors_list
        }
        
        json_path = os.path.join(output_dir, 'incident_report.json')
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=4)
        logger.info(f"JSON report saved to: {json_path}")

        # 2. HTML Report
        template = self.env.get_template('report.html.j2')
        html_content = template.render(
            stats=stats,
            incidents=incidents,
            top_errors=top_errors_list
        )
        
        html_path = os.path.join(output_dir, 'incident_report.html')
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        logger.info(f"HTML report saved to: {html_path}")
