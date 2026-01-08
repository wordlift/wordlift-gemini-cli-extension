---
name: wordlift-kg-builder
description: Build and maintain Knowledge Graphs from webpages using WordLift APIs. Use when importing pages from sitemaps via WordLift Sitemap Import API, creating product catalogs with GS1 Digital Link identifiers (GTIN-based), generating slug-based entity IDs for organizations/people/webpages, creating JSON-LD markup programmatically, or performing daily sync workflows with batch operations and PATCH updates. Handles entity lifecycle management with proper JSON-LD structure.
---

# WordLift Knowledge Graph Builder

Build and maintain Knowledge Graphs from webpages using WordLift's Sitemap Import API, with focus on product catalogs and e-commerce data.

## Core Capabilities

1. **Sitemap Import API**: Direct import of URLs from sitemap.xml or URL lists
2. **Template Configuration**: Interactive workflow to validate markup templates before bulk imports
3. **GS1 Digital Link for Products**: `{dataset_uri}/01/{GTIN-14}` identifiers
4. **Slug-based IDs for Other Entities**: `{dataset_uri}/{entity_type}/{slug}` format (⚠️ **MUST use recognized patterns**)
5. **Entity Reuse via GraphQL**: Prevents duplicates by checking for existing entities (Organizations, Brands, People)
6. **SHACL Validation**: Ensures data quality before upload with built-in shapes for Products, Organizations, WebPages, etc.
7. **JSON-LD Creation**: Programmatic creation of schema.org markup with EntityBuilder
8. **Entity Upgrading**: Post-import type changes and property updates using Fetch-Modify-Update pattern
9. **Entity Verification**: Verify entities are actually persisted (not just 200 OK)
10. **Daily Sync Workflows**: Full replacement or incremental PATCH updates
11. **Batch Operations**: Efficient bulk create/update operations

## Quick Start

### 1. Import Pages from Sitemap

Use the Sitemap Import API to jumpstart your Knowledge Graph:

**API Endpoint:** `POST https://api.wordlift.io/sitemap-imports`

```python
from scripts.wordlift_client import WordLiftClient

client = WordLiftClient(api_key)

# Import from sitemap.xml
results = client.import_from_sitemap("https://example.com/sitemap.xml")
print(f"Imported {len(results)} pages")

# Or import specific URLs
results = client.import_from_urls([
    "https://example.com/page1.html",
    "https://example.com/page2.html"
])
```

The API returns NDJSON (newline-delimited JSON) with details about each imported page.

**Important:** The endpoint is `/sitemap-imports` (plural), not `/sitemap/import` or `/sitemap-import`.

### 2. Query Imported Data

After import, query the data via GraphQL:

```python
result = client.graphql_query("""
  query {
    entities(page: 0, rows: 1000) {
      id: iri
      headline: string(name: "schema:headline")
      text: string(name: "schema:text")
      url: string(name: "schema:url")
    }
  }
""")
```

### 3. Enhance with Proper Product Entities

For e-commerce, create products with GS1 Digital Link IDs:

```python
from scripts.entity_builder import EntityBuilder

builder = EntityBuilder("https://data.wordlift.io/wl123")

product = builder.build_product({
    'gtin': '12345678901231',
    'name': 'Product Name',
    'brand': 'Brand Name',
    'price': '29.99',
    'currency': 'USD'
})

client.create_or_update_entity(product)
```

## Entity ID Generation

### Products (GS1 Digital Link)

Products use GS1 Digital Link format with GTIN-14:

```python
from scripts.id_generator import generate_product_id

# Basic product
product_id = generate_product_id("https://data.wordlift.io/wl123", "12345678901231")
# Result: https://data.wordlift.io/wl123/01/12345678901231

# With serial number
product_id = generate_product_id("https://data.wordlift.io/wl123", "12345678901231", serial="SN123")
# Result: https://data.wordlift.io/wl123/01/12345678901231/21/SN123
```

