# Template Configuration Workflow

Before importing hundreds or thousands of pages, it's critical to establish the right markup template. This workflow helps you validate and configure the template using sample pages.

## Why Template Configuration?

Without template configuration:
- ❌ Import 700 pages with wrong @type (WebPage instead of Article)
- ❌ Miss critical properties (author, publisher, datePublished)
- ❌ Generate incorrect entity IDs
- ❌ Have to delete and re-import everything

With template configuration:
- ✅ Analyze 2-3 sample pages first
- ✅ Validate markup structure
- ✅ Get user approval
- ✅ Apply correct template to all pages
- ✅ One-time import, done right

## Workflow Steps

### Step 1: Select Sample Pages

Choose 2-3 representative pages from your sitemap:

```python
sample_urls = [
    "https://example.com/blog/post-1",      # Blog post
    "https://example.com/blog/post-2",      # Another blog post
    "https://example.com/about"             # Static page
]
```

**Tips for selecting samples:**
- Include different content types (blog, product, static page)
- Choose typical pages, not edge cases
- Include pages with all the metadata you want to extract

### Step 2: Run Template Configurator

```python
from scripts.template_configurator import TemplateConfigurator
from scripts.wordlift_client import WordLiftClient

client = WordLiftClient(api_key)
configurator = TemplateConfigurator(client, dataset_uri)

# Analyze samples
analyses = configurator.analyze_sample_pages(sample_urls)
```

**Output:**
```
============================================================
ANALYZING 3 SAMPLE PAGES
============================================================

[1/3] Analyzing: https://example.com/blog/post-1
------------------------------------------------------------
  Detected Type: BlogPosting
  Validation: ✓ VALID
    ⚠ Missing recommended field: image
    ⚠ Missing recommended field: datePublished

[2/3] Analyzing: https://example.com/blog/post-2
------------------------------------------------------------
  Detected Type: BlogPosting
  Validation: ✓ VALID
    ⚠ Missing recommended field: image

[3/3] Analyzing: https://example.com/about
------------------------------------------------------------
  Detected Type: WebPage
  Validation: ✓ VALID
```

### Step 3: Review Configuration Summary

```python
configurator.display_configuration_summary(analyses)
```

**Output:**
```
============================================================
CONFIGURATION SUMMARY
============================================================

Analyzed 3 sample pages
Most common type: BlogPosting

Detected content types:
  • BlogPosting: 2 page(s)
  • WebPage: 1 page(s)

Validation: 3/3 samples valid

Recommendations:
  • Add 'image' property for social sharing
  • Add 'datePublished' for temporal context
  • Consider adding 'author' for content attribution
```

### Step 4: Answer Configuration Questions

The configurator generates questions based on the analysis:

```python
questions = configurator.generate_configuration_questions(analyses)
```

**Questions:**

#### Q1: Entity Type
```
What schema.org type should these pages use?

Detected: BlogPosting
Options:
  - WebPage (generic)
  - Article (news/blog articles)
  - BlogPosting (specifically blog posts)  ← Recommended
  - NewsArticle (news content)

Your choice: [BlogPosting]
```

#### Q2: Author Handling
```
Do your pages have authors?

Options:
  - Yes - Extract and reuse author entities  ← Recommended for blogs
  - No - Skip author
  - Yes - Use organization as author

Your choice: [Yes - Extract and reuse]
```

#### Q3: Publisher Information
```
Publisher/Organization information:

Name: [Your Company Name]
URL: [https://yoursite.com]
Logo: [https://yoursite.com/logo.png]

This will be used for all pages.
```

#### Q4: Metadata Extraction
```
Which metadata properties should be extracted?

☑ headline/name          ← Essential
☑ description            ← Essential
☑ datePublished          ← Recommended
☐ dateModified
☑ image                  ← Recommended
☐ keywords
☐ breadcrumb

Your selections: [headline/name, description, datePublished, image]
```

