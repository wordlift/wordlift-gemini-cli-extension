# Entity Reuse and SHACL Validation

This guide explains the two critical quality control features in the WordLift KG Builder:

1. **Entity Reuse** - Prevents duplicates by checking for existing entities via GraphQL
2. **SHACL Validation** - Ensures data quality before upload

## Entity Reuse

### Problem
When creating products, articles, or other entities, you often reference shared entities like:
- **Publishers** (Organizations)
- **Brands**
- **Authors** (People)
- **Places**

Without checking, you'd create duplicate entities every time, leading to:
- Fragmented data
- Inconsistent entity IRIs
- Poor data quality

### Solution: EntityReuseManager

The `EntityReuseManager` uses GraphQL queries to check if entities already exist before creating new ones.

```python
from scripts.entity_reuse import EntityReuseManager
from scripts.wordlift_client import WordLiftClient

client = WordLiftClient(api_key)
reuse_manager = EntityReuseManager(client, "https://data.wordlift.io/wl123")

# Preload existing entities for fast lookups
reuse_manager.preload_cache()
```

### Example: Reusing a Publisher

```python
# First product references "Acme Corporation"
publisher_iri_1 = reuse_manager.get_or_create_organization({
    'name': 'Acme Corporation',
    'url': 'https://acme.com',
    'logo': 'https://acme.com/logo.png'
})
# Output: + Creating new organization: Acme Corporation
# Returns: https://data.wordlift.io/wl123/organization/acme-corporation

# Second product also references "Acme Corporation"
publisher_iri_2 = reuse_manager.get_or_create_organization({
    'name': 'Acme Corporation'
})
# Output: ✓ Reusing existing organization: Acme Corporation
# Returns: https://data.wordlift.io/wl123/organization/acme-corporation

# Same IRI! No duplicate created
assert publisher_iri_1 == publisher_iri_2
```

### How It Works

1. **Check Cache** - Fast in-memory lookup
2. **Check by IRI** - Query KG for expected IRI
3. **Check by Name** - Query KG by entity name (in case different slug was used)
4. **Create if Not Found** - Only create if entity doesn't exist

### GraphQL Queries Used

**Query Organization by Name:**
```graphql
query($name: String!) {
  entities(
    query: {
      typeConstraint: { in: ["http://schema.org/Organization"] }
      nameConstraint: { in: [$name] }
    }
    rows: 1
  ) {
    iri
    name: string(name: "schema:name")
  }
}
```

**Query Brand by Name:**
```graphql
query($name: String!) {
  entities(
    query: {
      typeConstraint: { in: ["http://schema.org/Brand"] }
      nameConstraint: { in: [$name] }
    }
    rows: 1
  ) {
    iri
    name: string(name: "schema:name")
  }
}
```

### Supported Entity Types

```python
# Organizations
publisher_iri = reuse_manager.get_or_create_organization({
    'name': 'Publisher Name',
    'url': 'https://publisher.com',
    'logo': 'https://publisher.com/logo.png'
})

# People (Authors)
author_iri = reuse_manager.get_or_create_person({
    'name': 'John Doe',
    'jobTitle': 'Senior Writer',
    'email': 'john@example.com'
})

# Brands
brand = reuse_manager.get_or_create_brand('Nike')
# or with details
brand = reuse_manager.get_or_create_brand({
    'name': 'Nike',
    'logo': 'https://nike.com/logo.png',
    'url': 'https://nike.com'
})
```

### Integration with EntityBuilder

The `EntityBuilder` can use the `EntityReuseManager` automatically:

```python
from scripts.entity_builder import EntityBuilder
from scripts.entity_reuse import EntityReuseManager

client = WordLiftClient(api_key)
reuse_manager = EntityReuseManager(client, dataset_uri)
reuse_manager.preload_cache()

# Pass reuse manager to builder
builder = EntityBuilder(dataset_uri, reuse_manager=reuse_manager)

# Now when you build products, brands are automatically reused
product1 = builder.build_product({
    'gtin': '12345678901231',
    'name': 'Product 1',
    'brand': 'Nike',  # Creates Nike brand
    'price': '99.99',
    'currency': 'USD'
})

product2 = builder.build_product({
    'gtin': '98765432109876',
    'name': 'Product 2',
    'brand': 'Nike',  # Reuses Nike brand!
    'price': '149.99',
    'currency': 'USD'
})

# Both products reference the same Nike brand entity
assert product1['brand']['@id'] == product2['brand']['@id']
```

