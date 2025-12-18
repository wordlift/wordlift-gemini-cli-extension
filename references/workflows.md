# Knowledge Graph Sync Workflows

This document describes common workflows for syncing data to WordLift Knowledge Graph using the Sitemap Import API.

## Initial Import Workflow

### Step 1: Import from Sitemap

Use the Sitemap Import API to jumpstart your Knowledge Graph:

**API Endpoint:** `POST https://api.wordlift.io/sitemap-imports`

**Important:** The endpoint is `/sitemap-imports` (plural), not `/sitemap/import`.

```python
from scripts.wordlift_client import WordLiftClient

client = WordLiftClient(api_key)

# Import all URLs from sitemap.xml
results = client.import_from_sitemap("https://example.com/sitemap.xml")

print(f"Imported {len(results)} pages")

# Inspect results (NDJSON format)
for result in results[:5]:  # Show first 5
    print(f"- {result.get('url')}: {result.get('status')}")
```

### Step 2: Query Imported Data

Check what was imported:

```python
# Get all imported entities
entities_query = """
query {
  entities(page: 0, rows: 100) {
    id: iri
    url: string(name: "schema:url")
    headline: string(name: "schema:headline")
    types: refs(name: "rdf:type")
  }
}
"""

result = client.graphql_query(entities_query)
entities = result['entities']

print(f"Found {len(entities)} entities in KG")
```

### Step 3: Enhance with Product Entities

For e-commerce sites, create proper Product entities with GS1 Digital Link IDs:

```python
from scripts.entity_builder import EntityBuilder

builder = EntityBuilder("https://data.wordlift.io/wl123")

# Product data from your catalog/database
products_data = [
    {
        'gtin': '12345678901231',
        'name': 'Product 1',
        'price': '29.99',
        'currency': 'USD'
    },
    # ... more products
]

# Create entities
entities = [builder.build_product(p) for p in products_data]

# Batch upload
client.batch_create_or_update(entities)
```

### Step 4: Validate Import

```python
# Check product count
products_query = """
query {
  products(rows: 10000) {
    totalCount: aggregateInt(operation: COUNT) { count }
  }
}
"""

result = client.graphql_query(products_query)
count = result['products']['totalCount']['count']
print(f"Total products in KG: {count}")
```

## Import from URL List

For specific pages instead of full sitemap:

```python
urls_to_import = [
    "https://example.com/product-1",
    "https://example.com/product-2",
    "https://example.com/about"
]

results = client.import_from_urls(urls_to_import)

# Process results
for result in results:
    print(f"Imported: {result.get('url')}")
    print(f"  Status: {result.get('status')}")
    print(f"  Entities: {result.get('entity_count', 0)}")
```

## Programmatic Entity Creation Workflow

### Step 1: Build Entity

```python
from scripts.entity_builder import EntityBuilder

builder = EntityBuilder("https://data.wordlift.io/wl123")

# Create a Product entity
product = builder.build_product({
    'gtin': '12345678901231',
    'name': 'Example Product',
    'description': 'A great product',
    'brand': 'Nike',
    'price': '29.99',
    'currency': 'USD',
    'availability': 'InStock',
    'image': 'https://example.com/product.jpg'
})
```

### Step 2: Validate Entity

```python
from scripts.shacl_validator import SHACLValidator

validator = SHACLValidator()

# Validate with SHACL shapes
is_valid, errors, warnings = validator.validate(product, strict=True)

if is_valid:
    print("✓ Entity is valid")
else:
    print("✗ Validation errors:")
    for error in errors:
        print(f"  - {error}")
```

### Step 3: Upload to KG

```python
from scripts.wordlift_client import WordLiftClient

client = WordLiftClient(api_key)

if is_valid:
    client.create_or_update_entity(product)
    print("✓ Entity uploaded successfully")
```

### Step 4: Verify in KG

```python
# Query to verify
result = client.graphql_query("""
  query {
    entity(url: "https://data.wordlift.io/wl123/01/12345678901231") {
      iri
      name: string(name: "schema:name")
      gtin14: string(name: "schema:gtin14")
    }
  }
""")

print(f"Verified: {result['entity']['name']}")
```

## Daily Sync Workflow

### Full Replacement Sync

Best for small catalogs or structural changes:

```python
from scripts.kg_sync import KGSyncOrchestrator

orchestrator = KGSyncOrchestrator(
    api_key=api_key,
    dataset_uri="https://data.wordlift.io/wl123"
)

# Load today's product data
with open('daily_products.json', 'r') as f:
    products_data = json.load(f)

# Full sync (creates new, updates existing)
stats = orchestrator.sync_products(products_data, batch_size=50)

print(f"Created: {stats['created']}")
print(f"Updated: {stats['updated']}")
print(f"Errors: {stats['errors']}")
```

