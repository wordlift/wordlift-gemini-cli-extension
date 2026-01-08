import os
import logging
import sys
import json
from typing import Optional, List, Dict, Any
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv
import rdflib

# Add skills scripts directory to path
# Add skills scripts directory to path (prioritize over installed packages)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "skills", "wordlift-kg-builder", "scripts"))

# Import new components
from wordlift_client import WordLiftClient
from entity_builder import EntityBuilder
from id_generator import generate_product_id, generate_entity_id
from shacl_validator import SHACLValidator
from markup_validator import MarkupValidator
from kg_sync import KGSyncOrchestrator
from template_configurator import TemplateConfigurator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Configuration
WORDLIFT_API_KEY = os.getenv("WORDLIFT_API_KEY")
WORDLIFT_BASE_URI = os.getenv("WORDLIFT_BASE_URI")
WORDLIFT_API_ENDPOINT = os.getenv("WORDLIFT_API_ENDPOINT", "https://api.wordlift.io")

# Initialize FastMCP
mcp = FastMCP("WordLift")

def get_client():
    """Returns a WordLift API client."""
    if not WORDLIFT_API_KEY:
        raise ValueError("WORDLIFT_API_KEY environment variable is not set.")
    return WordLiftClient(WORDLIFT_API_KEY, WORDLIFT_API_ENDPOINT)

def get_dataset_uri():
    """Returns the dataset URI from env or raises error."""
    if not WORDLIFT_BASE_URI:
        raise ValueError("WORDLIFT_BASE_URI environment variable is not set.")
    return WORDLIFT_BASE_URI.rstrip('/')

# ==================== KNOWLEDGE GRAPH BUILDING ====================

@mcp.tool()
def import_from_sitemap(sitemap_url: str) -> str:
    """
    Import pages from a sitemap.xml using WordLift Sitemap Import API.

    Args:
        sitemap_url: URL to the sitemap.xml file.
    """
    try:
        client = get_client()
        results = client.import_from_sitemap(sitemap_url)
        return f"Successfully imported {len(results)} pages from sitemap: {sitemap_url}"
    except Exception as e:
        logger.error(f"Sitemap import error: {e}")
        return f"Error: {str(e)}"

@mcp.tool()
def import_from_urls(urls: List[str]) -> str:
    """
    Import specific URLs into the WordLift Knowledge Graph.

    Args:
        urls: List of URLs to import.
    """
    try:
        client = get_client()
        results = client.import_from_urls(urls)
        return f"Successfully imported {len(results)} URLs"
    except Exception as e:
        logger.error(f"URL import error: {e}")
        return f"Error: {str(e)}"

@mcp.tool()
def build_product(data_json: str) -> str:
    """
    Build a JSON-LD Product entity with GS1 Digital Link ID.

    Args:
        data_json: JSON string containing product data (gtin, name, description, brand, price, currency, etc.).
    """
    try:
        data = json.loads(data_json)
        builder = EntityBuilder(get_dataset_uri())
        product = builder.build_product(data)
        return json.dumps(product, indent=2)
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool()
def build_organization(data_json: str) -> str:
    """
    Build a JSON-LD Organization entity.

    Args:
        data_json: JSON string containing organization data (name, url, logo, description, etc.).
    """
    try:
        data = json.loads(data_json)
        builder = EntityBuilder(get_dataset_uri())
        org = builder.build_organization(data)
        return json.dumps(org, indent=2)
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool()
def build_webpage(data_json: str) -> str:
    """
    Build a JSON-LD WebPage entity.

    Args:
        data_json: JSON string containing webpage data (url, name, description, etc.).
    """
    try:
        data = json.loads(data_json)
        builder = EntityBuilder(get_dataset_uri())
        webpage = builder.build_webpage(data)
        return json.dumps(webpage, indent=2)
    except Exception as e:
        return f"Error: {str(e)}"

# ==================== VALIDATION & SYNC ====================

@mcp.tool()
def validate_entity(entity_json: str, strict: bool = False) -> str:
    """
    Validate a JSON-LD entity against SHACL shapes.

    Args:
        entity_json: JSON-LD entity string.
        strict: Whether to treat recommended fields as required.
    """
    try:
        entity = json.loads(entity_json)
        validator = SHACLValidator()
        is_valid, errors, warnings = validator.validate(entity, strict)

        result = {
            "valid": is_valid,
            "errors": errors,
            "warnings": warnings
        }
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool()
def sync_kg(products_json: str, incremental: bool = False) -> str:
    """
    Sync multiple products to the WordLift Knowledge Graph.

    Args:
        products_json: JSON array of product data.
        incremental: Whether to use incremental PATCH updates.
    """
    try:
        products = json.loads(products_json)
        orchestrator = KGSyncOrchestrator(WORDLIFT_API_KEY, get_dataset_uri())

        if incremental:
            stats = orchestrator.incremental_update(products)
        else:
            stats = orchestrator.sync_products(products)

        return f"Sync complete: {json.dumps(stats, indent=2)}"
    except Exception as e:
        logger.error(f"Sync error: {e}")
        return f"Error: {str(e)}"

# ==================== LEGACY OPERATIONS (Refactored) ====================

@mcp.tool()
def create_or_update_entities(rdf_content: str, content_format: str = "json-ld") -> str:
    """
    Creates new entities or updates existing ones in the WordLift Knowledge Graph.

    Args:
        rdf_content: RDF data as a string.
        content_format: Format (turtle, json-ld, xml). Default: json-ld.
    """
    try:
        client = get_client()
        if content_format == "json-ld":
            entity = json.loads(rdf_content)
            client.create_or_update_entity(entity)
            return "Successfully upserted entity in WordLift KG."
        else:
            # Fallback for Turtle/XML using simple implementation
            return "Error: Enhanced client currently optimized for JSON-LD. Use build_product/build_organization for best results."
    except Exception as e:
        logger.error(f"Upsert error: {e}")
        return f"Error: {str(e)}"

@mcp.tool()
def get_entity(entity_id: str) -> str:
    """
    Retrieves an entity from the WordLift Knowledge Graph by its ID/IRI.
    """
    try:
        client = get_client()
        entity = client.get_entity_by_url(entity_id)
        if entity:
            return json.dumps(entity, indent=2)
        return f"Entity not found: {entity_id}"
    except Exception as e:
        logger.error(f"Get entity error: {e}")
        return f"Error: {str(e)}"

@mcp.tool()
def delete_entities(entity_ids: str) -> str:
    """
    Deletes entities from the WordLift Knowledge Graph by their IDs.

    Args:
        entity_ids: Comma-separated list of entity IRIs.
    """
    try:
        client = get_client()
        id_list = [id.strip() for id in entity_ids.split(",")]
        for entity_id in id_list:
            client.delete_entity(entity_id)
        return f"Successfully deleted {len(id_list)} entities from WordLift KG."
    except Exception as e:
        logger.error(f"Delete error: {e}")
        return f"Error: {str(e)}"

if __name__ == "__main__":
    mcp.run()
