import os
import csv
import random
from faker import Faker

def generate_raw_products(output_path: str, count: int = 5000):
    """
    Generates a realistic raw product CSV with intentional messiness:
    - Extra whitespace in strings
    - Mixed casing in category/brand
    - Duplicate IDs
    - Missing prices
    - Encoding artifacts in titles
    """
    fake = Faker()
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    categories = ["Electronics", "ELECTRONICS", "electronics", "Apparel", "Home & Kitchen", "Books", "Beauty", "Sports"]
    brands = ["Sony", "SONY", "Nike", "Apple", "APPLE", "Samsung", "Philips"]

    rows = []
    generated_ids = []

    def make_asin():
        return "B" + "".join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", k=9))

    for i in range(count):
        prod_id = f"PROD-{10000 + i}"
        title = "  " + fake.catch_phrase() + "  "   # Leading/trailing whitespace
        price = round(random.uniform(5.0, 499.99), 2)
        category = random.choice(categories)
        brand = random.choice(brands)
        stock = random.randint(0, 500)
        asin = make_asin()

        # Inject anomalies ~7% of the time
        if random.random() < 0.07:
            anomaly = random.choice(["missing_price", "duplicate_id", "whitespace_brand", "encoding"])
            if anomaly == "missing_price":
                price = ""
            elif anomaly == "duplicate_id" and generated_ids:
                prod_id = random.choice(generated_ids)
            elif anomaly == "whitespace_brand":
                brand = "   Samsung   "
            elif anomaly == "encoding":
                title = title + " Special Edition (encoding artifact)"

        generated_ids.append(prod_id)
        rows.append({
            "prod_id": prod_id,
            "prod_title": title,
            "price": price,
            "category": category,
            "brand": brand,
            "stock": stock,
            "asin": asin,
        })

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["prod_id", "prod_title", "price", "category", "brand", "stock", "asin"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"✅ Generated {len(rows)} raw product records → {output_path}")

if __name__ == "__main__":
    generate_raw_products("sample_data/raw_products.csv", 5000)