### Incremental Patch Sync

Best for large catalogs with few daily changes:

```python
# Load products with changes
with open('changed_products.json', 'r') as f:
    changed_products = json.load(f)

# Incremental sync (PATCH only changed fields)
stats = orchestrator.incremental_update(changed_products)

print(f"Updated: {stats['updated']}")
print(f"No changes: {stats['no_changes']}")
```

### Manual Incremental Sync

For custom update logic:

```python
# Update specific product fields
client.patch_entity(
    entity_id="https://data.wordlift.io/wl123/01/12345678901231",
    patches=[
        {
            "op": "replace",
            "path": "/https://schema.org/offers/https://schema.org/price",
            "value": "34.99"
        },
        {
            "op": "replace",
            "path": "/https://schema.org/offers/https://schema.org/availability",
            "value": "https://schema.org/OutOfStock"
        }
    ]
)
```

## Entity Creation Patterns

### Product with GS1 Digital Link ID

```python
from scripts.entity_builder import EntityBuilder

builder = EntityBuilder("https://data.wordlift.io/wl123")

product = builder.build_product({
    'gtin': '12345678901231',
    'name': 'Example Product',
    'brand': 'Example Brand',
    'price': '29.99',
    'currency': 'USD',
    'sku': 'SKU-001',
    'image': 'https://example.com/image.jpg',
    'availability': 'InStock'
})

# ID will be: https://data.wordlift.io/wl123/01/12345678901231
```

### Product with Serial Number

```python
product = builder.build_product({
    'gtin': '12345678901231',
    'serial': 'SN12345',
    'name': 'Example Product'
})

# ID will be: https://data.wordlift.io/wl123/01/12345678901231/21/SN12345
```

### Organization Entity (Slug-based)

```python
org = builder.build_organization({
    'name': 'Acme Corporation',
    'url': 'https://acme.com',
    'logo': 'https://acme.com/logo.png'
})

# ID will be: https://data.wordlift.io/wl123/organization/acme-corporation
```

### Person Entity (Slug-based)

```python
from scripts.id_generator import generate_entity_id

person_id = generate_entity_id(
    "https://data.wordlift.io/wl123",
    "person",
    "John Doe"
)
# Result: https://data.wordlift.io/wl123/person/john-doe

person = {
    "@context": "https://schema.org",
    "@type": "Person",
    "@id": person_id,
    "name": "John Doe",
    "jobTitle": "CEO"
}

client.create_or_update_entity(person)
```

### Web Page Entity (Slug-based)

```python
webpage = builder.build_webpage({
    'url': 'https://example.com/about',
    'name': 'About Us',
    'description': 'Learn about our company',
    'datePublished': '2024-01-01'
})

# @id: https://data.wordlift.io/wl123/webpage/about-us
# url: https://example.com/about (stored in url property)

# With custom slug
webpage = builder.build_webpage({
    'url': 'https://example.com/contact',
    'name': 'Contact Us',
    'slug': 'contact'
})

# @id: https://data.wordlift.io/wl123/webpage/contact
```

## Batch Operations

### Create Multiple Entities

```python
entities = []

# Add products
for product_data in products_list:
    entities.append(builder.build_product(product_data))

# Add organizations
for org_data in orgs_list:
    entities.append(builder.build_organization(org_data))

# Batch upload (max 50-100 per batch)
batch_size = 50
for i in range(0, len(entities), batch_size):
    batch = entities[i:i+batch_size]
    client.batch_create_or_update(batch)
    print(f"Uploaded batch {i//batch_size + 1}")
```

### Batch Size Recommendations

- Small catalogs (<1000 products): batch_size=100
- Medium catalogs (1000-10000): batch_size=50
- Large catalogs (>10000): batch_size=25
- Network issues: batch_size=10

## Error Handling

### Handle Sitemap Import Failures

```python
try:
    results = client.import_from_sitemap(sitemap_url)

    # Check for errors in results
    errors = [r for r in results if r.get('error')]
    if errors:
        print(f"Found {len(errors)} errors:")
        for error in errors[:10]:  # Show first 10
            print(f"  - {error.get('url')}: {error.get('error')}")

except requests.HTTPError as e:
    print(f"Sitemap import failed: {e}")
    print(f"Status: {e.response.status_code}")
    print(f"Details: {e.response.text}")
```

### Handle Batch Upload Failures

```python
try:
    client.batch_create_or_update(entities)
except requests.HTTPError as e:
    print(f"Batch upload failed: {e}")

    # Retry with individual uploads to identify problem entities
    for entity in entities:
        try:
            client.create_or_update_entity(entity)
        except Exception as entity_error:
            print(f"Failed: {entity['@id']}")
            print(f"  Error: {entity_error}")
```