GTINs are automatically:
- Normalized to 14 digits (left-padded with zeros)
- Validated using GS1 check digit algorithm

### Other Entities (Slug-based)

Non-product entities use descriptive slug-based IDs:

```python
from scripts.id_generator import generate_entity_id

# Organization
org_id = generate_entity_id("https://data.wordlift.io/wl123", "organization", "Acme Corporation")
# Result: https://data.wordlift.io/wl123/organization/acme-corporation

# Person
person_id = generate_entity_id("https://data.wordlift.io/wl123", "person", "John Doe")
# Result: https://data.wordlift.io/wl123/person/john-doe

# WebPage (slug from URL path or title)
page_id = generate_entity_id("https://data.wordlift.io/wl123", "webpage", "About Us")
# Result: https://data.wordlift.io/wl123/webpage/about-us

# WebPage homepage
homepage_id = generate_entity_id("https://data.wordlift.io/wl123", "webpage", "homepage")
# Result: https://data.wordlift.io/wl123/webpage/homepage

# State-specific service
service_id = generate_entity_id("https://data.wordlift.io/wl123", "service", "debt-consolidation-alaska")
# Result: https://data.wordlift.io/wl123/service/debt-consolidation-alaska
```

Slug generation:
- Converts to lowercase
- Replaces spaces with hyphens
- Removes non-alphanumeric characters
- Handles consecutive hyphens

**Important:** The page URL goes in the `url` property, while the @id uses the slug-based pattern within your dataset URI.



## ⚠️ IRI Pattern Requirements (CRITICAL)

**CRITICAL**: WordLift requires specific IRI path patterns. The API will **return 200 OK for invalid patterns** but **entities will NOT be persisted** (silent failure).

### Valid Patterns Only

| Entity Type | Required Pattern | Example |
|------------|------------------|---------|
| Products | `/01/{GTIN-14}` | `https://data.wordlift.io/wl123/01/12345678901234` |
| Organizations | `/organization/{slug}` | `https://data.wordlift.io/wl123/organization/acme` |
| Places | `/place/{slug}` | `https://data.wordlift.io/wl123/place/italy` |
| People | `/person/{slug}` | `https://data.wordlift.io/wl123/person/john-doe` |
| Destinations | `/destination/{slug}` | `https://data.wordlift.io/wl123/destination/venice` |
| Articles | `/article/{slug}` | `https://data.wordlift.io/wl123/article/news` |

**Invalid patterns** (accepted by API but NOT persisted):
- ❌ `/sejour/country/destination` (auto-generated from sitemap)
- ❌ `/custom/nested/path` (arbitrary nesting)
- ❌ `/mytype/{slug}` (unrecognized entity type)

### Always Verify Entity Persistence

```python
from scripts.entity_verifier import verify_entity_persisted

# After creating entity
is_persisted, message = verify_entity_persisted(entity['@id'], wait_seconds=2)

if not is_persisted:
    print(f"⚠️  CRITICAL: Entity not persisted! Reason: {message}")
    # Check IRI pattern and recreate with valid pattern
```

**The `generate_entity_id()` function now validates patterns and will raise ValueError for invalid patterns.**

See `references/iri-patterns-and-verification.md` for complete guide.

## Creating JSON-LD Entities

### Build Entities Programmatically

Use `EntityBuilder` to create schema.org JSON-LD entities:

```python
from scripts.entity_builder import EntityBuilder

builder = EntityBuilder("https://data.wordlift.io/wl92832")

# Create a Product
product = builder.build_product({
    'gtin': '12345678901231',
    'name': 'Product Name',
    'description': 'Product description',
    'brand': 'Nike',
    'price': '99.99',
    'currency': 'USD',
    'availability': 'InStock',
    'image': 'https://example.com/product.jpg'
})

# Upload to KG
client.create_or_update_entity(product)
```

### Validate Before Upload

Always validate entities before uploading:

