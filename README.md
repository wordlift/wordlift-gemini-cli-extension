# WordLift Gemini CLI Extension

This extension allows you to interact with WordLift Knowledge Graphs directly from Gemini CLI with full CRUD (Create, Read, Update, Delete) operations for entities.

## Features

### Entity Management Tools

- **`create_entities`**: Create new entities in your Knowledge Graph
- **`create_or_update_entities`**: Upsert entities (create new or update existing) - **recommended for most use cases**
- **`get_entities`**: Retrieve entities by their IDs
- **`patch_entities`**: Partially update specific properties of existing entities
- **`delete_entities`**: Delete entities by their IDs
- **`upload_turtle_file`**: Bulk upload/update entities from Turtle (.ttl) files

### Supported RDF Formats

All entity operations support multiple RDF formats:
- **Turtle** (default, `.ttl`)
- **JSON-LD** (`.jsonld`)
- **RDF/XML** (`.rdf`, `.xml`)

## Prerequisites

- Python 3.10+
- WordLift API Key
- WordLift Dataset URI

## Installation

1.  Navigate to the extension directory:
    ```bash
    cd wordlift-gemini-cli-extension
    ```

2.  Install Python dependencies:
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```

3.  Configure Environment Variables:
    Create a `.env` file in this directory with your WordLift credentials:
    ```env
    WORDLIFT_API_KEY=your_api_key_here
    WORDLIFT_BASE_URI=https://data.wordlift.io/wl1505540
    WORDLIFT_API_ENDPOINT=https://api.wordlift.io
    ```

4.  Link the extension to Gemini CLI:
    ```bash
    gemini extensions link .
    ```

## Usage Examples

Once linked, you can use natural language in Gemini CLI to interact with your Knowledge Graph:

### Creating Entities

```
Create a new entity in my WordLift KG:
@prefix schema: <http://schema.org/> .
<http://example.com/person/john> a schema:Person ;
    schema:name "John Doe" ;
    schema:email "john@example.com" .
```

### Upserting Entities (Recommended)

```
Upsert the following entity to my WordLift KG:
@prefix schema: <http://schema.org/> .
<http://example.com/org/acme> a schema:Organization ;
    schema:name "ACME Corporation" ;
    schema:url "https://acme.com" .
```

### Retrieving Entities

```
Get the entity http://example.com/person/john from WordLift
```

### Patching Entities

```
Update just the email address for entity http://example.com/person/john:
@prefix schema: <http://schema.org/> .
<http://example.com/person/john> schema:email "newemail@example.com" .
```

### Deleting Entities

```
Delete entities http://example.com/person/john, http://example.com/person/jane from WordLift
```

### Uploading Turtle Files

```
Upload the file /path/to/entities.ttl to WordLift using upsert operation
```

## API Methods Reference

### Create Operations

#### `create_entities(rdf_content, content_format="turtle")`
Creates new entities. Will fail if entities already exist.

**Parameters:**
- `rdf_content` (str): RDF data as string
- `content_format` (str): Format type - "turtle", "json-ld", or "xml"

#### `create_or_update_entities(rdf_content, content_format="turtle")`
**Recommended**: Upserts entities - creates new or updates existing.

**Parameters:**
- `rdf_content` (str): RDF data as string
- `content_format` (str): Format type - "turtle", "json-ld", or "xml"

### Read Operations

#### `get_entities(entity_ids)`
Retrieves entities by their IDs/IRIs.

**Parameters:**
- `entity_ids` (str): Comma-separated list of entity URIs

**Example:** `"http://example.com/entity1, http://example.com/entity2"`

### Update Operations

#### `patch_entities(rdf_content, content_format="turtle")`
Partially updates existing entities without replacing all properties.

**Parameters:**
- `rdf_content` (str): RDF data containing only properties to update
- `content_format` (str): Format type - "turtle", "json-ld", or "xml"

### Delete Operations

#### `delete_entities(entity_ids)`
Deletes entities permanently.

**Parameters:**
- `entity_ids` (str): Comma-separated list of entity URIs

### File Operations

#### `upload_turtle_file(file_path, operation="upsert")`
Validates and uploads Turtle files.

**Parameters:**
- `file_path` (str): Absolute path to .ttl file
- `operation` (str): Operation type - "create", "upsert", or "patch"

## Architecture

This extension is built using:
- **FastMCP**: Python SDK for Model Context Protocol
- **wordlift-client**: Official WordLift Python SDK (v1.123.0+)
- **rdflib**: RDF parsing and validation

The extension exposes MCP tools that Gemini can use to manage your Knowledge Graph through natural language interactions.

## Troubleshooting

### API Authentication Errors
Ensure your `WORDLIFT_API_KEY` is correctly set in the `.env` file and is valid.

### Module Not Found Errors
Make sure you've activated the virtual environment and installed all dependencies:
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### RDF Parsing Errors
Validate your RDF syntax before uploading. The extension will report the specific line where parsing failed.

## Support

For WordLift API documentation, visit: https://docs.wordlift.io/api/middleware/entities/
