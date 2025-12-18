# Release v1.1.0 - Knowledge Graph Builder

## 🚀 Knowledge Graph Builder Suite

This release transforms the WordLift Gemini CLI Extension into a powerful Knowledge Graph builder, enabling automated data pipelines from webpages to your WordLift KG.

## ✨ New Features

### 📦 Webpage-to-Data Pipeline
- **Sitemap Import**: Jumpstart your KG by importing all pages from a sitemap.xml.
- **Entity Reuse**: Automatically detects and reuses existing brands, authors, and publishers to prevent duplicates.
- **GS1 Digital Link**: Native support for GS1 standards, generating deterministic, dereferenceable IRIs for product catalogs.

### ✅ Validation & Sync
- **SHACL Validation**: Ensure your entities meet strict schema.org requirements (e.g., GTIN-14 validation) before syncing.
- **Incremental PATCH Sync**: Update large catalogs efficiently by only sending changes (using JSON Patch).
- **Batch Operations**: High-performance batch creation and updates.

### � Technical Documentation
- **Technical References**: A new `references/` directory containing detailed guides on workflows, GraphQL patterns, and automation scheduling.
- **Dry Run Testing**: New `scripts/dry_run_test.py` to verify your data logic offline.

## 🔧 Internal Improvements
- New high-level `WordLiftClient` for unified API interaction.
- Enhanced `EntityBuilder` with built-in entity reuse logic.
- Modular architecture with standalone scripts in `scripts/`.

## 📦 Installation & Update

Update your extension directly from GitHub:

```bash
gemini extensions update https://github.com/wordlift/wordlift-gemini-cli-extension.git
```

## 📚 Documentation
- [Workflows](references/workflows.md) - Common KG building patterns
- [GraphQL Patterns](references/graphql_queries.md) - Querying your imported data
- [Validation Guide](references/entity-reuse-and-shacl-validation.md) - Ensuring data quality

## 🔐 Environmental Variables
Update your `.env` to include:
- `WORDLIFT_BASE_URI`: Your base dataset IRI (e.g., `https://data.wordlift.io/wl123`)
