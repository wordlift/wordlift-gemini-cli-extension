#!/usr/bin/env python3
"""
Example Product Extraction Script
Customize this script to extract products from your data source.
"""

import json
import os
import sys
from typing import List, Dict, Any


def extract_from_database() -> List[Dict[str, Any]]:
    """
    Extract products from a database.

    Example using PostgreSQL:
    """
    # Uncomment and customize for your database
    """
    import psycopg2

    conn = psycopg2.connect(
        host=os.environ.get('DB_HOST', 'localhost'),
        database=os.environ.get('DB_NAME', 'products'),
        user=os.environ.get('DB_USER', 'user'),
        password=os.environ.get('DB_PASSWORD', 'password')
    )

    cursor = conn.cursor()

    query = '''
        SELECT
            gtin,
            name,
            description,
            brand,
            price,
            currency,
            sku,
            image_url,
            availability,
            rating,
            review_count
        FROM products
        WHERE active = true
        ORDER BY updated_at DESC
    '''

    cursor.execute(query)
    rows = cursor.fetchall()

    products = []
    for row in rows:
        products.append({
            'gtin': row[0],
            'name': row[1],
            'description': row[2],
            'brand': row[3],
            'price': str(row[4]),
            'currency': row[5],
            'sku': row[6],
            'image': row[7],
            'availability': row[8],
            'rating': str(row[9]) if row[9] else None,
            'reviewCount': str(row[10]) if row[10] else None
        })

    cursor.close()
    conn.close()

    return products
    """

    # Placeholder - replace with actual database logic
    return []


def extract_from_csv(csv_file: str) -> List[Dict[str, Any]]:
    """
    Extract products from a CSV file.

    CSV should have columns: gtin, name, description, brand, price, currency, sku, image, availability
    """
    import csv

    products = []

    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        for row in reader:
            product = {
                'gtin': row.get('gtin'),
                'name': row.get('name'),
                'description': row.get('description'),
                'brand': row.get('brand'),
                'price': row.get('price'),
                'currency': row.get('currency', 'USD'),
                'sku': row.get('sku'),
                'image': row.get('image'),
                'availability': row.get('availability', 'InStock')
            }

            # Add optional fields if present
            if 'rating' in row and row['rating']:
                product['rating'] = row['rating']
            if 'reviewCount' in row and row['reviewCount']:
                product['reviewCount'] = row['reviewCount']

            products.append(product)

    return products


def extract_from_json(json_file: str) -> List[Dict[str, Any]]:
    """
    Extract products from a JSON file.

    JSON should be an array of product objects.
    """
    with open(json_file, 'r', encoding='utf-8') as f:
        products = json.load(f)

    return products


def extract_from_api() -> List[Dict[str, Any]]:
    """
    Extract products from an external API.

    Example using REST API:
    """
    # Uncomment and customize for your API
    """
    import requests

    api_url = os.environ.get('PRODUCT_API_URL', 'https://api.example.com/products')
    api_key = os.environ.get('PRODUCT_API_KEY')

    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }

    response = requests.get(api_url, headers=headers)
    response.raise_for_status()

    data = response.json()

    # Transform API response to expected format
    products = []
    for item in data.get('products', []):
        products.append({
            'gtin': item.get('gtin'),
            'name': item.get('title'),
            'description': item.get('desc'),
            'brand': item.get('manufacturer'),
            'price': str(item.get('price')),
            'currency': item.get('currency', 'USD'),
            'sku': item.get('sku'),
            'image': item.get('image_url'),
            'availability': 'InStock' if item.get('in_stock') else 'OutOfStock'
        })

    return products
    """

    # Placeholder - replace with actual API logic
    return []


def extract_from_shopify() -> List[Dict[str, Any]]:
    """
    Extract products from Shopify store.

    Requires: SHOPIFY_SHOP_NAME, SHOPIFY_ACCESS_TOKEN
    """
    # Uncomment and customize
    """
    import requests

    shop_name = os.environ.get('SHOPIFY_SHOP_NAME')
    access_token = os.environ.get('SHOPIFY_ACCESS_TOKEN')

    url = f'https://{shop_name}.myshopify.com/admin/api/2024-01/products.json'
    headers = {
        'X-Shopify-Access-Token': access_token,
        'Content-Type': 'application/json'
    }

    all_products = []
    page_info = None

    while True:
        params = {'limit': 250}
        if page_info:
            params['page_info'] = page_info

        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()

        data = response.json()
        products = data.get('products', [])

        for product in products:
            # Get first variant for pricing
            variant = product['variants'][0] if product['variants'] else {}

            all_products.append({
                'gtin': variant.get('barcode') or product.get('gtin'),
                'name': product.get('title'),
                'description': product.get('body_html'),
                'brand': product.get('vendor'),
                'price': variant.get('price'),
                'currency': 'USD',  # Adjust based on your store
                'sku': variant.get('sku'),
                'image': product['images'][0]['src'] if product.get('images') else None,
                'availability': 'InStock' if variant.get('inventory_quantity', 0) > 0 else 'OutOfStock'
            })

        # Check for pagination
        link_header = response.headers.get('Link', '')
        if 'rel="next"' in link_header:
            # Extract page_info from Link header
            import re
            match = re.search(r'page_info=([^&>]+)', link_header)
            page_info = match.group(1) if match else None
        else:
            break

    return all_products
    """

    return []


