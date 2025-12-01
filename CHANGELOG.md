# Changelog

All notable changes to the WordLift Gemini CLI Extension will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