#### Q5: ID Pattern
```
How should WebPage IDs be generated?

Options:
  - URL slug only (/webpage/about-us)  ← Recommended
  - Full path (/webpage/company/about-us)
  - Custom pattern

Your choice: [URL slug only]
```

### Step 5: Review Proposed Markup

Based on your answers, the configurator shows the final template:

```json
{
  "@context": "https://schema.org",
  "@type": "BlogPosting",
  "@id": "https://data.wordlift.io/wl92832/webpage/{slug}",
  "url": "{page_url}",
  "headline": "{extracted_headline}",
  "description": "{extracted_description}",
  "datePublished": "{extracted_date}",
  "image": "{extracted_image}",
  "author": {
    "@type": "Person",
    "@id": "https://data.wordlift.io/wl92832/person/{author_slug}",
    "name": "{extracted_author}"
  },
  "publisher": {
    "@type": "Organization",
    "@id": "https://data.wordlift.io/wl92832/organization/your-company",
    "name": "Your Company Name",
    "url": "https://yoursite.com",
    "logo": "https://yoursite.com/logo.png"
  }
}
```

### Step 6: Validate Template

```python
from scripts.shacl_validator import SHACLValidator

validator = SHACLValidator()

# Validate the template
is_valid, errors, warnings = validator.validate(template, strict=True)

if is_valid:
    print("✓ Template is valid!")
else:
    print("✗ Template has errors:")
    for error in errors:
        print(f"  - {error}")
```

### Step 7: Approve & Save Template

```python
# Save approved configuration
configurator.save_template(template_config, 'bulk_import_template.json')
```

**Output:**
```
✓ Template configuration saved to: bulk_import_template.json
```

### Step 8: Bulk Import with Approved Template

Now that the template is validated and approved, proceed with bulk import:

```python
from scripts.wordlift_client import WordLiftClient

client = WordLiftClient(api_key)

# Import all pages from sitemap
results = client.import_from_sitemap("https://yoursite.com/sitemap.xml")

print(f"Imported {len(results)} pages")

# Query to verify
result = client.graphql_query("""
  query {
    entities(
      query: { typeConstraint: { in: ["http://schema.org/BlogPosting"] } }
      rows: 10
    ) {
      iri
      headline: string(name: "schema:headline")
      author: resource(name: "schema:author") {
        name: string(name: "schema:name")
      }
    }
  }
""")

print("Sample imported entities:")
for entity in result['entities']:
    print(f"  {entity['headline']} by {entity['author']['name']}")
```

---

## Complete Example

Here's a complete workflow from start to finish:

```python
from scripts.template_configurator import interactive_template_configuration
from scripts.wordlift_client import WordLiftClient

# Your configuration
api_key = "your_wordlift_api_key"
dataset_uri = "https://data.wordlift.io/wl92832"

sample_urls = [
    "https://yoursite.com/blog/post-1",
    "https://yoursite.com/blog/post-2",
    "https://yoursite.com/about"
]

# Initialize client
client = WordLiftClient(api_key)

# Run interactive configuration
print("🔧 TEMPLATE CONFIGURATION WORKFLOW")
print("="*60)

template_config = interactive_template_configuration(
    client,
    dataset_uri,
    sample_urls
)

# Review and approve
print("\n📋 TEMPLATE CONFIGURATION:")
print(json.dumps(template_config, indent=2))

user_approval = input("\nApprove this template for bulk import? (yes/no): ")

if user_approval.lower() == 'yes':
    # Save template
    configurator = TemplateConfigurator(client, dataset_uri)
    configurator.save_template(template_config, 'approved_template.json')

    # Proceed with bulk import
    print("\n🚀 Starting bulk import with approved template...")

    results = client.import_from_sitemap("https://yoursite.com/sitemap.xml")

    print(f"\n✅ Import complete!")
    print(f"   Imported: {len(results)} pages")

    # Verify
    verify_query = """
      query {
        entities(
          query: { typeConstraint: { in: ["http://schema.org/BlogPosting"] } }
          rows: 1
        ) {
          totalCount: aggregateInt(operation: COUNT) { count }
        }
      }
    """

    result = client.graphql_query(verify_query)
    total = result['entities']['totalCount']['count']

    print(f"   Verified: {total} entities in KG")
else:
    print("\n❌ Template not approved. Please refine configuration.")
```