### Preloading Cache

For better performance with large catalogs:

```python
# Preload at start
reuse_manager.preload_cache()
# Output:
# Preloading entity cache...
#   Loaded 45 organizations
#   Loaded 12 people
#   Loaded 230 brands

# Now all lookups are instant (cache hits)
for product in products:
    brand = reuse_manager.get_or_create_brand(product['brand_name'])
    # ✓ Reusing existing brand: [brand_name] (instant!)
```

### Cache Management

```python
# Clear cache if needed
reuse_manager.clear_cache()

# Reload cache
reuse_manager.preload_cache()

# Get existing entities manually
orgs = reuse_manager.get_existing_entities_by_type('Organization', limit=1000)
brands = reuse_manager.get_existing_entities_by_type('Brand', limit=1000)
```

---

## SHACL Validation

### Problem
Invalid data can break your Knowledge Graph:
- Missing required fields
- Invalid data types
- Malformed IRIs
- Incorrect schema.org structure

### Solution: SHACLValidator

The `SHACLValidator` checks entities against SHACL shapes before upload.

```python
from scripts.shacl_validator import SHACLValidator

validator = SHACLValidator()

is_valid, errors, warnings = validator.validate(entity)
if not is_valid:
    print(f"Validation failed: {errors}")
```

### SHACL Shapes

Built-in shapes for common types:

**Product Shape:**
- Required: `@id`, `@type`, `name`, `gtin14`
- Recommended: `description`, `brand`, `offers`, `image`
- Constraints:
  - `gtin14` must be 14 digits
  - `@id` must follow GS1 Digital Link format (`/01/`)
  - `offers` must be an Offer object

**Organization Shape:**
- Required: `@id`, `@type`, `name`
- Recommended: `url`, `logo`, `description`
- Constraints:
  - `url` must start with `http`

**WebPage Shape:**
- Required: `@id`, `@type`, `url`, `name`
- Recommended: `description`, `datePublished`
- Constraints:
  - `url` must start with `http`

**Offer Shape:**
- Required: `@type`, `price`, `priceCurrency`
- Recommended: `availability`, `url`
- Constraints:
  - `priceCurrency` must be 3 characters (ISO 4217)
  - `availability` must be schema.org URL

### Example: Validating a Product

```python
validator = SHACLValidator()

product = {
    "@context": "https://schema.org",
    "@type": "Product",
    "@id": "https://data.wordlift.io/wl123/01/12345678901231",
    "name": "Example Product",
    "gtin14": "12345678901231",
    "offers": {
        "@type": "Offer",
        "price": "29.99",
        "priceCurrency": "USD",
        "availability": "https://schema.org/InStock"
    }
}

is_valid, errors, warnings = validator.validate(product)

if is_valid:
    print("✓ Product is valid!")
    # Safe to upload
    client.create_or_update_entity(product)
else:
    print("✗ Validation failed:")
    for error in errors:
        print(f"  - {error}")
```

### Validation Modes

**Normal Mode** (default):
- Required fields must be present
- Recommended fields trigger warnings only

```python
is_valid, errors, warnings = validator.validate(entity, strict=False)
```

**Strict Mode:**
- Required AND recommended fields must be present
- Use for high-quality data requirements

```python
is_valid, errors, warnings = validator.validate(entity, strict=True)
```

### Batch Validation

```python
validator = SHACLValidator()

entities = [product1, product2, product3, ...]

results = validator.validate_batch(entities, strict=False)

print(f"Total: {results['total']}")
print(f"Valid: {results['valid']}")
print(f"Invalid: {results['invalid']}")

# Get validation report
report = validator.get_validation_report(results)
print(report)
```