```python
from scripts.shacl_validator import SHACLValidator

validator = SHACLValidator()

# Validate
is_valid, errors, warnings = validator.validate(product, strict=True)

if is_valid:
    print("✓ Valid! Safe to upload")
    client.create_or_update_entity(product)
else:
    print(f"✗ Validation errors: {errors}")
```

The validator checks:
- Required fields (@context, @type, @id)
- Entity-specific requirements (Product needs name, gtin14)
- Proper URL formats
- GS1 Digital Link format for products
- Offer structure (price, currency, availability)

### Supported Entity Types

```python
# Organization
org = builder.build_organization({
    'name': 'Company Name',
    'url': 'https://example.com',
    'logo': 'https://example.com/logo.png'
})

# Person
person = builder.build_person({
    'name': 'John Doe',
    'jobTitle': 'CEO',
    'email': 'john@example.com'
})

# WebPage
webpage = builder.build_webpage({
    'url': 'https://example.com/about',
    'name': 'About Us',
    'description': 'Learn about our company'
})
```

## Entity Reuse (Preventing Duplicates)

### Problem
When creating multiple products or articles, you often reference the same entities:
- **Brands** (e.g., "Nike" across 100 products)
- **Publishers** (e.g., "Acme Corporation" across articles)
- **Authors** (e.g., "John Doe" across blog posts)

Without checking, you'd create duplicates every time, fragmenting your data.

### Solution: EntityReuseManager

The `EntityReuseManager` uses GraphQL queries to check if entities already exist:

```python
from scripts.entity_reuse import EntityReuseManager
from scripts.entity_builder import EntityBuilder

client = WordLiftClient(api_key)
reuse_manager = EntityReuseManager(client, "https://data.wordlift.io/wl123")

# Preload cache for fast lookups
reuse_manager.preload_cache()
# Output:
#   Loaded 45 organizations
#   Loaded 230 brands
#   Loaded 12 people

# Create builder with reuse manager
builder = EntityBuilder(dataset_uri, reuse_manager=reuse_manager)

# Build products - brands are automatically reused
product1 = builder.build_product({'gtin': '12345', 'brand': 'Nike', ...})
# Output: + Creating new brand: Nike

product2 = builder.build_product({'gtin': '67890', 'brand': 'Nike', ...})
# Output: ✓ Reusing existing brand: Nike

# Both products reference the same Nike brand entity!
```

### Supported Entity Types

```python
# Organizations (Publishers)
publisher_iri = reuse_manager.get_or_create_organization({
    'name': 'Acme Corporation',
    'url': 'https://acme.com',
    'logo': 'https://acme.com/logo.png'
})

# People (Authors)
author_iri = reuse_manager.get_or_create_person({
    'name': 'John Doe',
    'jobTitle': 'Senior Writer'
})

# Brands
brand = reuse_manager.get_or_create_brand('Nike')
```

### How It Works

1. **Cache Check** - Fast in-memory lookup
2. **IRI Check** - Query KG for expected IRI via GraphQL
3. **Name Check** - Query KG by name (in case different slug)
4. **Create Only If Not Found** - Avoids duplicates

See `references/entity-reuse-and-validation.md` for complete documentation.

## SHACL Validation (Data Quality)

### Problem
Invalid data breaks your Knowledge Graph:
- Missing required fields (name, GTIN)
- Invalid formats (wrong GTIN length, bad URLs)
- Incorrect structure (missing Offer in Product)

### Solution: SHACLValidator

Built-in SHACL shapes validate entities before upload:

```python
from scripts.shacl_validator import SHACLValidator

validator = SHACLValidator()

# Validate single entity
is_valid, errors, warnings = validator.validate(product)

if is_valid:
    print("✓ Valid! Safe to upload")
    client.create_or_update_entity(product)
else:
    print(f"✗ Invalid: {errors}")
```

### Built-in Shapes

**Product:**
- Required: `@id`, `@type`, `name`, `gtin14`
- Recommended: `description`, `brand`, `offers`, `image`
- Validates: GTIN format, GS1 Digital Link IRI, Offer structure