---

## Configuration Best Practices

### 1. Choose Representative Samples

✅ **DO:**
- Pick typical pages from different sections
- Include pages with all expected metadata
- Choose pages that are live and accessible

❌ **DON'T:**
- Use only edge cases
- Pick pages with incomplete metadata
- Use draft or unpublished pages

### 2. Start with Strict Validation

```python
# Use strict mode to catch all issues
is_valid, errors, warnings = validator.validate(template, strict=True)
```

In strict mode, recommended fields become required. This ensures high-quality data.

### 3. Test Entity Reuse

If your pages have common entities (authors, publishers):

```python
from scripts.entity_reuse import EntityReuseManager

reuse_manager = EntityReuseManager(client, dataset_uri)
reuse_manager.preload_cache()

# Check if publisher exists
publisher_iri = reuse_manager.get_or_create_organization({
    'name': 'Your Company',
    'url': 'https://yoursite.com'
})

print(f"Publisher IRI: {publisher_iri}")
```

### 4. Document Your Template

Save a README with your template:

```markdown
# Bulk Import Template Configuration

**Date:** 2024-01-15
**Pages:** 700 blog posts
**Entity Type:** BlogPosting

## Configuration:
- Extract authors: Yes
- Publisher: Your Company (https://data.wordlift.io/wl92832/organization/your-company)
- Metadata: headline, description, datePublished, image
- ID Pattern: URL slug only

## Sample Analysis:
- Analyzed 3 sample pages
- All samples passed validation
- Common type: BlogPosting (100%)

## Approved by: [Your Name]
```

### 5. Incremental Import for Testing

Before importing all 700 pages, test with a small batch:

```python
# Import just 10 URLs first
test_urls = [
    "https://yoursite.com/blog/post-1",
    "https://yoursite.com/blog/post-2",
    # ... 8 more
]

results = client.import_from_urls(test_urls)

# Verify the results
# If everything looks good, proceed with full sitemap
```

---

## Troubleshooting

### Issue: Validation Fails on Samples

**Symptom:**
```
✗ Product missing required field: gtin14
✗ Invalid @id format
```

**Solution:**
1. Check sample pages have all required data
2. Adjust template to match actual page structure
3. Use WordLift Agent to analyze page markup
4. Update configuration based on Agent output

### Issue: Different Page Types Detected

**Symptom:**
```
Detected content types:
  • BlogPosting: 2 page(s)
  • Product: 1 page(s)
  • WebPage: 3 page(s)
```

**Solution:**
- Create separate templates for each type
- Run bulk import in batches by type
- Or use conditional logic to handle mixed types

### Issue: Entity Reuse Not Working

**Symptom:**
```
+ Creating new organization: Your Company
+ Creating new organization: Your Company
```

**Solution:**
1. Preload cache before import: `reuse_manager.preload_cache()`
2. Check organization name is consistent
3. Verify dataset_uri is correct

---

## Summary Checklist

Before bulk importing 700 pages:

- [ ] Select 2-3 representative sample URLs
- [ ] Run template configurator on samples
- [ ] Review detected entity types
- [ ] Answer configuration questions
- [ ] Validate proposed markup template
- [ ] Check SHACL validation passes (strict mode)
- [ ] Save approved template configuration
- [ ] Test with small batch (10-20 pages)
- [ ] Verify test import in KG
- [ ] Get user approval
- [ ] Proceed with full bulk import
- [ ] Verify total entity count matches expected

**Only proceed with bulk import after ✅ ALL checkboxes are checked!**

This workflow ensures you get it right the first time and avoid costly mistakes on large imports.