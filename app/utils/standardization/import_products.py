import sys
from pathlib import Path
import json
import os
import glob

# Add the project root directory to the Python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

try:
    from app import db, create_app
    from app.models.models import UnifiedProduct
    from app.utils.standardization.standardize import (
        process_file,
        convert_to_unified_product
    )
except ImportError:
    print("Error importing app modules. Make sure you're running this script from the project root.")
    sys.exit(1)

def import_products():
    """Import products from JSON files"""
    app = create_app()
    with app.app_context():
        # Define paths to Citilink category JSON files
        citilink_data_dir = "app/utils/Citi_parser/data"
        citilink_files = glob.glob(os.path.join(citilink_data_dir, "*", "Товары.json"))
        
        if not citilink_files:
            print(f"Error: No category files found in {citilink_data_dir}")
            return
        
        # DNS file as before
        dns_file = "app/utils/DNS_parsing/product_data.json"
        if not os.path.exists(dns_file):
            print(f"Error: File not found: {dns_file}")
            return
        
        # Process Citilink files
        citilink_products = []
        for file in citilink_files:
            print(f"Processing Citilink data from {file}...")
            products = process_file(file, "citilink")
            print(f"Found {len(products)} products in {file}")
            citilink_products.extend(products)
        print(f"Total Citilink products found: {len(citilink_products)}")
        
        # Process DNS file
        print("Processing DNS data...")
        dns_products = process_file(dns_file, "dns")
        print(f"Found {len(dns_products)} products from DNS")
        
        # Convert to UnifiedProduct instances
        unified_products = []
        for product in citilink_products + dns_products:
            unified_product = convert_to_unified_product(product)
            unified_products.append(unified_product)
        
        # Save to database with duplicate check by product_url
        print("Saving to database (checking for duplicates by product_url)...")
        added_count = 0
        skipped_count = 0
        for product in unified_products:
            existing = UnifiedProduct.query.filter_by(product_url=product.product_url).first()
            if not existing:
                db.session.add(product)
                added_count += 1
            else:
                skipped_count += 1
        
        try:
            db.session.commit()
            print(f"Successfully added {added_count} new products to database. Skipped {skipped_count} duplicates.")
        except Exception as e:
            db.session.rollback()
            print(f"Error saving to database: {e}")
            print(str(e))

if __name__ == "__main__":
    import_products() 