**Example Report:**
```
============================================================
SHACL VALIDATION REPORT
============================================================
Total entities: 100
Valid: 95
Invalid: 5

INVALID ENTITIES:
------------------------------------------------------------

Product - https://data.wordlift.io/wl123/01/12345678901234
  ✗ Missing required field: gtin14
  ✗ Constraint failed for field '@id': Product @id should follow GS1 Digital Link format

Product - https://data.wordlift.io/wl123/01/98765432109876
  ✗ Missing required field: name
  ✗ Offer: Missing required field: priceCurrency

WARNINGS:
------------------------------------------------------------

Product - https://data.wordlift.io/wl123/01/11111111111111
  ⚠ Missing recommended field: description
  ⚠ Missing recommended field: image

============================================================
```

### Filter Valid/Invalid Entities

```python
from scripts.shacl_validator import validate_before_upload

entities = [product1, product2, product3, ...]

valid_entities, invalid_entities = validate_before_upload(entities, strict=False)

print(f"Valid: {len(valid_entities)}")
print(f"Invalid: {len(invalid_entities)}")

# Upload only valid entities
if valid_entities:
    client.batch_create_or_update(valid_entities)

# Log invalid entities for review
for invalid in invalid_entities:
    print(f"Failed: {invalid['entity']['@id']}")
    print(f"Errors: {invalid['errors']}")
```

### Nested Entity Validation

The validator automatically validates nested entities:

```python
product = {
    "@type": "Product",
    "name": "Product",
    "gtin14": "12345678901231",
    "brand": {
        "@type": "Brand",
        "@id": "...",
        "name": "Nike"
    },
    "offers": {
        "@type": "Offer",
        "price": "99.99",
        "priceCurrency": "USD"
    }
}

is_valid, errors, warnings = validator.validate(product)
# Validates product, brand, and offer
# Errors prefixed with "Brand:" or "Offer:" for nested entities
```

---

## Integration in KG Sync

Both features are automatically enabled in `KGSyncOrchestrator`:

```python
from scripts.kg_sync import KGSyncOrchestrator

orchestrator = KGSyncOrchestrator(
    api_key=api_key,
    dataset_uri="https://data.wordlift.io/wl123",
    enable_validation=True,  # Enable SHACL validation
    enable_reuse=True        # Enable entity reuse
)

# During sync:
# 1. EntityReuseManager preloads cache
# 2. Entities are built with brand/publisher reuse
# 3. SHACL validation runs before upload
# 4. Only valid entities are uploaded

stats = orchestrator.sync_products(products_data)
```

### Command-Line Flags

```bash
# With validation and reuse (default)
python scripts/kg_sync.py \
  --api-key YOUR_KEY \
  --dataset-uri https://data.wordlift.io/wl123 \
  --input products.json

# Disable validation (not recommended)
python scripts/kg_sync.py \
  --api-key YOUR_KEY \
  --dataset-uri https://data.wordlift.io/wl123 \
  --input products.json \
  --no-validation

# Disable entity reuse (not recommended)
python scripts/kg_sync.py \
  --api-key YOUR_KEY \
  --dataset-uri https://data.wordlift.io/wl123 \
  --input products.json \
  --no-reuse

# Disable both (use with caution!)
python scripts/kg_sync.py \
  --api-key YOUR_KEY \
  --dataset-uri https://data.wordlift.io/wl123 \
  --input products.json \
  --no-validation \
  --no-reuse
```

### Sync Output Example

```
Preloading entity cache...
  Loaded 45 organizations
  Loaded 12 people
  Loaded 230 brands

Fetching existing products from KG...
Found 5240 existing products

Processing batch 1/20 (50 products)...
  ✓ Reusing existing brand: Nike
  ✓ Reusing existing brand: Adidas
  + Creating new brand: New Balance
  ✓ Reusing existing organization: Acme Corp
  Validating 50 entities...
  ✓ All entities passed validation
  Creating 12 new products...
  Updating 38 existing products...

Processing batch 2/20 (50 products)...
  ✓ Reusing existing brand: Nike
  Validating 50 entities...
  ⚠ Warning: 2 entities failed validation
  Creating 8 new products...
  Updating 40 existing products...

==================================================
Sync Complete!
Total: 1000
Created: 234
Updated: 758
Errors: 8
Skipped: 0
==================================================
```

