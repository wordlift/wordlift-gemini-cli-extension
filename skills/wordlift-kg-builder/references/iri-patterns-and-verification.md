# IRI Patterns and Entity Verification

## ⚠️ Critical: Silent Failure Warning

WordLift's API will **accept invalid IRI patterns** and return `200 OK`, but **entities will NOT be persisted**. Always verify entity persistence after creation.

---

## Valid IRI Path Patterns

WordLift requires specific path patterns for entities. Only these patterns are guaranteed to persist:

| Entity Type | Pattern | Example |
|------------|---------|---------|
| **Products** | `/01/{GTIN-14}` | `https://data.wordlift.io/wl123/01/12345678901234` |
| **Organizations** | `/organization/{slug}` | `https://data.wordlift.io/wl123/organization/acme-corp` |
| **Places** | `/place/{slug}` | `https://data.wordlift.io/wl123/place/italy` |
| **People** | `/person/{slug}` | `https://data.wordlift.io/wl123/person/john-doe` |
| **Tourist Destinations** | `/destination/{slug}` | `https://data.wordlift.io/wl123/destination/venice` |
| **Articles** | `/article/{slug}` | `https://data.wordlift.io/wl123/article/news-story` |
| **WebPages** | `/webpage/{slug}` | `https://data.wordlift.io/wl123/webpage/about-us` |
| **Brands** | `/brand/{slug}` | `https://data.wordlift.io/wl123/brand/nike` |
| **Events** | `/event/{slug}` | `https://data.wordlift.io/wl123/event/conference-2024` |
| **Services** | `/service/{slug}` | `https://data.wordlift.io/wl123/service/consulting` |

---

## Invalid IRI Patterns (Silent Failures)

These patterns will be **accepted by the API (200 OK) but NOT persisted**:

### ❌ Auto-generated paths from sitemap import
```
https://data.wordlift.io/wl123/sejour/country/destination-name
https://data.wordlift.io/wl123/auto/generated/path/entity
```

### ❌ Arbitrary nested paths
```
https://data.wordlift.io/wl123/custom/nested/path/entity
https://data.wordlift.io/wl123/my/special/structure/item
```

### ❌ Paths that don't match recognized patterns
```
https://data.wordlift.io/wl123/mytype/entity-name
https://data.wordlift.io/wl123/customclass/some-slug
```

### ❌ Too many path segments
```
https://data.wordlift.io/wl123/organization/department/team/person
```

---

## Entity Verification Methods

### Method 1: Check Dereferenceability (Fastest)

```python
from scripts.entity_verifier import verify_entity_persisted

iri = "https://data.wordlift.io/wl123/destination/venice"

is_persisted, message = verify_entity_persisted(iri, wait_seconds=2)

if is_persisted:
    print("✓ Entity persisted successfully")
else:
    print(f"✗ Entity NOT persisted: {message}")
```

**What it checks:**
1. `.html` endpoint is accessible
2. `.html` page doesn't contain "No local triples"
3. `.json` endpoint returns data

**Speed:** 2-5 seconds

### Method 2: Check GraphQL Index (Slower but comprehensive)

```python
from scripts.entity_verifier import verify_via_graphql
from scripts.wordlift_client import WordLiftClient

client = WordLiftClient(api_key)

is_indexed, message, entity = verify_via_graphql(
    client,
    iri,
    wait_seconds=10
)

if is_indexed:
    print(f"✓ Entity indexed: {entity['name']}")
else:
    print(f"⚠️  {message}")
```

**What it checks:**
- Entity is queryable via GraphQL
- Entity has name and type data

**Speed:** 5-60 seconds (indexing delay)

**Note:** GraphQL indexing is asynchronous and can take 1-5 minutes.

### Method 3: Complete Verification Suite

```python
from scripts.entity_verifier import verify_entity_complete

results = verify_entity_complete(client, iri, check_graphql=True)

print(f"Persisted: {results['persisted']}")
print(f"Dereferenceable: {results['dereferenceable']}")
print(f"GraphQL Indexed: {results['graphql_indexed']}")

for msg in results['messages']:
    print(f"  {msg}")
```

**Runs all checks:**
- Dereferenceability (.html/.json)
- GraphQL indexing
- Returns detailed messages

---

## Recommended Verification Workflow

### Step 1: Create Entity

```python
from scripts.entity_builder import EntityBuilder
from scripts.wordlift_client import WordLiftClient

client = WordLiftClient(api_key)
builder = EntityBuilder("https://data.wordlift.io/wl123")

# Create entity
entity = builder.build_organization({
    'name': 'Venice Tourism Board',
    'url': 'https://venice-tourism.com'
})

# Upload
client.create_or_update_entity(entity)
iri = entity['@id']
```

