import datetime
from jinja2 import Template
from typing import Dict, Any

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Catalog Data Quality Report</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-color: #0b0f19;
            --panel-bg: rgba(23, 28, 41, 0.6);
            --border-color: rgba(255, 255, 255, 0.08);
            --text-primary: #f3f4f6;
            --text-secondary: #9ca3af;
            --accent-blue: #3b82f6;
            --accent-green: #10b981;
            --accent-yellow: #f59e0b;
            --accent-red: #ef4444;
            --accent-purple: #8b5cf6;
            --glass-shine: linear-gradient(135deg, rgba(255, 255, 255, 0.05), rgba(255, 255, 255, 0.01));
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            font-family: 'Outfit', sans-serif;
            background-color: var(--bg-color);
            color: var(--text-primary);
            padding: 2rem;
            min-height: 100vh;
            background-image: 
                radial-gradient(circle at 10% 20%, rgba(59, 130, 246, 0.05) 0%, transparent 40%),
                radial-gradient(circle at 90% 80%, rgba(139, 92, 246, 0.05) 0%, transparent 40%);
            background-attachment: fixed;
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
        }

        header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 2rem;
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 1.5rem;
        }

        .header-title h1 {
            font-size: 2.2rem;
            font-weight: 700;
            background: linear-gradient(to right, #60a5fa, #a78bfa);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0.25rem;
        }

        .header-title p {
            color: var(--text-secondary);
            font-size: 0.95rem;
        }

        .timestamp {
            text-align: right;
            color: var(--text-secondary);
            font-size: 0.9rem;
        }

        .quality-score-badge {
            background: linear-gradient(135deg, #10b981 0%, #059669 100%);
            padding: 0.5rem 1rem;
            border-radius: 9999px;
            font-weight: 600;
            font-size: 0.9rem;
            color: white;
            box-shadow: 0 4px 12px rgba(16, 185, 129, 0.2);
            display: inline-block;
            margin-top: 0.5rem;
        }
        
        .quality-score-badge.warning {
            background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
            box-shadow: 0 4px 12px rgba(245, 158, 11, 0.2);
        }

        .quality-score-badge.danger {
            background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
            box-shadow: 0 4px 12px rgba(239, 68, 68, 0.2);
        }

        /* Metrics Cards */
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }

        .card {
            background: var(--panel-bg);
            border: 1px solid var(--border-color);
            border-radius: 16px;
            padding: 1.5rem;
            position: relative;
            overflow: hidden;
            backdrop-filter: blur(12px);
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }

        .card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: var(--glass-shine);
            pointer-events: none;
        }

        .card:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(0, 0, 0, 0.2);
        }

        .card-label {
            color: var(--text-secondary);
            font-size: 0.85rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 0.5rem;
            display: block;
        }

        .card-value {
            font-size: 1.8rem;
            font-weight: 700;
        }

        .card.critical { border-left: 4px solid var(--accent-red); }
        .card.warning { border-left: 4px solid var(--accent-yellow); }
        .card.info { border-left: 4px solid var(--accent-blue); }
        .card.success { border-left: 4px solid var(--accent-green); }

        .critical .card-value { color: var(--accent-red); }
        .warning .card-value { color: var(--accent-yellow); }
        .info .card-value { color: var(--accent-blue); }
        .success .card-value { color: var(--accent-green); }

        /* Dashboard Content Layout */
        .dashboard-body {
            display: grid;
            grid-template-columns: 1fr 2fr;
            gap: 2rem;
            margin-bottom: 2rem;
        }

        @media (max-width: 1024px) {
            .dashboard-body {
                grid-template-columns: 1fr;
            }
        }

        .panel {
            background: var(--panel-bg);
            border: 1px solid var(--border-color);
            border-radius: 16px;
            padding: 1.5rem;
            backdrop-filter: blur(12px);
        }

        .panel-title {
            font-size: 1.2rem;
            font-weight: 600;
            margin-bottom: 1.25rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 0.75rem;
        }

        /* Distribution Lists / Bar charts */
        .dist-item {
            margin-bottom: 1rem;
        }

        .dist-label-row {
            display: flex;
            justify-content: space-between;
            font-size: 0.9rem;
            margin-bottom: 0.25rem;
        }

        .dist-label {
            color: var(--text-primary);
            font-weight: 500;
        }

        .dist-count {
            color: var(--text-secondary);
        }

        .dist-bar-bg {
            height: 8px;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 4px;
            overflow: hidden;
        }

        .dist-bar-fill {
            height: 100%;
            background: linear-gradient(to right, var(--accent-blue), var(--accent-purple));
            border-radius: 4px;
            transition: width 0.3s ease;
        }

        /* Defects Section */
        .defects-section {
            margin-top: 2rem;
        }

        .controls-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1.25rem;
            flex-wrap: wrap;
            gap: 1rem;
        }

        .filter-buttons {
            display: flex;
            gap: 0.5rem;
        }

        .filter-btn {
            background: rgba(255, 255, 255, 0.04);
            border: 1px solid var(--border-color);
            color: var(--text-secondary);
            padding: 0.4rem 1rem;
            border-radius: 8px;
            font-family: inherit;
            font-size: 0.85rem;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s;
        }

        .filter-btn:hover {
            background: rgba(255, 255, 255, 0.08);
            color: var(--text-primary);
        }

        .filter-btn.active {
            background: var(--accent-blue);
            color: white;
            border-color: var(--accent-blue);
        }

        .search-box {
            background: rgba(255, 255, 255, 0.04);
            border: 1px solid var(--border-color);
            color: var(--text-primary);
            padding: 0.5rem 1rem;
            border-radius: 8px;
            font-family: inherit;
            font-size: 0.85rem;
            outline: none;
            min-width: 250px;
        }

        .search-box:focus {
            border-color: var(--accent-blue);
            box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2);
        }

        /* Table design */
        .table-container {
            overflow-x: auto;
            border-radius: 12px;
            border: 1px solid var(--border-color);
        }

        table {
            width: 100%;
            border-collapse: collapse;
            text-align: left;
            font-size: 0.9rem;
        }

        th {
            background: rgba(15, 23, 42, 0.5);
            padding: 1rem;
            font-weight: 600;
            color: var(--text-secondary);
            border-bottom: 1px solid var(--border-color);
        }

        td {
            padding: 1rem;
            border-bottom: 1px solid var(--border-color);
            color: var(--text-primary);
        }

        tr:last-child td {
            border-bottom: none;
        }

        tr:hover td {
            background: rgba(255, 255, 255, 0.02);
        }

        .badge {
            display: inline-block;
            padding: 0.25rem 0.6rem;
            border-radius: 6px;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
        }

        .badge.critical {
            background: rgba(239, 68, 68, 0.15);
            color: #fca5a5;
            border: 1px solid rgba(239, 68, 68, 0.3);
        }

        .badge.warning {
            background: rgba(245, 158, 11, 0.15);
            color: #fde047;
            border: 1px solid rgba(245, 158, 11, 0.3);
        }

        .badge.info {
            background: rgba(59, 130, 246, 0.15);
            color: #93c5fd;
            border: 1px solid rgba(59, 130, 246, 0.3);
        }

        .val-text {
            font-family: monospace;
            background: rgba(0, 0, 0, 0.2);
            padding: 0.15rem 0.3rem;
            border-radius: 4px;
            font-size: 0.85rem;
            max-width: 180px;
            display: inline-block;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
            vertical-align: middle;
        }

        .empty-state {
            padding: 3rem;
            text-align: center;
            color: var(--text-secondary);
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div class="header-title">
                <h1>Catalog Data Quality Report</h1>
                <p>Data validation metrics and structural analysis dashboard</p>
            </div>
            <div class="timestamp">
                <p>Report Generated: <strong>{{ timestamp }}</strong></p>
                <div class="quality-score-badge {{ 'danger' if quality_score < 80 else ('warning' if quality_score < 95 else '') }}">
                    Quality Score: {{ "%.2f"|format(quality_score) }}%
                </div>
            </div>
        </header>

        <!-- Metric Summary -->
        <div class="metrics-grid">
            <div class="card success">
                <span class="card-label">Total Validated</span>
                <span class="card-value">{{ summary.total_records | number_format }}</span>
            </div>
            <div class="card {{ 'critical' if summary.defective_records > 0 else 'success' }}">
                <span class="card-label">Defective Records</span>
                <span class="card-value">{{ summary.defective_records | number_format }}</span>
            </div>
            <div class="card info">
                <span class="card-label">Defect Rate</span>
                <span class="card-value">{{ "%.2f"|format(summary.defect_rate * 100) }}%</span>
            </div>
            <div class="card critical">
                <span class="card-label">Critical Defects</span>
                <span class="card-value">{{ summary.severity_breakdown.get('CRITICAL', 0) | number_format }}</span>
            </div>
            <div class="card warning">
                <span class="card-label">Warning Defects</span>
                <span class="card-value">{{ summary.severity_breakdown.get('WARNING', 0) | number_format }}</span>
            </div>
            <div class="card info">
                <span class="card-label">Info Defects</span>
                <span class="card-value">{{ summary.severity_breakdown.get('INFO', 0) | number_format }}</span>
            </div>
        </div>

        <div class="dashboard-body">
            <!-- Left Side: Breakdowns -->
            <div class="panel">
                <h2 class="panel-title">Defect Distribution by Rule</h2>
                {% if summary.rule_breakdown %}
                    {% for rule, count in summary.rule_breakdown.items() %}
                        {% set percentage = (count / summary.total_defects * 100) if summary.total_defects > 0 else 0 %}
                        <div class="dist-item">
                            <div class="dist-label-row">
                                <span class="dist-label">{{ rule }}</span>
                                <span class="dist-count">{{ count }} ({{ "%.1f"|format(percentage) }}%)</span>
                            </div>
                            <div class="dist-bar-bg">
                                <div class="dist-bar-fill" style="width: {{ percentage }}%;"></div>
                            </div>
                        </div>
                    {% endfor %}
                {% else %}
                    <p class="empty-state">No defects to analyze.</p>
                {% endif %}
                
                <h2 class="panel-title" style="margin-top: 2rem;">Defects by Column</h2>
                {% if summary.column_breakdown %}
                    {% for col, count in summary.column_breakdown.items() %}
                        {% set percentage = (count / summary.total_defects * 100) if summary.total_defects > 0 else 0 %}
                        <div class="dist-item">
                            <div class="dist-label-row">
                                <span class="dist-label">{{ col }}</span>
                                <span class="dist-count">{{ count }} ({{ "%.1f"|format(percentage) }}%)</span>
                            </div>
                            <div class="dist-bar-bg">
                                <div class="dist-bar-fill" style="width: {{ percentage }}%; background: linear-gradient(to right, var(--accent-yellow), var(--accent-red));"></div>
                            </div>
                        </div>
                    {% endfor %}
                {% else %}
                    <p class="empty-state">No columns affected.</p>
                {% endif %}
            </div>

            <!-- Right Side: Defects List -->
            <div class="panel">
                <h2 class="panel-title">Defect Register</h2>
                
                <div class="controls-row">
                    <div class="filter-buttons">
                        <button class="filter-btn active" onclick="filterSeverity('ALL')">All</button>
                        <button class="filter-btn" onclick="filterSeverity('CRITICAL')">Critical</button>
                        <button class="filter-btn" onclick="filterSeverity('WARNING')">Warning</button>
                        <button class="filter-btn" onclick="filterSeverity('INFO')">Info</button>
                    </div>
                    <input type="text" id="search" class="search-box" placeholder="Search defects..." onkeyup="searchTable()">
                </div>

                <div class="table-container">
                    <table id="defects-table">
                        <thead>
                            <tr>
                                <th>ID / Row</th>
                                <th>Column</th>
                                <th>Rule</th>
                                <th>Value</th>
                                <th>Severity</th>
                                <th>Details</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for d in display_defects %}
                            <tr class="defect-row" data-severity="{{ d.severity }}">
                                <td>{{ d.row_index }}</td>
                                <td style="font-weight: 500;">{{ d.column }}</td>
                                <td style="color: var(--text-secondary);">{{ d.rule }}</td>
                                <td>
                                    {% if d.value is not none and d.value != '' %}
                                        <span class="val-text" title="{{ d.value | e }}">{{ d.value }}</span>
                                    {% else %}
                                        <span style="color: var(--text-secondary); font-style: italic;">null</span>
                                    {% endif %}
                                </td>
                                <td><span class="badge {{ d.severity | lower }}">{{ d.severity }}</span></td>
                                <td style="font-size: 0.85rem; max-width: 300px;">{{ d.message }}</td>
                            </tr>
                            {% endfor %}
                            {% if not display_defects %}
                            <tr>
                                <td colspan="6" class="empty-state">🎉 Excellent! Zero defects found in the dataset.</td>
                            </tr>
                            {% endif %}
                        </tbody>
                    </table>
                </div>
                
                {% if summary.total_defects > display_defects|length %}
                <p style="margin-top: 1rem; text-align: center; color: var(--text-secondary); font-size: 0.85rem;">
                    * Showing the first {{ display_defects|length }} of {{ summary.total_defects }} total defects to optimize performance.
                </p>
                {% endif %}
            </div>
        </div>
    </div>

    <script>
        function filterSeverity(severity) {
            // Update active state of buttons
            const buttons = document.querySelectorAll('.filter-btn');
            buttons.forEach(btn => btn.classList.remove('active'));
            
            event.target.classList.add('active');

            const rows = document.querySelectorAll('.defect-row');
            rows.forEach(row => {
                const rowSev = row.getAttribute('data-severity');
                if (severity === 'ALL' || rowSev === severity) {
                    row.style.display = '';
                } else {
                    row.style.display = 'none';
                }
            });
            searchTable(true); // Maintain search filter if active
        }

        function searchTable(isFiltering) {
            const query = document.getElementById('search').value.toLowerCase();
            const activeBtn = document.querySelector('.filter-btn.active');
            const activeSeverity = activeBtn ? activeBtn.innerText.toUpperCase() : 'ALL';
            
            const rows = document.querySelectorAll('.defect-row');
            rows.forEach(row => {
                const rowSev = row.getAttribute('data-severity');
                const matchesSeverity = (activeSeverity === 'ALL' || activeSeverity === 'ALL' || rowSev === activeSeverity);
                
                if (!matchesSeverity) {
                    row.style.display = 'none';
                    return;
                }

                const text = row.innerText.toLowerCase();
                if (text.includes(query)) {
                    row.style.display = '';
                } else {
                    row.style.display = 'none';
                }
            });
        }
    </script>
</body>
</html>
"""

def number_format_filter(value):
    return f"{value:,}"

def generate_html_report(report: Dict[str, Any], output_path: str):
    """
    Renders the quality report to HTML using Jinja2 templates.
    """
    summary = report["summary"]
    defects = report["defects"]

    # Calculate Quality Score: Percentage of valid records
    total = summary["total_records"]
    defective = summary["defective_records"]
    quality_score = ((total - defective) / total * 100) if total > 0 else 100.0

    # Limit table items to 1000 items to avoid freezing browsers
    display_defects = defects[:1000]

    from jinja2 import Environment
    env = Environment()
    env.filters['number_format'] = number_format_filter
    template = env.from_string(HTML_TEMPLATE)

    html_content = template.render(
        summary=summary,
        display_defects=display_defects,
        quality_score=quality_score,
        timestamp=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    )

    with open(output_path, "w") as f:
        f.write(html_content)
