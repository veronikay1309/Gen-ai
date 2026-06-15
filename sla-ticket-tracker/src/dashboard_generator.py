import os
import json
from jinja2 import Environment, FileSystemLoader
import pandas as pd
import logging

logger = logging.getLogger(__name__)

class DashboardGenerator:
    """Generates the HTML dashboard and JSON metrics report."""
    
    def __init__(self, templates_dir: str = "templates"):
        self.templates_dir = templates_dir
        os.makedirs(self.templates_dir, exist_ok=True)
        self._create_template()
        self.env = Environment(loader=FileSystemLoader(self.templates_dir))

    def _create_template(self):
        """Creates the Jinja2 HTML template if missing."""
        template_path = os.path.join(self.templates_dir, "dashboard.html.j2")
        if not os.path.exists(template_path):
            html = """
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <title>Operational Metrics: SLA Tracker</title>
                <style>
                    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; margin: 40px; color: #333; background-color: #f4f6f8; }
                    .card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 20px; }
                    h1, h2 { color: #2c3e50; }
                    .stats { display: flex; gap: 20px; }
                    .stat-box { background: #ecf0f1; padding: 15px; border-radius: 6px; flex: 1; text-align: center; }
                    .stat-box.danger { background: #fee2e2; color: #991b1b; border: 1px solid #fca5a5; }
                    .stat-box.warning { background: #fef08a; color: #854d0e; border: 1px solid #fde047; }
                    table { width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 14px; }
                    th, td { padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }
                    th { background-color: #f8f9fa; }
                    tr:hover { background-color: #f1f5f9; }
                    .badge { padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; }
                    .SEV1 { background: #fca5a5; color: #991b1b; }
                    .SEV2 { background: #fdba74; color: #9a3412; }
                    .SEV3 { background: #fef08a; color: #854d0e; }
                </style>
            </head>
            <body>
                <h1>📊 SLA Health Dashboard</h1>
                
                <div class="stats">
                    <div class="stat-box">
                        <h3>Total Tickets</h3>
                        <h2>{{ metrics.total_tickets }}</h2>
                    </div>
                    <div class="stat-box danger">
                        <h3>SLA Breaches</h3>
                        <h2>{{ metrics.breached_count }} ({{ metrics.breach_rate }}%)</h2>
                    </div>
                    <div class="stat-box warning">
                        <h3>At-Risk (Open)</h3>
                        <h2>{{ metrics.at_risk_count }}</h2>
                    </div>
                </div>

                <div class="card">
                    <h2>⚠️ At-Risk Tickets (Requires Immediate Action)</h2>
                    {% if at_risk_tickets %}
                    <table>
                        <tr><th>Ticket ID</th><th>Severity</th><th>Status</th><th>Elapsed Hours</th><th>SLA Limit</th></tr>
                        {% for ticket in at_risk_tickets %}
                        <tr>
                            <td>{{ ticket.ticket_id }}</td>
                            <td><span class="badge {{ ticket.severity }}">{{ ticket.severity }}</span></td>
                            <td>{{ ticket.status }}</td>
                            <td>{{ "%.1f"|format(ticket.elapsed_hours) }}h</td>
                            <td>{{ ticket.sla_limit_hours }}h</td>
                        </tr>
                        {% endfor %}
                    </table>
                    {% else %}
                    <p>No tickets currently at risk. Great job! 🎉</p>
                    {% endif %}
                </div>

                <div class="card">
                    <h2>❌ Recent SLA Breaches</h2>
                    {% if breached_tickets %}
                    <table>
                        <tr><th>Ticket ID</th><th>Severity</th><th>Status</th><th>Elapsed Hours</th><th>SLA Limit</th></tr>
                        {% for ticket in breached_tickets %}
                        <tr>
                            <td>{{ ticket.ticket_id }}</td>
                            <td><span class="badge {{ ticket.severity }}">{{ ticket.severity }}</span></td>
                            <td>{{ ticket.status }}</td>
                            <td>{{ "%.1f"|format(ticket.elapsed_hours) }}h</td>
                            <td>{{ ticket.sla_limit_hours }}h</td>
                        </tr>
                        {% endfor %}
                    </table>
                    {% else %}
                    <p>No SLA breaches found.</p>
                    {% endif %}
                </div>
            </body>
            </html>
            """
            with open(template_path, 'w', encoding='utf-8') as f:
                f.write(html)

    def generate(self, df: pd.DataFrame, metrics: dict, output_dir: str):
        """Generates the reports."""
        os.makedirs(output_dir, exist_ok=True)
        
        # 1. JSON Report
        json_path = os.path.join(output_dir, "sla_metrics.json")
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(metrics, f, indent=4)
        logger.info(f"Saved JSON metrics to {json_path}")

        # 2. HTML Dashboard
        at_risk = df[df['is_at_risk']].sort_values('elapsed_hours', ascending=False).to_dict('records')
        breached = df[df['is_breached']].sort_values('elapsed_hours', ascending=False).head(10).to_dict('records')

        template = self.env.get_template("dashboard.html.j2")
        html = template.render(
            metrics=metrics,
            at_risk_tickets=at_risk,
            breached_tickets=breached
        )

        html_path = os.path.join(output_dir, "sla_dashboard.html")
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html)
        logger.info(f"Saved HTML dashboard to {html_path}")