### Step 2: Immediate Verification (2 seconds)

```python
from scripts.entity_verifier import verify_entity_persisted

is_persisted, message = verify_entity_persisted(iri, wait_seconds=2)

if not is_persisted:
    print(f"⚠️  CRITICAL: Entity not persisted!")
    print(f"   Reason: {message}")
    print(f"   IRI: {iri}")
    print(f"   Check IRI pattern is valid")
    # Handle failure - retry with correct IRI pattern
```

### Step 3: Verify IRI Pattern

```python
from scripts.entity_verifier import check_iri_pattern

is_valid, pattern_msg = check_iri_pattern(iri)

if not is_valid:
    print(f"⚠️  Invalid IRI pattern: {pattern_msg}")
    print(f"   This IRI will NOT be persisted")
```

### Step 4: GraphQL Verification (Optional, 10+ seconds)

```python
from scripts.entity_verifier import verify_via_graphql

# Wait for indexing
is_indexed, msg, entity = verify_via_graphql(client, iri, wait_seconds=10)

if is_indexed:
    print(f"✓ Entity fully indexed")
else:
    print(f"ℹ️  Not yet indexed (may take 1-5 minutes)")
```

---

## Command-Line Verification

```bash
# Quick verification
python scripts/entity_verifier.py <IRI>

# With GraphQL check
python scripts/entity_verifier.py <IRI> <API_KEY>
```

**Example:**
```bash
python scripts/entity_verifier.py \
  https://data.wordlift.io/wl123/destination/venice \
  your_api_key
```

**Output:**
```
Verifying entity: https://data.wordlift.io/wl123/destination/venice

IRI Pattern: Valid IRI pattern: /destination/

Checking dereferenceability...
Result: Entity successfully persisted and dereferenceable
✓ Entity is persisted and dereferenceable

Checking GraphQL indexing...
Result: Entity indexed in GraphQL
  Entity: Venice Tourism Board
  Types: ['http://schema.org/TouristDestination']
```

---

## Batch Verification

```python
from scripts.entity_verifier import verify_entity_persisted

# Verify multiple entities
iris = [
    "https://data.wordlift.io/wl123/destination/venice",
    "https://data.wordlift.io/wl123/destination/florence",
    "https://data.wordlift.io/wl123/destination/rome"
]

results = {
    'persisted': [],
    'failed': []
}

for iri in iris:
    is_persisted, msg = verify_entity_persisted(iri)

    if is_persisted:
        results['persisted'].append(iri)
    else:
        results['failed'].append((iri, msg))

print(f"✓ Persisted: {len(results['persisted'])}/{len(iris)}")

if results['failed']:
    print(f"✗ Failed: {len(results['failed'])}")
    for iri, msg in results['failed']:
        print(f"  {iri}: {msg}")
```

---

## Custom Namespace Limitations

### Issue

Using custom namespaces can cause problems:

```python
# ❌ Might cause issues
entity = {
    "@context": {
        "schema": "https://schema.org/",
        "seovoc": "https://w3id.org/seovoc/"
    },
    "seovoc:markdownText": "markdown content"
}
```

### Recommended Approach

Use standard schema.org with `additionalProperty`:

```python
# ✅ Better approach
entity = {
    "@context": "https://schema.org",
    "@type": "Article",
    "@id": "https://data.wordlift.io/wl123/article/my-article",
    "name": "Article Title",
    "additionalProperty": {
        "@type": "PropertyValue",
        "name": "markdownText",
        "value": "markdown content"
    }
}
```

**Benefits:**
- Avoids namespace conflicts
- Standard schema.org only
- Works reliably
- Easy to query

---

## Indexing Delays

### Timeline

| Verification Method | Typical Delay |
|--------------------|---------------|
| `.html` endpoint | Immediate - 5 seconds |
| `.json` endpoint | Immediate - 5 seconds |
| GraphQL query | 10 seconds - 5 minutes |

### Handling Delays

```python
import time

# Create entity
client.create_or_update_entity(entity)
iri = entity['@id']

# Immediate check (dereferenceability)
is_persisted, msg = verify_entity_persisted(iri, wait_seconds=2)

if not is_persisted:
    print("⚠️  Entity not persisted - check IRI pattern!")
    # Handle error
    sys.exit(1)

print("✓ Entity persisted")

# For GraphQL queries, wait longer
print("Waiting for GraphQL indexing...")
for attempt in range(6):  # Try 6 times over 60 seconds
    time.sleep(10)
    is_indexed, msg, entity = verify_via_graphql(client, iri, wait_seconds=0)

    if is_indexed:
        print("✓ Entity indexed in GraphQL")
        break

    print(f"  Attempt {attempt + 1}/6: Not yet indexed")
else:
    print("⚠️  Entity not indexed after 60 seconds")
    print("   This may be normal for large batches")
```

