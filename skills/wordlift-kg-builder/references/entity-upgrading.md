# Entity Upgrading Guide

## Why Entity Upgrader?

### The Problem with PATCH

JSON PATCH (RFC 6902) has limitations when modifying entities:

❌ **Cannot change @type** - PATCH operations like `{"op": "replace", "path": "/@type", "value": "Article"}` don't work reliably
❌ **Complex nested updates** - Updating nested objects (like author) is error-prone
❌ **Partial failures** - If one PATCH operation fails, the entire batch fails
❌ **Type validation** - KG may reject type changes via PATCH

### The Solution: Fetch-Modify-Update

✅ **Fetch** - Get current entity data via GraphQL
✅ **Modify** - Change type, add/update properties in memory
✅ **Update** - Send complete entity via PUT/create_or_update_entity

This pattern:
- ✅ Safely changes entity types
- ✅ Preserves existing properties
- ✅ Handles complex nested updates
- ✅ Validates entire entity before upload
- ✅ More reliable for structural changes

---

## When to Use Each Approach

### Use PATCH For:
- ✅ Simple field updates (price, availability)
- ✅ Incremental daily syncs with <20% changes
- ✅ Large catalogs (1000+ products)
- ✅ Same entity type, just data changes

### Use Entity Upgrader For:
- ✅ Changing entity types (WebPage → Article)
- ✅ Adding complex nested properties (author, publisher)
- ✅ Structural changes to entities
- ✅ Post-import cleanup/enrichment
- ✅ Small to medium updates (1-100 entities)

---

## Usage Examples

### Example 1: Change Entity Type

**Scenario:** You imported 700 pages as `WebPage`, but they should be `Article`.

```bash
# Single entity
python scripts/entity_upgrader.py \
  https://data.wordlift.io/wl92832/webpage/my-post \
  --type Article
```

**Output:**
```
Fetching entity: https://data.wordlift.io/wl92832/webpage/my-post...
✓ Entity found: My Blog Post
  Changing type to: Article
  Preserved 4 existing properties

Updating entity...
✓ Successfully updated https://data.wordlift.io/wl92832/webpage/my-post

Final entity:
  Type: Article
  Properties: 5
```

### Example 2: Add Author to Entities

**Scenario:** Your imported pages don't have authors. Add them.

```bash
python scripts/entity_upgrader.py \
  https://data.wordlift.io/wl92832/webpage/my-post \
  --props '{"author": {"@type": "Person", "@id": "https://data.wordlift.io/wl92832/person/john-doe", "name": "John Doe"}}'
```

**Output:**
```
Fetching entity: https://data.wordlift.io/wl92832/webpage/my-post...
✓ Entity found: My Blog Post
  Preserved 4 existing properties
  Adding 1 new properties: ['author']

Updating entity...
✓ Successfully updated

Final entity:
  Type: Article
  Properties: 6
```

### Example 3: Change Type AND Add Properties

**Scenario:** Upgrade WebPage to Article and add author.

```bash
python scripts/entity_upgrader.py \
  https://data.wordlift.io/wl92832/webpage/my-post \
  --type Article \
  --props '{"author": {"@type": "Person", "name": "John Doe"}, "headline": "Updated Headline"}'
```

### Example 4: Batch Upgrade from File

**Scenario:** Upgrade 100 WebPages to Articles.

**Step 1:** Get IRIs via GraphQL
```python
from scripts.wordlift_client import WordLiftClient

client = WordLiftClient(api_key)

result = client.graphql_query("""
  query {
    entities(
      query: { typeConstraint: { in: ["http://schema.org/WebPage"] } }
      rows: 100
    ) {
      iri
    }
  }
""")

# Save to file
with open('webpages.txt', 'w') as f:
    for entity in result['entities']:
        f.write(entity['iri'] + '\n')
```

**Step 2:** Batch upgrade
```bash
python scripts/entity_upgrader.py \
  --batch-file webpages.txt \
  --type Article
```