def extract_from_woocommerce() -> List[Dict[str, Any]]:
    """
    Extract products from WooCommerce store.

    Requires: WC_URL, WC_CONSUMER_KEY, WC_CONSUMER_SECRET
    """
    # Uncomment and customize
    """
    from woocommerce import API

    wcapi = API(
        url=os.environ.get('WC_URL', 'https://example.com'),
        consumer_key=os.environ.get('WC_CONSUMER_KEY'),
        consumer_secret=os.environ.get('WC_CONSUMER_SECRET'),
        version="wc/v3"
    )

    all_products = []
    page = 1

    while True:
        response = wcapi.get("products", params={"per_page": 100, "page": page})
        products = response.json()

        if not products:
            break

        for product in products:
            all_products.append({
                'gtin': product.get('sku'),  # WC doesn't have GTIN by default
                'name': product.get('name'),
                'description': product.get('description'),
                'brand': next((attr['options'][0] for attr in product.get('attributes', [])
                              if attr['name'] == 'Brand'), None),
                'price': product.get('price'),
                'currency': 'USD',  # Adjust based on your store
                'sku': product.get('sku'),
                'image': product['images'][0]['src'] if product.get('images') else None,
                'availability': 'InStock' if product.get('stock_status') == 'instock' else 'OutOfStock'
            })

        page += 1

    return all_products
    """

    return []


def extract_products_from_source() -> List[Dict[str, Any]]:
    """
    Main extraction function.
    Customize this to call the appropriate extraction method for your data source.
    """

    # Option 1: From database
    # return extract_from_database()

    # Option 2: From CSV file
    # return extract_from_csv('products.csv')

    # Option 3: From JSON file
    # return extract_from_json('products.json')

    # Option 4: From API
    # return extract_from_api()

    # Option 5: From Shopify
    # return extract_from_shopify()

    # Option 6: From WooCommerce
    # return extract_from_woocommerce()

    # Default: Load from JSON file
    json_file = os.environ.get('PRODUCTS_FILE', 'products.json')
    if os.path.exists(json_file):
        return extract_from_json(json_file)

    print("No data source configured. Please customize extract_products_from_source()")
    return []


def validate_products(products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Validate and clean product data before syncing.
    """
    valid_products = []

    for product in products:
        # Check required fields
        if not product.get('gtin'):
            print(f"Warning: Product '{product.get('name', 'unknown')}' missing GTIN, skipping")
            continue

        if not product.get('name'):
            print(f"Warning: Product with GTIN '{product.get('gtin')}' missing name, skipping")
            continue

        # Clean price (ensure it's a string)
        if 'price' in product and product['price'] is not None:
            product['price'] = str(product['price']).replace(',', '')

        # Ensure currency
        if 'price' in product and 'currency' not in product:
            product['currency'] = 'USD'

        # Normalize availability
        if 'availability' in product:
            avail_map = {
                'in stock': 'InStock',
                'instock': 'InStock',
                'available': 'InStock',
                'out of stock': 'OutOfStock',
                'outofstock': 'OutOfStock',
                'unavailable': 'OutOfStock',
                'preorder': 'PreOrder',
                'pre-order': 'PreOrder',
            }
            avail_lower = str(product['availability']).lower()
            product['availability'] = avail_map.get(avail_lower, product['availability'])

        valid_products.append(product)

    return valid_products


if __name__ == '__main__':
    """
    Extract products and output as JSON.
    Usage: python extract_products.py > products.json
    """

    # Extract products
    products = extract_products_from_source()

    # Validate and clean
    products = validate_products(products)

    print(f"# Extracted {len(products)} valid products", file=sys.stderr)

    # Output as JSON
    print(json.dumps(products, indent=2))