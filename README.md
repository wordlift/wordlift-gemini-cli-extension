# WordLift Knowledge Graph Builder & Gemini CLI Extension

This extension empowers Gemini with the **WordLift Knowledge Graph Builder** skill, allowing you to build and maintain Knowledge Graphs directly from your CLI.

## 🧠 Agent Skills

This extension includes the `wordlift-kg-builder` skill. When enabled, Gemini gains specialized expertise to:

- **Import Sitemaps**: Ingest thousands of pages from `sitemap.xml`.
- **Build Entities**: Create valid schema.org Product, Organization, and WebPage entities.
- **Generate GS1 IDs**: Create deterministic, GS1 Digital Link compliant identifiers.
- **Validate Data**: Ensure data quality with built-in SHACL validation.
- **Sync to WordLift**: Orchestrate batch updates and incremental patches.

To use it, simply ask Gemini:
> "Help me import pages from my sitemap"
> "Build a Product entity with GS1 Digital Link"
> "Validate this JSON-LD against your SHACL shapes"

## Installation

Install the extension directly from GitHub:

```bash
gemini extensions install https://github.com/wordlift/wordlift-gemini-cli-extension.git
```

### Configuration

Create a `.env` file in the extension directory with your WordLift credentials:

```env
WORDLIFT_API_KEY=your_api_key_here
WORDLIFT_BASE_URI=https://data.wordlift.io/wl123
WORDLIFT_API_ENDPOINT=https://api.wordlift.io
```

## Core Features (via MCP)

Even without activating the full Skill, the extension provides basic tools via the Model Context Protocol (MCP):

- **`import_from_sitemap`**: Import URLs from sitemap.xml.
- **`build_product`**: Create schema.org Product entities.
- **`validate_entity`**: Validate entities against SHACL shapes.
- **`sync_kg`**: Perform batch create/update operations.

## Architecture

- **`skills/`**: Contains the `wordlift-kg-builder` Agent Skill.
- **`wl_extension/`**: Core Python logic (entity building, validation, sync).
- **`server.py`**: MCP server implementation.

## Support

For WordLift API documentation, visit: [docs.wordlift.io](https://docs.wordlift.io/)