**Organization:**
- Required: `@id`, `@type`, `name`
- Recommended: `url`, `logo`, `description`

**WebPage:**
- Required: `@id`, `@type`, `url`, `name`
- Recommended: `description`, `datePublished`

**Offer:**
- Required: `@type`, `price`, `priceCurrency`
- Validates: Currency code (3 chars), availability URL format

### Batch Validation

```python
validator = SHACLValidator()

results = validator.validate_batch(entities)

print(f"Valid: {results['valid']}")
print(f"Invalid: {results['invalid']}")

# Get detailed report
report = validator.get_validation_report(results)
print(report)

# Filter valid entities
from scripts.shacl_validator import validate_before_upload

valid_entities, invalid_entities = validate_before_upload(entities)

# Upload only valid
client.batch_create_or_update(valid_entities)
```

### Validation Modes

**Normal Mode** (warnings for recommended fields):
```python
validator.validate(entity, strict=False)
```

**Strict Mode** (errors for recommended fields):
```python
validator.validate(entity, strict=True)
```

See `references/entity-reuse-and-validation.md` for complete documentation.

## Integration in Sync Workflows

Both features are enabled by default:

```python
from scripts.kg_sync import KGSyncOrchestrator

orchestrator = KGSyncOrchestrator(
    api_key=api_key,
    dataset_uri="https://data.wordlift.io/wl123",
    enable_validation=True,  # SHACL validation
    enable_reuse=True        # Entity reuse
)

# During sync:
# 1. Preloads entity cache (organizations, brands, people)
# 2. Reuses existing entities automatically
# 3. Validates all entities with SHACL shapes
# 4. Uploads only valid entities

stats = orchestrator.sync_products(products_data)
```

**Command-line:**
```bash
# With validation and reuse (default)
python scripts/kg_sync.py \
  --api-key YOUR_KEY \
  --dataset-uri https://data.wordlift.io/wl123 \
  --input products.json

# Disable validation (not recommended)
python scripts/kg_sync.py \
  --input products.json \
  --no-validation

# Disable entity reuse (not recommended)
python scripts/kg_sync.py \
  --input products.json \
  --no-reuse
```



### Product Entity

```python
from scripts.entity_builder import EntityBuilder

builder = EntityBuilder("https://data.wordlift.io/wl123")

product = builder.build_product({
    'gtin': '12345678901231',
    'name': 'Product Name',
    'description': 'Product description',
    'brand': 'Brand Name',
    'price': '29.99',
    'currency': 'USD',
    'sku': 'SKU-001',
    'image': 'https://example.com/image.jpg',
    'availability': 'InStock'
})
```

Result is proper JSON-LD with:
- GS1 Digital Link @id
- schema.org vocabulary
- Validated structure

### Organization Entity

```python
org = builder.build_organization({
    'name': 'Acme Corporation',
    'url': 'https://acme.com',
    'logo': 'https://acme.com/logo.png',
    'email': 'info@acme.com'
})
# ID: https://data.wordlift.io/wl123/organization/acme-corporation
```

### Web Page Entity

```python
webpage = builder.build_webpage({
    'url': 'https://example.com/about',
    'name': 'About Us',
    'description': 'Learn about our company',
    'datePublished': '2024-01-01'
})
# @id: https://data.wordlift.io/wl123/webpage/about-us
# url: https://example.com/about (in the url property)

# With custom slug
webpage = builder.build_webpage({
    'url': 'https://example.com/contact',
    'name': 'Contact Us',
    'slug': 'contact'  # Custom slug
})
# @id: https://data.wordlift.io/wl123/webpage/contact

# Homepage
homepage = builder.build_webpage({
    'url': 'https://example.com/',
    'name': 'Homepage',
    'slug': 'homepage'
})
# @id: https://data.wordlift.io/wl123/webpage/homepage
```

The @id uses a slug-based pattern within your dataset URI, while the actual page URL is stored in the `url` property.

## Syncing to WordLift

### Batch Create/Update

