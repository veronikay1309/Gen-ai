import os
import random
import csv
from faker import Faker

def generate_mock_catalog(output_path: str, count: int = 10000):
    """
    Generates a mock e-commerce product catalog with realistic data
    and intentionally injected defects for validation testing.
    """
    fake = Faker()
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Categories list
    categories = ["Electronics", "Apparel", "Home & Kitchen", "Books", "Beauty", "Sports", "Toys", "Automotive"]

    # We will generate raw data
    data = []
    
    # Store generated IDs and ASINs to inject duplicate anomalies
    generated_ids = []
    generated_asins = []
    
    # Base ASIN generator
    def make_valid_asin():
        chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
        return "B" + "".join(random.choices(chars, k=9))

    print(f"Generating {count} mock product records...")

    for i in range(count):
        prod_id = f"PROD-{100000 + i}"
        title = fake.catch_phrase()
        desc = fake.paragraph(nb_sentences=2)
        price = round(random.uniform(5.99, 499.99), 2)
        asin = make_valid_asin()
        category = random.choice(categories)
        stock = random.randint(0, 1000)

        # Intentionally inject anomalies in roughly 5% of records
        anomaly_type = None
        if random.random() < 0.06:
            anomaly_type = random.choice([
                "missing_title", "missing_price", "missing_category", 
                "negative_price", "extreme_price", "negative_stock",
                "bad_asin_format", "mojibake_desc", "unicode_replacement",
                "exact_duplicate_id", "exact_duplicate_asin", "fuzzy_duplicate_title"
            ])

        if anomaly_type == "missing_title":
            title = ""
        elif anomaly_type == "missing_price":
            price = None
        elif anomaly_type == "missing_category":
            category = ""
        elif anomaly_type == "negative_price":
            price = round(random.uniform(-50.0, -1.0), 2)
        elif anomaly_type == "extreme_price":
            price = 999999.00
        elif anomaly_type == "negative_stock":
            stock = random.randint(-100, -1)
        elif anomaly_type == "bad_asin_format":
            asin = "A1B2C3D4" # Too short, starts with A
        elif anomaly_type == "mojibake_desc":
            desc = desc + " with bad Ã©nconding â€” details."
        elif anomaly_type == "unicode_replacement":
            title = title + " \ufffd Item"
        elif anomaly_type == "exact_duplicate_id" and generated_ids:
            prod_id = random.choice(generated_ids)
        elif anomaly_type == "exact_duplicate_asin" and generated_asins:
            asin = random.choice(generated_asins)
        elif anomaly_type == "fuzzy_duplicate_title" and len(data) > 0:
            # Copy a previous record's title and modify slightly
            prev_record = random.choice(data)
            title = prev_record["title"] + " (New Model)"
            # Keep other attributes unique
            category = prev_record["category"]

        record = {
            "id": prod_id,
            "title": title,
            "description": desc,
            "price": price,
            "asin": asin,
            "category": category,
            "stock": stock
        }

        data.append(record)
        
        # Keep track for duplicates
        if record["id"]:
            generated_ids.append(record["id"])
        if record["asin"] and len(record["asin"]) == 10:
            generated_asins.append(record["asin"])

    # Write to CSV
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "title", "description", "price", "asin", "category", "stock"])
        writer.writeheader()
        for row in data:
            writer.writerow(row)

    print(f"Successfully generated {len(data)} records in {output_path}")

if __name__ == "__main__":
    generate_mock_catalog("sample_data/products_10k.csv", 10000)
