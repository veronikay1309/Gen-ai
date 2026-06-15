import os
import csv
import random

def generate_legacy_data(output_path: str, count: int = 1000):
    """
    Generates legacy product data with old column names and formats.
    Some records will deliberately have missing data to trigger validation failures.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    depts = ["Elec", "App", "H&K", "Books", "Toys"]
    brands = ["Sony", "Nike", "KitchenAid", "Penguin", "Lego"]
    
    rows = []
    
    for i in range(count):
        # Valid record base
        item_sku = f"LEGACY-{10000 + i}"
        product_name = f"Product Name {i}"
        brand_name = random.choice(brands)
        short_desc = "Good product"
        dept = random.choice(depts)
        base_price = str(round(random.uniform(5.0, 150.0), 2))
        stock_count = random.randint(0, 100)
        
        # Inject invalid data to test validation (approx 5% failure rate)
        rand = random.random()
        if rand < 0.02:
            base_price = "-10.0"  # Negative price (fails validation)
        elif rand < 0.04:
            product_name = ""  # Empty title (fails validation)
        elif rand < 0.05:
            base_price = "invalid_price" # String price (fails mapping cast)

        rows.append({
            "item_sku": item_sku,
            "product_name": product_name,
            "brand_name": brand_name,
            "short_desc": short_desc,
            "dept": dept,
            "base_price": base_price,
            "stock_count": stock_count
        })

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["item_sku", "product_name", "brand_name", "short_desc", "dept", "base_price", "stock_count"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"✅ Generated {len(rows)} legacy records → {output_path}")

if __name__ == "__main__":
    generate_legacy_data("sample_data/legacy_products.csv", 1000)
