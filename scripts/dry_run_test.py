#!/usr/bin/env python3
"""
Comprehensive Dry Run Test
Verifies Entity Building, ID Generation, and SHACL Validation logic.
"""

import sys
import os
import json

# Add scripts directory to path
sys.path.append(os.path.join(os.path.dirname(__file__)))

from id_generator import generate_product_id, generate_entity_id, normalize_gtin
from entity_builder import EntityBuilder
from shacl_validator import SHACLValidator

def run_test():
    dataset_uri = "https://data.wordlift.io/wl123"
    builder = EntityBuilder(dataset_uri)
    validator = SHACLValidator()

    print("--- 1. Testing ID Generation ---")
    gtin = "12345678901231"
    product_id = generate_product_id(dataset_uri, gtin)
    print(f"Product ID: {product_id}")

    org_id = generate_entity_id(dataset_uri, "organization", "Acme Corp")
    print(f"Org ID: {org_id}")

    print("\n--- 2. Testing Entity Building & Validation ---")

    # Test valid product
    product_data = {
        'gtin': gtin,
        'name': 'Nike Air Max',
        'price': '120.00',
        'currency': 'USD',
        'brand': 'Nike',
        'availability': 'InStock'
    }

    print("Building product...")
    product = builder.build_product(product_data)
    print(json.dumps(product, indent=2))

    print("\nValidating product (Strict)...")
    is_valid, errors, warnings = validator.validate(product, strict=True)
    print(f"Valid: {is_valid}")
    if errors: print(f"Errors: {errors}")
    if warnings: print(f"Warnings: {warnings}")

    print("\n--- 3. Testing Validation Failure ---")
    invalid_product = {
        "@context": "https://schema.org",
        "@type": "Product",
        "@id": product_id,
        "name": "Invalid Product"
        # Missing gtin14
    }

    is_valid, errors, warnings = validator.validate(invalid_product)
    print(f"Entity with missing GTIN Valid: {is_valid}")
    print(f"Expected Error: {errors}")

    print("\n--- 4. Testing WebPage Building ---")
    webpage_data = {
        'url': 'https://example.com/about-us',
        'name': 'About Us',
        'description': 'Our company story'
    }
    webpage = builder.build_webpage(webpage_data)
    print(json.dumps(webpage, indent=2))

    print("\nDRY RUN COMPLETE!")

if __name__ == "__main__":
    run_test()