### Check for Existing Entities

```python
# Before creating, check if exists
if client.entity_exists(entity_id):
    print("Entity exists, will update")
    # Use PATCH for efficiency
    client.patch_entity(entity_id, patches)
else:
    print("Entity is new, will create")
    client.create_or_update_entity(entity)
```

## Monitoring and Validation

### Query Sync Status

```python
# Get product count
result = client.graphql_query("""
  query {
    products(rows: 10000) {
      totalCount: aggregateInt(operation: COUNT) { count }
    }
  }
""")

total = result['products']['totalCount']['count']
print(f"Total products: {total}")

# Get recently modified products
result = client.graphql_query("""
  query {
    products(
      query: {
        dateModifiedConstraint: { gt: "2024-01-01T00:00:00Z" }
      }
      rows: 100
    ) {
      iri
      dateModified: string(name: "schema:dateModified")
    }
  }
""")
```

### Validate GTINs Before Sync

```python
from scripts.id_generator import normalize_gtin, validate_gtin_check_digit

def validate_products(products_data):
    """Validate GTINs in product data."""
    valid = []
    invalid = []

    for product in products_data:
        gtin = product.get('gtin')
        if not gtin:
            invalid.append((product, "Missing GTIN"))
            continue

        try:
            gtin_14 = normalize_gtin(gtin)
            valid.append(product)
        except ValueError as e:
            invalid.append((product, str(e)))

    return valid, invalid

# Use before sync
valid_products, invalid_products = validate_products(products_data)

print(f"Valid: {len(valid_products)}")
print(f"Invalid: {len(invalid_products)}")

if invalid_products:
    print("\nInvalid GTINs:")
    for product, error in invalid_products[:10]:
        print(f"  - {product.get('name')}: {error}")
```

## Scheduling Daily Syncs

### Using Cron

```bash
# Run daily at 2 AM
0 2 * * * cd /path/to/project && /usr/bin/python3 scripts/kg_sync.py \
  --api-key $WORDLIFT_API_KEY \
  --dataset-uri https://data.wordlift.io/wl123 \
  --input /path/to/products.json \
  --incremental
```

### Using Python Scheduler

```python
import schedule
import time

def daily_sync():
    orchestrator = KGSyncOrchestrator(api_key, dataset_uri)

    # Extract products from your source
    products = extract_products_from_source()

    # Sync
    stats = orchestrator.incremental_update(products)

    # Log results
    print(f"Daily sync complete: {stats}")

# Schedule
schedule.every().day.at("02:00").do(daily_sync)

while True:
    schedule.run_pending()
    time.sleep(60)
```

## State-Specific Entity Pattern

For entities that vary by location (common in services):

```python
from scripts.id_generator import generate_entity_id

# State entity
state_id = generate_entity_id(
    "https://data.wordlift.io/wl123",
    "state",
    "Alaska"
)
# Result: https://data.wordlift.io/wl123/state/alaska

# Service specific to state
service_id = generate_entity_id(
    "https://data.wordlift.io/wl123",
    "service",
    "debt-consolidation-alaska"
)
# Result: https://data.wordlift.io/wl123/service/debt-consolidation-alaska

# Web page for state
page_id = generate_entity_id(
    "https://data.wordlift.io/wl123",
    "webpage",
    "alaska-services"
)
# Result: https://data.wordlift.io/wl123/webpage/alaska-services
```

## Query Patterns for Imported Data

### Get All WebPages from Sitemap

```python
result = client.graphql_query("""
  query {
    entities(
      query: {
        typeConstraint: { in: ["http://schema.org/WebPage"] }
      }
      rows: 1000
    ) {
      iri
      url: string(name: "schema:url")
      headline: string(name: "schema:headline")
    }
  }
""")
```

### Get Pages with SEO Keywords

```python
result = client.graphql_query("""
  query {
    entities(page: 0, rows: 100) {
      url: string(name: "schema:url")
      topKeywords: topN(
        name: "seovoc:seoKeywords"
        sort: { field: "seovoc:3MonthsImpressions", direction: DESC }
        limit: 5
      ) {
        name: string(name: "seovoc:name")
        impressions: int(name: "seovoc:3MonthsImpressions")
        clicks: int(name: "seovoc:3MonthsClicks")
      }
    }
  }
""")
```

## Tips for Success

1. **Start with sitemap import** to quickly populate KG
2. **Validate all entities** with SHACL validator before upload
3. **Use slug-based IDs** for predictable, human-readable URIs
4. **Batch operations** for efficiency (50-100 entities per batch)
5. **Incremental updates** with PATCH for daily syncs
6. **Monitor NDJSON responses** from sitemap import for errors
7. **Query after operations** to verify entity counts
8. **Handle errors gracefully** with retry logic for failed batches