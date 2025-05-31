import json
import sys
from pathlib import Path

# Add the project root directory to the Python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

from app.utils.standardization.standardize import (
    process_file, 
    standardize_characteristics
)

def test_standardization():
    """Test the standardization process without saving to the database"""
    # Example usage
    citilink_file = "app/utils/Citi_parser/Товары.json"
    dns_file = "app/utils/DNS_parsing/product_data.json"
    
    # Process files
    print("Processing Citilink data...")
    citilink_products = process_file(citilink_file, "citilink")
    print(f"Found {len(citilink_products)} products from Citilink")
    
    print("Processing DNS data...")
    dns_products = process_file(dns_file, "dns")
    print(f"Found {len(dns_products)} products from DNS")
    
    # Find matching products (same GPU model)
    print("\nLooking for matching products...")
    matches = []
    for c_product in citilink_products:
        c_chars = c_product.get("characteristics", {})
        c_gpu = c_chars.get("gpu_model", "")
        
        for d_product in dns_products:
            d_chars = d_product.get("characteristics", {})
            d_gpu = d_chars.get("gpu_model", "")
            
            # Simple matching logic - can be improved
            if c_gpu and d_gpu and c_gpu.lower() in d_gpu.lower() or d_gpu.lower() in c_gpu.lower():
                matches.append((c_product, d_product))
    
    print(f"Found {len(matches)} matching product pairs")
    
    # Display matching products and their standardized characteristics
    for i, (c_product, d_product) in enumerate(matches):
        print(f"\nMatch {i+1}:")
        print(f"Citilink: {c_product.get('product_name')}")
        print(f"DNS: {d_product.get('product_name')}")
        
        print("\nStandardized characteristics:")
        c_chars = c_product.get("characteristics", {})
        d_chars = d_product.get("characteristics", {})
        
        # Combine all keys from both products
        all_keys = set(c_chars.keys()) | set(d_chars.keys())
        
        for key in sorted(all_keys):
            c_value = c_chars.get(key, "N/A")
            d_value = d_chars.get(key, "N/A")
            print(f"{key:20}: Citilink: {c_value:20} | DNS: {d_value}")
    
    # Save standardized data to JSON for inspection
    with open("standardized_test.json", "w", encoding="utf-8") as f:
        json.dump(matches, f, ensure_ascii=False, indent=2)
    print("\nSaved standardized test data to standardized_test.json")

if __name__ == "__main__":
    test_standardization() 