```python
from scripts.wordlift_client import WordLiftClient
from scripts.entity_builder import EntityBuilder

client = WordLiftClient(api_key)
builder = EntityBuilder("https://data.wordlift.io/wl123")

entities = [
    builder.build_product({...}),
    builder.build_product({...}),
    builder.build_organization({...})
]

# Batch operation (upsert - creates or updates)
client.batch_create_or_update(entities)
```

### Incremental Updates (PATCH)

For daily syncs where only some fields change:

```python
# Patch specific fields only
client.patch_entity(
    entity_id="https://data.wordlift.io/wl123/01/12345678901231",
    patches=[
        {"op": "replace", "path": "/https://schema.org/offers/https://schema.org/price", "value": "34.99"},
        {"op": "add", "path": "/https://schema.org/image", "value": "https://example.com/new.jpg"}
    ]
)
```

## Querying the KG

### Check Existing Products

```python
# Get all products
products = client.get_products(limit=100)

# Get all existing GTINs
existing_gtins = client.get_all_product_gtins()

# Check if entity exists
exists = client.entity_exists("https://data.wordlift.io/wl123/01/12345678901231")
```

### Custom GraphQL Queries

See `references/graphql_queries.md` for common patterns.

```python
# Get imported pages with SEO keywords
result = client.graphql_query("""
  query {
    entities(page: 0, rows: 100) {
      id: iri
      url: string(name: "schema:url")
      seoKeywords: strings(name: "seovoc:seoKeywords")
      topKeywords: topN(
        name: "seovoc:seoKeywords"
        sort: { field: "seovoc:3MonthsImpressions", direction: DESC }
        limit: 3
      ) {
        name: string(name: "seovoc:name")
        impressions: int(name: "seovoc:3MonthsImpressions")
      }
    }
  }
""")
```

## Workflow Patterns

### Post-Import Entity Upgrading

**After importing pages, upgrade entity types and add properties:**

```python
from scripts.entity_upgrader import upgrade_entity, upgrade_batch
from scripts.wordlift_client import WordLiftClient

client = WordLiftClient(api_key)

# Single entity upgrade
upgrade_entity(
    client,
    "https://data.wordlift.io/wl92832/webpage/my-post",
    new_type="Article",
    new_props={
        "author": {
            "@type": "Person",
            "@id": "https://data.wordlift.io/wl92832/person/john-doe",
            "name": "John Doe"
        }
    }
)

# Batch upgrade: WebPage → Article
result = client.graphql_query("""
  query {
    entities(query: { typeConstraint: { in: ["http://schema.org/WebPage"] } }) {
      iri
    }
  }
""")

iris = [e['iri'] for e in result['entities']]
stats = upgrade_batch(client, iris, new_type="Article")
```