**Output:**
```
============================================================
BATCH UPGRADE: 100 entities
============================================================

[1/100] Processing https://data.wordlift.io/wl92832/webpage/post-1
------------------------------------------------------------
✓ Successfully updated

[2/100] Processing https://data.wordlift.io/wl92832/webpage/post-2
------------------------------------------------------------
✓ Successfully updated

...

[100/100] Processing https://data.wordlift.io/wl92832/webpage/post-100
------------------------------------------------------------
✓ Successfully updated

============================================================
BATCH COMPLETE
============================================================
Total: 100
Success: 100
Failed: 0
```

---

## Common Upgrade Scenarios

### Scenario 1: Post-Import Type Correction

You imported pages from sitemap, but they're all `WebPage`. Make them more specific.

**Query to find entities:**
```graphql
query {
  entities(
    query: {
      typeConstraint: { in: ["http://schema.org/WebPage"] }
      urlConstraint: { regex: { pattern: "^/blog/" } }
    }
    rows: 1000
  ) {
    iri
    url: string(name: "schema:url")
  }
}
```

**Upgrade:**
```bash
# Save blog IRIs to file
# Then upgrade
python scripts/entity_upgrader.py \
  --batch-file blog-pages.txt \
  --type BlogPosting
```

### Scenario 2: Add Missing Publisher

Your articles don't have a publisher. Add it.

**Upgrade:**
```bash
python scripts/entity_upgrader.py \
  https://data.wordlift.io/wl92832/webpage/article-1 \
  --props '{"publisher": {"@type": "Organization", "@id": "https://data.wordlift.io/wl92832/organization/my-company", "name": "My Company", "url": "https://mysite.com"}}'
```

### Scenario 3: Enrich Product Data

Add brand and availability to products.

```bash
python scripts/entity_upgrader.py \
  https://data.wordlift.io/wl92832/01/12345678901231 \
  --props '{"brand": {"@type": "Brand", "name": "Nike"}, "offers": {"@type": "Offer", "availability": "https://schema.org/InStock"}}'
```

### Scenario 4: Fix Incorrect IDs

If entities were created with wrong IDs, you can't change the @id. Instead:

1. Create new entity with correct ID
2. Delete old entity

```python
from scripts.entity_builder import EntityBuilder
from scripts.wordlift_client import WordLiftClient

client = WordLiftClient(api_key)
builder = EntityBuilder(dataset_uri)

# Create new entity with correct ID
new_entity = builder.build_webpage({
    'url': 'https://mysite.com/page',
    'name': 'Page Title',
    'description': 'Description'
})

client.create_or_update_entity(new_entity)

# Delete old entity (if needed)
# Note: Delete API may require specific permissions
```

---

## Script Options

### Required Arguments

```bash
# Single entity
python scripts/entity_upgrader.py <IRI>

# Batch from file
python scripts/entity_upgrader.py --batch-file <FILE>
```

### Optional Arguments

```
--type TYPE           New Schema.org type (e.g., Article, Product)
--props JSON          JSON object of properties to add/update
--api-key KEY         WordLift API key (or use WORDLIFT_API_KEY env var)
```

### Environment Variables

```bash
export WORDLIFT_API_KEY=your_key_here
python scripts/entity_upgrader.py <IRI> --type Article
```

---

## Advanced Usage

### Add Complex Nested Objects

```bash
python scripts/entity_upgrader.py \
  https://data.wordlift.io/wl92832/webpage/recipe \
  --type Recipe \
  --props '{
    "author": {
      "@type": "Person",
      "@id": "https://data.wordlift.io/wl92832/person/chef-john",
      "name": "Chef John"
    },
    "recipeIngredient": ["flour", "sugar", "eggs"],
    "recipeInstructions": "Mix and bake",
    "prepTime": "PT30M",
    "cookTime": "PT1H"
  }'
```

### Programmatic Batch Upgrade

