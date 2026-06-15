import os
import random
from datetime import datetime, timedelta

def generate_logs(output_path: str, count: int = 10000):
    """Generates realistic server logs with a built-in anomaly (spike in errors)."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    services = ["checkout-api", "payment-gateway", "inventory-service", "auth-service", "user-profile"]
    severities = ["INFO", "INFO", "INFO", "INFO", "WARN", "ERROR"]
    
    # Common error messages
    errors = {
        "checkout-api": [("Timeout connecting to DB", "504"), ("Null pointer exception", "500")],
        "payment-gateway": [("Card declined", "402"), ("Stripe API rate limit", "429")],
        "inventory-service": [("Item out of stock", "404"), ("Sync failed", "500")],
        "auth-service": [("Invalid token", "401"), ("Connection reset by peer", "503")],
        "user-profile": [("Record not found", "404")]
    }

    start_time = datetime.now() - timedelta(hours=24)
    logs = []

    for i in range(count):
        # Time progression (steady traffic)
        current_time = start_time + timedelta(seconds=i * 2)

        # INJECT ANOMALY: Between record 5000 and 5500, massive spike in payment-gateway errors
        is_anomaly_window = 5000 <= i <= 5500
        
        if is_anomaly_window:
            service = "payment-gateway"
            severity = "ERROR" if random.random() < 0.9 else "FATAL" # 90% error rate in this window
            msg, code = "Payment Provider Timeout", "504"
        else:
            service = random.choice(services)
            severity = random.choice(severities)
            
            if severity in ["ERROR", "WARN"]:
                msg, code = random.choice(errors[service])
            else:
                msg = f"Processed request successfully for /api/v1/{service}"
                code = "200"

        # Format: [YYYY-MM-DD HH:MM:SS] [SEVERITY] [SERVICE_NAME] - Message (Code: X)
        log_line = f"[{current_time.strftime('%Y-%m-%d %H:%M:%S')}] [{severity}] [{service}] - {msg} (Code: {code})"
        logs.append(log_line)

        # Interleaved unparseable line to test robustness
        if i % 1000 == 0:
            logs.append("This is a random stacktrace line that shouldn't match the regex")

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(logs) + "\n")

    print(f"✅ Generated {len(logs)} log lines (including injected anomaly) at {output_path}")

if __name__ == "__main__":
    generate_logs("data/system.log", 10000)