**Why Entity Upgrader?**
- ✅ Changes entity types (PATCH can't do this)
- ✅ Preserves existing properties automatically
- ✅ Handles complex nested objects
- ✅ Validates complete entity before upload

**Command-line:**
```bash
# Single entity
python scripts/entity_upgrader.py <IRI> --type Article

# Batch from file
python scripts/entity_upgrader.py --batch-file iris.txt --type Article --props '{...}'
```

See `references/entity-upgrading.md` for complete guide.

### Template Configuration (Before Bulk Import)

**CRITICAL**: Before importing hundreds of pages, configure and validate your markup template using samples.

```python
from scripts.template_configurator import interactive_template_configuration
from scripts.wordlift_client import WordLiftClient

# Select 2-3 representative sample pages
sample_urls = [
    "https://yoursite.com/blog/post-1",
    "https://yoursite.com/blog/post-2",
    "https://yoursite.com/about"
]

client = WordLiftClient(api_key)

# Run interactive configuration
template_config = interactive_template_configuration(
    client,
    dataset_uri,
    sample_urls
)

# Review proposed markup:
# - Entity type (BlogPosting, Article, WebPage)
# - Required properties (author, publisher, datePublished)
# - Metadata extraction (headline, description, image)
# - ID pattern (slug generation)

# User approves template → Proceed with bulk import
```

**Why this is critical:**
- ❌ Without: Import 700 pages with wrong @type, have to delete and re-import
- ✅ With: Get it right the first time, validate on samples before bulk operation

See `references/template-configuration.md` for complete workflow guide.

### Initial Import from Sitemap

1. **Import pages** using Sitemap Import API
2. **Query imported data** to see what was created
3. **Enhance with products** by creating proper Product entities with GS1 IDs
4. **Validate** entity counts and structure

```python
# Step 1: Import
results = client.import_from_sitemap("https://example.com/sitemap.xml")

# Step 2: Query
entities = client.graphql_query("""{ entities(rows: 10) { iri url: string(name: "schema:url") } }""")

# Step 3: Create products
for product_data in products_list:
    product = builder.build_product(product_data)
    client.create_or_update_entity(product)
```

### Daily Sync Strategy

1. **Extract** product data from your source
2. **Query** existing products to identify what's new/changed
3. **Sync** using orchestrator:
   - New products → batch create
   - Existing products → batch update or PATCH
4. **Validate** sync completed successfully

See `references/workflows.md` for detailed workflow patterns.
**For automated scheduling**, see `references/scheduling.md` for cron, GitHub Actions, Docker, and cloud function setups.

```bash
python scripts/kg_sync.py \
  --api-key YOUR_API_KEY \
  --dataset-uri https://data.wordlift.io/wl123 \
  --input products.json \
  --batch-size 50
```

For incremental updates:
```bash
python scripts/kg_sync.py \
  --api-key YOUR_API_KEY \
  --dataset-uri https://data.wordlift.io/wl123 \
  --input products.json \
  --incremental
```

### Handling Large Catalogs

For catalogs >10,000 products:
- Use batch_size=25-50 to avoid timeouts
- Use incremental PATCH for daily updates
- Schedule syncs during off-peak hours
- Monitor import progress with NDJSON streaming

## Script Reference

### `entity_verifier.py`
Verify entity persistence (prevent silent failures):
- `verify_entity_persisted()` - Check if entity is dereferenceable (2 seconds)
- `verify_via_graphql()` - Check GraphQL indexing (10+ seconds)
- `verify_entity_complete()` - Complete verification suite
- `check_iri_pattern()` - Validate IRI follows WordLift patterns
- **CRITICAL**: Always verify after creation - API returns 200 OK even for invalid IRIs

### `entity_upgrader.py`
Upgrade existing entities (Fetch-Modify-Update pattern):
- Change entity types (WebPage → Article)
- Add complex nested properties (author, publisher)
- Preserve existing data automatically
- Batch upgrade from file
- Safer than PATCH for structural changes

### `template_configurator.py`
Configure markup templates before bulk imports:
- `TemplateConfigurator.analyze_sample_pages()` - Analyze sample pages
- `TemplateConfigurator.display_configuration_summary()` - Show analysis summary
- `TemplateConfigurator.generate_configuration_questions()` - Generate config questions
- `TemplateConfigurator.save_template()` - Save approved template
- `interactive_template_configuration()` - Full interactive workflow

### `id_generator.py`
Generate entity IDs:
- `generate_product_id()` - GS1 Digital Link for products
- `generate_entity_id()` - Slug-based for other entities
- `generate_slug()` - Convert text to URL-friendly slug
- `normalize_gtin()` - Convert any GTIN to GTIN-14
- `validate_gtin_check_digit()` - Validate GTIN

### `entity_builder.py`
Build JSON-LD entities:
- `EntityBuilder.build_product()` - Create Product entity
- `EntityBuilder.build_organization()` - Create Organization
- `EntityBuilder.build_webpage()` - Create WebPage
- `create_product_from_scraped_data()` - Auto-map scraped fields

### `entity_reuse.py`
Prevent duplicate entities:
- `EntityReuseManager.get_or_create_organization()` - Reuse organizations
- `EntityReuseManager.get_or_create_person()` - Reuse people
- `EntityReuseManager.get_or_create_brand()` - Reuse brands
- `EntityReuseManager.preload_cache()` - Load existing entities for fast lookup
- `EntityReuseManager.get_existing_entities_by_type()` - Query entities by type

### `shacl_validator.py`
Validate data quality:
- `SHACLValidator.validate()` - Validate single entity
- `SHACLValidator.validate_batch()` - Validate multiple entities
- `SHACLValidator.get_validation_report()` - Generate report
- `validate_before_upload()` - Filter valid/invalid entities

### `wordlift_client.py`
Interact with WordLift APIs:
- `import_from_sitemap()` - Import from sitemap.xml
- `import_from_urls()` - Import specific URLs
- `graphql_query()` - Execute GraphQL queries
- `create_or_update_entity()` - Upsert single entity
- `batch_create_or_update()` - Batch operations
- `patch_entity()` - Incremental updates
- `get_products()`, `get_all_product_gtins()` - Query helpers

### `markup_validator.py`
Validate JSON-LD markup:
- `MarkupValidator.validate()` - Validate single markup
- `MarkupValidator.validate_batch()` - Validate multiple markups
- `validate_json_ld_string()` - Validate JSON-LD from string

### `kg_sync.py`
Orchestrate sync workflows:
- `KGSyncOrchestrator.sync_products()` - Full sync
- `KGSyncOrchestrator.incremental_update()` - PATCH-based sync
- Command-line interface for daily automation
- Flags: `--no-validation`, `--no-reuse` to disable features

### `extract_products.py`
Extract products from data sources:
- `extract_from_database()` - PostgreSQL example
- `extract_from_csv()` - CSV file parsing
- `extract_from_json()` - JSON file parsing
- `extract_from_api()` - REST API example
- `extract_from_shopify()` - Shopify integration
- `extract_from_woocommerce()` - WooCommerce integration

## Dataset URI Structure

WordLift uses account-specific base URIs:

**Format**: `https://data.wordlift.io/wl{account_id}/`

**Examples**:
- Staging: `https://data.wordlift.io/wl1505540/`
- Production: `https://data.wordlift.io/wl1506865/`

All entity IDs are prefixed with this base URI.

## Entity ID Patterns

### Products
`{dataset_uri}/01/{GTIN-14}[/21/{serial}][/10/{lot}]`

### Organizations
`{dataset_uri}/organization/{slug}`

### People
`{dataset_uri}/person/{slug}`

### Web Pages
`{dataset_uri}/webpage/{slug}`

Note: The @id uses this pattern, while the actual page URL is stored in the `url` property.

### Services
`{dataset_uri}/service/{slug}`

### States/Locations
`{dataset_uri}/state/{slug}`

## Error Handling

### Sitemap Import Errors

```python
try:
    results = client.import_from_sitemap(sitemap_url)
    print(f"Successfully imported {len(results)} pages")
except requests.HTTPError as e:
    print(f"Import failed: {e.response.status_code}")
    print(f"Details: {e.response.text}")
```

### Markup Validation Errors

```python
is_valid, errors, markup = validate_markup_from_agent(agent_output)

if not is_valid:
    print("Validation errors:")
    for error in errors:
        print(f"  - {error}")
    # Fix errors before uploading
```

### Invalid GTIN

```python
from scripts.id_generator import normalize_gtin

try:
    gtin_14 = normalize_gtin(user_input)
except ValueError as e:
    print(f"Invalid GTIN: {e}")
```

## Best Practices

1. **Dataset URI**: Use your WordLift account URI (`https://data.wordlift.io/wl{account_id}/`)
2. **IRI Patterns**: ONLY use recognized patterns (organization, place, person, destination, article, etc.)
3. **Always Verify**: Verify entity persistence after creation (API returns 200 OK even for invalid IRIs)
4. **Template Configuration**: ALWAYS configure and validate markup template on sample pages before bulk imports
5. **Entity Reuse**: Always enable entity reuse to prevent duplicate Organizations, Brands, and People
6. **Preload Cache**: Call `reuse_manager.preload_cache()` at start for performance
7. **SHACL Validation**: Always validate entities before upload (enabled by default)
8. **GTIN Quality**: Validate GTINs before sync to prevent ID conflicts
9. **Slug Uniqueness**: Ensure natural keys generate unique slugs
10. **Batch Sizing**: Start with batch_size=50, adjust based on success rate
11. **Validation Mode**: Use strict mode in production for high-quality data
12. **Incremental Syncs**: Use PATCH for daily updates when <20% of products change
13. **Structural Changes**: Use Entity Upgrader (not PATCH) for type changes and complex updates
14. **Monitoring**: Track sync statistics, reuse rates, and validation results
15. **Query After Import**: Verify entity counts after sitemap import
16. **Test Before Bulk**: Import 10-20 pages first to verify configuration
17. **Custom Data**: Use `additionalProperty` instead of custom namespaces

## Common Issues

**Q: Why use Sitemap Import API instead of scraping?**
A: The Sitemap Import API is the recommended way to jumpstart a Knowledge Graph. It:
- Handles pagination and large sitemaps
- Returns structured NDJSON responses
- Automatically extracts structured data from pages
- Respects robots.txt and rate limits

**Q: How do slug-based IDs work?**
A: Slugs are URL-friendly versions of natural keys:
- "Acme Corporation" → "acme-corporation"
- "New York" → "new-york"
- "John Doe" → "john-doe"

This makes IDs human-readable and predictable.

**Q: When to use GS1 Digital Link vs slug-based IDs?**
A: Use GS1 Digital Link ONLY for products with GTINs. Use slug-based IDs for:
- Organizations
- People
- Locations
- Services
- Other non-product entities

**Q: Why is entity reuse important?**
A: Without entity reuse, you create duplicate entities:
- Brand "Nike" created 100 times (once per product)
- Publisher "Acme Corp" created 50 times (once per article)
- Author "John Doe" created 30 times (once per blog post)

Entity reuse via GraphQL ensures you reference the same entity IRI, maintaining data integrity.

**Q: How do I know if entities are being reused?**
A: Check the sync output:
```
✓ Reusing existing brand: Nike
+ Creating new brand: Adidas
✓ Reusing existing organization: Acme Corp
```

Also track reuse statistics in your logs.

**Q: What happens if validation fails?**
A: Invalid entities are filtered out and not uploaded. Check the validation report:
```
✗ Product missing required field: gtin14
✗ Offer: Missing required field: priceCurrency
```

Fix the errors and re-run the sync.

**Q: How do I create JSON-LD markup?**
A: Use the `EntityBuilder` to create entities programmatically:
```python
from scripts.entity_builder import EntityBuilder
builder = EntityBuilder(dataset_uri)
product = builder.build_product({...})
```
Always validate with `SHACLValidator` before uploading.

**Q: Why does the API return 200 OK but my entity isn't persisted?**
A: WordLift requires specific IRI path patterns. The API accepts invalid patterns (returns 200 OK) but doesn't persist them. Always:
1. Use recognized patterns (organization, place, person, destination, etc.)
2. Verify with `verify_entity_persisted()` after creation
3. Check `.html` and `.json` endpoints are accessible

See `references/iri-patterns-and-verification.md` for details.

**Q: When should I use Entity Upgrader vs PATCH?**
A: Use Entity Upgrader (`entity_upgrader.py`) for:
- Changing entity types (WebPage → Article)
- Adding complex nested properties (author, publisher)
- Post-import cleanup/enrichment

Use PATCH (`patch_entity()`) for:
- Daily price/availability updates
- Simple field changes
- Large catalogs with <20% daily changes

**Q: What if sitemap has >1000 URLs?**
A: The Sitemap Import API handles large sitemaps automatically. Monitor the NDJSON response to track progress.

## Dependencies

```bash
pip install requests --break-system-packages
```

No additional dependencies needed.