---

## Best Practices

### 1. Always Preload Cache

```python
# DO THIS
reuse_manager.preload_cache()  # Load once at start
for product in products:
    brand = reuse_manager.get_or_create_brand(product['brand'])

# NOT THIS (slow!)
for product in products:
    brand = reuse_manager.get_or_create_brand(product['brand'])
    # Hits GraphQL API every time
```

### 2. Use Strict Validation in Production

```python
# Development: warnings only
is_valid, errors, warnings = validator.validate(entity, strict=False)

# Production: enforce quality
is_valid, errors, warnings = validator.validate(entity, strict=True)
```

### 3. Filter Before Upload

```python
# Always filter invalid entities
valid_entities, invalid_entities = validate_before_upload(entities)

# Upload valid
client.batch_create_or_update(valid_entities)

# Log invalid for review
with open('invalid_entities.json', 'w') as f:
    json.dump(invalid_entities, f, indent=2)
```

### 4. Monitor Reuse Statistics

```python
# Track reuse vs creation
reuse_count = 0
create_count = 0

for product_data in products:
    brand_name = product_data['brand']

    # Check if already in cache
    if brand_name in reuse_manager._cache['brands']:
        reuse_count += 1
    else:
        create_count += 1

    brand = reuse_manager.get_or_create_brand(brand_name)

print(f"Reused: {reuse_count}")
print(f"Created: {create_count}")
print(f"Reuse rate: {reuse_count / (reuse_count + create_count) * 100:.1f}%")
```

### 5. Custom SHACL Shapes

For domain-specific validation, extend the validator:

```python
validator = SHACLValidator()

# Add custom shape for your product type
validator.shapes['CustomProduct'] = {
    "required": ["@id", "@type", "name", "gtin14", "customField"],
    "recommended": ["description", "brand", "customAttribute"],
    "constraints": {
        "@type": lambda v: v == "CustomProduct",
        "customField": lambda v: isinstance(v, str) and len(v) > 10
    }
}
```

---

## Troubleshooting

### Entity Not Being Reused

**Symptom:** Same entity created multiple times

**Causes:**
1. Name mismatch (e.g., "Nike Inc." vs "Nike")
2. Cache not preloaded
3. Different slugs generated

**Solution:**
```python
# Normalize names before lookup
name = product_data['brand'].strip().lower()

# Or preload cache and check
reuse_manager.preload_cache()
existing_brands = reuse_manager._cache['brands']
print(f"Known brands: {list(existing_brands.keys())}")
```

### Validation Always Failing

**Symptom:** All entities marked invalid

**Causes:**
1. Wrong @context
2. Missing required fields
3. Incorrect IRI format

**Solution:**
```python
# Check specific entity
is_valid, errors, warnings = validator.validate(entity)
print(f"Errors: {errors}")

# Common fixes:
entity['@context'] = 'https://schema.org'  # Not http://
entity['@id'] = generate_product_id(...)  # Use ID generator
entity['gtin14'] = normalize_gtin(entity['gtin'])  # Normalize GTIN
```

### Performance Issues

**Symptom:** Slow sync times

**Solution:**
```python
# Preload cache at start (once)
reuse_manager.preload_cache()

# Use batch operations
client.batch_create_or_update(entities)  # Not individual

# Validate in batches
results = validator.validate_batch(entities)  # Not one-by-one
```

---

## Summary

✅ **Entity Reuse** prevents duplicates by checking KG via GraphQL
✅ **SHACL Validation** ensures data quality before upload
✅ **Both enabled by default** in KGSyncOrchestrator
✅ **Preload cache** for performance
✅ **Monitor statistics** to track reuse rates
✅ **Use strict mode** in production for high quality

These features are essential for maintaining a clean, high-quality Knowledge Graph!