---

## Common Pitfalls

### Pitfall 1: Trusting 200 OK Response

```python
# ❌ BAD: Assuming success from HTTP status
response = client.create_or_update_entity(entity)
# Returns 200 OK even if IRI pattern is invalid!

# ✅ GOOD: Always verify
response = client.create_or_update_entity(entity)
is_persisted, msg = verify_entity_persisted(entity['@id'])
if not is_persisted:
    raise Exception(f"Entity not persisted: {msg}")
```

### Pitfall 2: Using Auto-Generated Paths

```python
# ❌ BAD: Path from sitemap import
iri = "https://data.wordlift.io/wl123/sejour/country/venice"
# This will NOT be persisted!

# ✅ GOOD: Use recognized pattern
iri = "https://data.wordlift.io/wl123/destination/venice"
```

### Pitfall 3: Not Validating IRI Pattern First

```python
# ❌ BAD: Create without checking pattern
iri = f"{dataset_uri}/customtype/{slug}"
entity = {'@id': iri, ...}
client.create_or_update_entity(entity)

# ✅ GOOD: Validate pattern first
from scripts.entity_verifier import check_iri_pattern

is_valid, msg = check_iri_pattern(iri)
if not is_valid:
    raise ValueError(f"Invalid IRI pattern: {msg}")

entity = {'@id': iri, ...}
client.create_or_update_entity(entity)
```

### Pitfall 4: Immediate GraphQL Query

```python
# ❌ BAD: Query immediately after creation
client.create_or_update_entity(entity)
result = client.graphql_query(...)  # May not be indexed yet

# ✅ GOOD: Wait for indexing or use dereferenceability check
client.create_or_update_entity(entity)

# Option 1: Check dereferenceability (immediate)
is_persisted, msg = verify_entity_persisted(entity['@id'])

# Option 2: Wait for GraphQL indexing
time.sleep(10)
result = client.graphql_query(...)
```

---

## Best Practices Checklist

- [ ] Use only recognized IRI path patterns
- [ ] Validate IRI pattern before entity creation
- [ ] Verify entity persistence after creation
- [ ] Use dereferenceability check for immediate verification
- [ ] Wait 10+ seconds before GraphQL queries
- [ ] Batch verify entities after bulk operations
- [ ] Log failed entities for investigation
- [ ] Use `additionalProperty` for custom data
- [ ] Keep `@context` simple (single string, not object)
- [ ] Always use `generate_entity_id()` for non-products
- [ ] Always use `generate_product_id()` for products

---

## Troubleshooting

### Issue: Entity Returns 200 OK but Not Persisted

**Symptom:**
```
POST /dataset returns 200 OK
But .html shows "No local triples"
```

**Cause:** Invalid IRI pattern

**Solution:**
1. Check IRI pattern with `check_iri_pattern()`
2. Use recognized pattern from valid patterns table
3. Recreate entity with correct IRI

### Issue: GraphQL Returns null

**Symptom:**
```python
result = client.graphql_query(...)
# Returns: {'data': {'entity': None}}
```

**Causes:**
1. Entity not yet indexed (wait longer)
2. Entity not persisted (check dereferenceability)
3. Wrong IRI in query

**Solution:**
1. Check dereferenceability first
2. Wait 10+ seconds for indexing
3. Verify IRI is correct

### Issue: Custom Properties Not Working

**Symptom:**
```python
entity = {
    "@context": {"custom": "..."},
    "custom:field": "value"
}
# Property not persisted
```

**Solution:** Use `additionalProperty`:
```python
entity = {
    "@context": "https://schema.org",
    "additionalProperty": {
        "@type": "PropertyValue",
        "name": "field",
        "value": "value"
    }
}
```

---

## Summary

✅ **Always verify entity persistence** - Don't trust 200 OK
✅ **Use recognized IRI patterns only** - Check valid patterns table
✅ **Validate patterns before creation** - Use `check_iri_pattern()`
✅ **Check dereferenceability immediately** - 2 seconds for quick check
✅ **Wait for GraphQL indexing** - 10+ seconds minimum
✅ **Use additionalProperty for custom data** - Avoid custom namespaces
✅ **Batch verify after bulk operations** - Don't assume success

Following these practices will prevent silent failures and ensure your entities are actually persisted in the Knowledge Graph!