```python
from scripts.entity_upgrader import upgrade_batch
from scripts.wordlift_client import WordLiftClient

client = WordLiftClient(api_key)

# Get IRIs to upgrade
result = client.graphql_query("""
  query {
    entities(query: { typeConstraint: { in: ["http://schema.org/WebPage"] } }) {
      iri
    }
  }
""")

iris = [e['iri'] for e in result['entities']]

# Batch upgrade
stats = upgrade_batch(
    client,
    iris,
    new_type="Article",
    new_props={
        "publisher": {
            "@type": "Organization",
            "name": "My Company"
        }
    }
)

print(f"Success: {stats['success']}/{stats['total']}")
```

---

## Performance Considerations

### Single Entity Upgrade
- **Time:** ~1-2 seconds per entity
- **Use for:** 1-10 entities, one-off fixes

### Batch Upgrade
- **Time:** ~1-2 seconds per entity (sequential)
- **Optimal batch size:** 50-100 entities
- **Use for:** Bulk corrections, post-import cleanup

### Large Scale (1000+ entities)
For very large batches:

```python
# Process in chunks
chunk_size = 100

for i in range(0, len(all_iris), chunk_size):
    chunk = all_iris[i:i+chunk_size]
    print(f"\nProcessing chunk {i//chunk_size + 1}...")

    stats = upgrade_batch(client, chunk, new_type="Article")

    print(f"Chunk complete: {stats['success']}/{stats['total']}")
```

---

## Troubleshooting

### Issue: Entity Not Found

**Error:**
```
Entity not found: https://data.wordlift.io/wl92832/webpage/missing
```

**Solution:**
Verify the IRI exists:
```graphql
query {
  resource(iri: "https://data.wordlift.io/wl92832/webpage/missing") {
    iri
  }
}
```

### Issue: Update Failed

**Error:**
```
Update failed: 400 Bad Request
```

**Causes:**
1. Invalid JSON in `--props`
2. Required fields missing for new type
3. Invalid property values

**Solution:**
1. Validate JSON: `echo '{"test": "value"}' | python -m json.tool`
2. Check required fields for type
3. Test with single entity first

### Issue: Properties Not Preserved

**Symptom:** After upgrade, some fields are missing.

**Cause:** Query in `upgrade_entity` doesn't fetch all fields.

**Solution:** Modify the GraphQL query in `entity_upgrader.py`:
```python
query = """
query($iri: Ref!) {
  resource(iri: $iri) {
    iri
    name: string(name: "schema:name")
    description: string(name: "schema:description")
    # Add more fields here
    customField: string(name: "schema:customField")
  }
}
"""
```

---

## Best Practices

1. **Test First** - Upgrade 1-2 entities and verify before batch
2. **Query Before** - Confirm entities exist before upgrading
3. **Verify After** - Query KG to confirm changes applied
4. **Backup Strategy** - Export data before large batch upgrades
5. **Incremental Batches** - Process in chunks (50-100 at a time)
6. **Error Handling** - Check stats and retry failures
7. **Preserve Data** - Always fetch existing properties first

---

## Comparison: PATCH vs Upgrader

| Feature | PATCH | Upgrader |
|---------|-------|----------|
| Change @type | ❌ No | ✅ Yes |
| Add nested objects | ⚠️ Limited | ✅ Yes |
| Preserve properties | ⚠️ Manual | ✅ Automatic |
| Large batches (1000+) | ✅ Fast | ⚠️ Slower |
| Structural changes | ❌ No | ✅ Yes |
| Simple field updates | ✅ Efficient | ⚠️ Overkill |
| Type safety | ⚠️ Limited | ✅ Full validation |

---

## Summary

✅ **Entity Upgrader** is essential for:
- Changing entity types post-import
- Adding complex nested properties
- Structural modifications
- Post-import cleanup

✅ **Fetch-Modify-Update** pattern:
- Safer than PATCH for type changes
- Preserves existing data automatically
- Handles complex updates reliably

✅ **Use cases**:
- WebPage → Article conversion
- Adding authors/publishers
- Enriching imported data
- Fixing structural issues

The Entity Upgrader complements PATCH - use Upgrader for structural changes, PATCH for daily data syncs!