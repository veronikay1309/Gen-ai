import os
import random
import pandas as pd
from datetime import datetime, timedelta, timezone

def generate_tickets(output_path: str, count: int = 5000):
    """Generates a dataset of support tickets with some deliberately breached SLAs."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    severities = ["SEV1", "SEV2", "SEV3", "SEV4"]
    weights = [0.05, 0.15, 0.40, 0.40]  # SEV1 is rare, SEV4 is common
    
    # SLA Limits mapping (must match configs/sla_policies.json)
    sla_limits = {"SEV1": 1, "SEV2": 4, "SEV3": 24, "SEV4": 168}

    data = []
    
    for i in range(count):
        ticket_id = f"TKT-{100000 + i}"
        severity = random.choices(severities, weights=weights)[0]
        status = random.choice(["OPEN", "IN_PROGRESS", "CLOSED", "CLOSED", "CLOSED"])
        
        limit_hours = sla_limits[severity]
        
        # Decide if this ticket breached SLA (approx 10% chance)
        is_breach = random.random() < 0.10
        
        if is_breach:
            elapsed_hours = limit_hours + random.uniform(1.0, 10.0)
        else:
            # Most tickets are resolved quickly or open for a short time
            elapsed_hours = random.uniform(0.1, limit_hours * 0.9)
            
            # Inject some "At-Risk" tickets (open and >80% limit)
            if status != "CLOSED" and random.random() < 0.2:
                elapsed_hours = limit_hours * random.uniform(0.85, 0.98)

        created_at = now - timedelta(hours=elapsed_hours)
        
        if status == "CLOSED":
            resolved_at = now
        else:
            resolved_at = pd.NaT

        data.append({
            "ticket_id": ticket_id,
            "severity": severity,
            "status": status,
            "created_at": created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "resolved_at": resolved_at.strftime("%Y-%m-%d %H:%M:%S") if pd.notna(resolved_at) else ""
        })

    df = pd.DataFrame(data)
    df.to_csv(output_path, index=False)
    print(f"✅ Generated {len(df)} tickets at {output_path}")

if __name__ == "__main__":
    generate_tickets("data/tickets.csv", 5000)
