# Changelog

All notable changes to the WordLift Gemini CLI Extension will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.0] - 2025-12-19

### Added
- **Entity Upgrading**: New `entity_upgrader.py` script for robust "Fetch-Modify-Update" workflows.
- **Enhanced Documentation**: Comprehensive update to `GEMINI.md` with refined core principles and tool selection guides.
- **Integrated Guides**: New reference documentation for `entity-upgrading.md` and updated `workflows.md`.

### Changed
- **Workspace Cleanup**: Removed legacy test scripts and unneeded scraper prototypes (`kg_builder.py`).
- **Standardized Core**: Synced internal scripts with the project folder for better consistency.

## [1.1.0] - 2025-12-18

### Added
- **Knowledge Graph Builder Suite**: Transform webpages into structured Data.
- **Improved Entity Building**:
  - `build_product`: Create Google-friendly Products with GS1 Digital Link IRIs.
  - `build_organization` & `build_webpage`: Proper slug-based ID generation.
- **Validation & Quality Control**:
  - `validate_entity`: SHACL-based validation for Products, Organizations, and WebPages.
  - `markup_validator`: Structural JSON-LD validation.
- **Sync & Orchestration**:
  - `sync_kg`: Multi-mode sync tool (Batch or Incremental PATCH).
  - `import_from_sitemap` & `import_from_urls`: Unified WordLift Sitemap Import API integration.
- **Internal Core Scripts**:
  - `id_generator.py`: GTIN-14 normalization and GS1 Digital Link generation.
  - `entity_reuse.py`: Prevents duplicates by reusing existing entities from the KG.
  - `wordlift_client.py`: High-level Python wrapper for both REST and GraphQL APIs.
- **Documentation**:
  - Extensive `references/` folder with technical guides and patterns.
  - `dry_run_test.py` for offline verification of core logic.

## [1.0.0] - 2025-12-01

### Added
- Initial release of WordLift Gemini CLI Extension
- Complete CRUD operations for WordLift Knowledge Graph entities:
  - `create_entities` - Create new entities
  - `create_or_update_entities` - Upsert entities (recommended)
  - `get_entities` - Retrieve entities by IDs
  - `patch_entities` - Partially update entity properties
  - `delete_entities` - Delete entities by IDs
  - `upload_turtle_file` - Bulk upload from Turtle files
- Support for multiple RDF formats (Turtle, JSON-LD, RDF/XML)
- RDF validation using rdflib
- Comprehensive error handling and reporting
- Full documentation with usage examples
- Automated installation script (`install.sh`) for seamless setup
- `.env.example` template for easy configuration
- Separate installation and development documentation
