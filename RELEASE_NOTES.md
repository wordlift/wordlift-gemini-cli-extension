# Release v1.0.0 - Initial Release

## 🎉 First Public Release

This is the first public release of the WordLift Gemini CLI Extension!

## ✨ Features

Complete CRUD operations for WordLift Knowledge Graph entities:

- **`create_entities`** - Create new entities in your Knowledge Graph
- **`create_or_update_entities`** - Upsert entities (create new or update existing) - **recommended**
- **`get_entities`** - Retrieve entities by their IDs
- **`patch_entities`** - Partially update specific properties of existing entities
- **`delete_entities`** - Delete entities by their IDs
- **`upload_turtle_file`** - Bulk upload/update entities from Turtle files

## 🔧 Technical Details

- Multi-format RDF support (Turtle, JSON-LD, RDF/XML)
- Built with FastMCP (Model Context Protocol)
- Official WordLift Python SDK integration
- RDF validation using rdflib
- Comprehensive error handling

## 📦 Installation

Install directly from GitHub:

```bash
gemini extensions install https://github.com/wordlift/wordlift-gemini-cli-extension.git
```

Or install this specific release:

```bash
gemini extensions install https://github.com/wordlift/wordlift-gemini-cli-extension.git --ref=v1.0.0
```

For detailed setup instructions, see [INSTALL.md](https://github.com/wordlift/wordlift-gemini-cli-extension/blob/main/INSTALL.md).

## 📚 Documentation

- [README.md](https://github.com/wordlift/wordlift-gemini-cli-extension/blob/main/README.md) - Full documentation
- [INSTALL.md](https://github.com/wordlift/wordlift-gemini-cli-extension/blob/main/INSTALL.md) - Installation guide
- [CHANGELOG.md](https://github.com/wordlift/wordlift-gemini-cli-extension/blob/main/CHANGELOG.md) - Version history

## 🔐 Configuration

This extension requires:
- WordLift API Key
- Python 3.10+
- Virtual environment with dependencies from `requirements.txt`

See installation guide for complete setup instructions.

## 📄 License

MIT License - see [LICENSE](https://github.com/wordlift/wordlift-gemini-cli-extension/blob/main/LICENSE)
