# WordLift Knowledge Graph Builder & Gemini CLI Extension

This extension allows you to build and maintain Knowledge Graphs directly from Gemini CLI using WordLift APIs. It handles everything from sitemap imports to GS1 Digital Link generation and SHACL validation.

## Installation

Install the extension directly from GitHub:

```bash
gemini extensions install https://github.com/wordlift/wordlift-gemini-cli-extension.git
```

The installation script will automatically set up the Python environment and dependencies.

### Configuration

After installation, configure the extension with your WordLift credentials:

1. Navigate to the extension directory:
   ```bash
   cd ~/.gemini/extensions/wordlift-gemini-cli-extension
   ```

2. Create a `.env` file with your credentials:
   ```env
   WORDLIFT_API_KEY=your_api_key_here
   WORDLIFT_BASE_URI=https://data.wordlift.io/wl123
   WORDLIFT_API_ENDPOINT=https://api.wordlift.io
   ```

3. Replace `your_api_key_here` with your actual WordLift API key
4. Replace `wl123` with your WordLift account dataset identifier

## Core Features

### 1. Knowledge Graph Building
- **`import_from_sitemap`**: Import URLs from sitemap.xml to jumpstart your Knowledge Graph.
- **`import_from_urls`**: Import specific URL lists for immediate processing.
- **`build_product`**: Create schema.org Product entities with GS1 Digital Link identifiers (`{dataset_uri}/01/{GTIN-14}`).
- **`build_organization`**: Create Organization entities with slug-based IDs.
- **`build_webpage`**: Create WebPage entities with proper slug patterns.

### 2. Data Quality & Sync
- **`validate_entity`**: Validate entities against SHACL shapes for Products, Organizations, and WebPages.
- **`sync_kg`**: Perform batch create/update operations or incremental PATCH updates for daily sync workflows.
- **`create_or_update_entities`**: Upsert entities using JSON-LD or Turtle content.

### 3. Entity Management
- **`get_entity`**: Retrieve specific entities by their IRI.
- **`delete_entities`**: Remove entities from the Knowledge Graph.

## Prerequisites

- Python 3.10+
- WordLift API Key
- WordLift Dataset URI (`https://data.wordlift.io/wl{account_id}/`)

## Usage Examples

### Import from Sitemap
```
Import all pages from https://example.com/sitemap.xml into my WordLift KG
```

### Build and Sync Products
You can ask Gemini to build a product from raw data:
```
Build a product for a Nike Air Max with GTIN 12345678901231, price 120 USD and in stock.
Then validate it and sync it to WordLift.
```

### Batch Sync
```
Sync the following products to my Knowledge Graph:
[
  {"gtin": "12345678901231", "name": "Product 1", "price": "29.99"},
  {"gtin": "09876543210987", "name": "Product 2", "price": "49.99"}
]
```

## API Methods Reference

### Knowledge Graph Building

#### `import_from_sitemap(sitemap_url)`
Starts a sitemap import task and returns the number of imported pages.

#### `build_product(data_json)`
Converts a JSON object into a valid schema.org Product JSON-LD with a GS1 Digital Link ID.

#### `build_organization(data_json)`
Converts a JSON object into a valid Organization entity.

### Validation & Sync

#### `validate_entity(entity_json, strict=False)`
Checks if an entity satisfies SHACL shape requirements (e.g., GHIN-14 for products).

#### `sync_kg(products_json, incremental=False)`
Efficiently uploads multiple products. If `incremental=True`, it uses JSON Patch to only update changed fields.

## Detailed Documentation

For more in-depth guides and specific workflows, refer to the documentation in the [references/](file:///Users/cyberandy/wordlift-gemini-cli-extension/references) directory:

- [Workflows](file:///Users/cyberandy/wordlift-gemini-cli-extension/references/workflows.md): Detailed sync and import patterns
- [Entity Reuse & Validation](file:///Users/cyberandy/wordlift-gemini-cli-extension/references/entity-reuse-and-shacl-validation.md): How to prevent duplicates and ensure data quality
- [GraphQL Queries](file:///Users/cyberandy/wordlift-gemini-cli-extension/references/graphql_queries.md): Common query patterns for your Knowledge Graph
- [Scheduling](file:///Users/cyberandy/wordlift-gemini-cli-extension/references/scheduling.md): How to automate your syncs with Cron or GitHub Actions
- [Template Configuration](file:///Users/cyberandy/wordlift-gemini-cli-extension/references/template-configuration.md): Guide to configuring markup templates for bulk imports

## Testing

You can verify the core logic (ID generation, entity building, and SHACL validation) using the included dry-run test script:

```bash
python3 scripts/dry_run_test.py
```

This test does not require an API key and performs a series of offline checks to ensure the extension is working correctly.

## Architecture

This extension leverages several core scripts located in the `scripts/` directory:
- `id_generator.py`: Generates GS1 Digital Link and slug-based IDs.
- `entity_builder.py`: Constructs schema.org JSON-LD.
- `shacl_validator.py`: Validates data quality.
- `kg_sync.py`: Orchestrates sync workflows.
- `wordlift_client.py`: High-level wrapper for WordLift APIs.

## Support

For WordLift API documentation, visit: [docs.wordlift.io](https://docs.wordlift.io/)
