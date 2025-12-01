import os
import logging
from typing import Optional, List
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv
import rdflib
import wordlift_client
from wordlift_client.rest import ApiException

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

def get_api_client():
    """Configures and returns the WordLift API client."""
    if not WORDLIFT_API_KEY:
        raise ValueError("WORDLIFT_API_KEY environment variable is not set.")

    configuration = wordlift_client.Configuration(
        host=WORDLIFT_API_ENDPOINT
    )
    configuration.api_key['Authorization'] = WORDLIFT_API_KEY
    configuration.api_key_prefix['Authorization'] = 'Key'

    return wordlift_client.ApiClient(configuration)

def format_rdf_content(content: str, format_type: str = "turtle") -> str:
    """Validate and format RDF content."""
    g = rdflib.Graph()
    g.parse(data=content, format=format_type)
    return g.serialize(format=format_type)

# ==================== CREATE OPERATIONS ====================

@mcp.tool()
def create_entities(rdf_content: str, content_format: str = "turtle") -> str:
    """
    Creates new entities in the WordLift Knowledge Graph.

    Args:
        rdf_content: RDF data as a string (Turtle, JSON-LD, or RDF/XML format).
        content_format: Format of the RDF content. Options: "turtle", "json-ld", "xml". Default: "turtle".

    Returns:
        A status message indicating success or failure.
    """
    try:
        # Validate and format the RDF content
        formatted_content = format_rdf_content(rdf_content, content_format)

        # Map format to content type
        content_type_map = {
            "turtle": "text/turtle",
            "json-ld": "application/ld+json",
            "xml": "application/rdf+xml"
        }
        content_type = content_type_map.get(content_format, "text/turtle")

        # Create entities
        api_client = get_api_client()
        api_instance = wordlift_client.EntitiesApi(api_client)

        api_instance.create_entities(
            body=formatted_content,
            _content_type=content_type
        )

        # Count triples for reporting
        g = rdflib.Graph()
        g.parse(data=formatted_content, format=content_format)
        triple_count = len(g)

        return f"Successfully created entities with {triple_count} triples in WordLift KG."

    except ApiException as e:
        logger.error(f"WordLift API Exception: {e}")
        return f"WordLift API Error: {e.status} - {e.reason}\n{e.body}"
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return f"Error: {str(e)}"

@mcp.tool()
def create_or_update_entities(rdf_content: str, content_format: str = "turtle") -> str:
    """
    Creates new entities or updates existing ones (upsert operation) in the WordLift Knowledge Graph.

    This is the recommended method for most operations as it handles both creation and updates.

    Args:
        rdf_content: RDF data as a string (Turtle, JSON-LD, or RDF/XML format).
        content_format: Format of the RDF content. Options: "turtle", "json-ld", "xml". Default: "turtle".

    Returns:
        A status message indicating success or failure.
    """
    try:
        # Validate and format the RDF content
        formatted_content = format_rdf_content(rdf_content, content_format)

        # Map format to content type
        content_type_map = {
            "turtle": "text/turtle",
            "json-ld": "application/ld+json",
            "xml": "application/rdf+xml"
        }
        content_type = content_type_map.get(content_format, "text/turtle")

        # Upsert entities
        api_client = get_api_client()
        api_instance = wordlift_client.EntitiesApi(api_client)

        api_instance.create_or_update_entities(
            body=formatted_content,
            _content_type=content_type
        )

        # Count triples for reporting
        g = rdflib.Graph()
        g.parse(data=formatted_content, format=content_format)
        triple_count = len(g)

        return f"Successfully upserted entities with {triple_count} triples in WordLift KG."

    except ApiException as e:
        logger.error(f"WordLift API Exception: {e}")
        return f"WordLift API Error: {e.status} - {e.reason}\n{e.body}"
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return f"Error: {str(e)}"

# ==================== READ OPERATIONS ====================

@mcp.tool()
def get_entities(entity_ids: str) -> str:
    """
    Retrieves entities from the WordLift Knowledge Graph by their IDs.

    Args:
        entity_ids: Comma-separated list of entity IRIs or IDs to retrieve.

    Returns:
        The entity data in Turtle format or an error message.
    """
    try:
        api_client = get_api_client()
        api_instance = wordlift_client.EntitiesApi(api_client)

        # Convert comma-separated string to list
        id_list = [id.strip() for id in entity_ids.split(",")]

        response = api_instance.get_entities(id=id_list)

        return f"Successfully retrieved entities:\n\n{response}"

    except ApiException as e:
        logger.error(f"WordLift API Exception: {e}")
        return f"WordLift API Error: {e.status} - {e.reason}\n{e.body}"
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return f"Error: {str(e)}"

# ==================== UPDATE OPERATIONS ====================

@mcp.tool()
def patch_entities(rdf_content: str, content_format: str = "turtle") -> str:
    """
    Patches (partially updates) existing entities in the WordLift Knowledge Graph.

    This method allows you to update specific properties without replacing the entire entity.

    Args:
        rdf_content: RDF data as a string containing the properties to update (Turtle, JSON-LD, or RDF/XML format).
        content_format: Format of the RDF content. Options: "turtle", "json-ld", "xml". Default: "turtle".

    Returns:
        A status message indicating success or failure.
    """
    try:
        # Validate and format the RDF content
        formatted_content = format_rdf_content(rdf_content, content_format)

        # Map format to content type
        content_type_map = {
            "turtle": "text/turtle",
            "json-ld": "application/ld+json",
            "xml": "application/rdf+xml"
        }
        content_type = content_type_map.get(content_format, "text/turtle")

        # Patch entities
        api_client = get_api_client()
        api_instance = wordlift_client.EntitiesApi(api_client)

        api_instance.patch_entities(
            body=formatted_content,
            _content_type=content_type
        )

        # Count triples for reporting
        g = rdflib.Graph()
        g.parse(data=formatted_content, format=content_format)
        triple_count = len(g)

        return f"Successfully patched entities with {triple_count} triples in WordLift KG."

    except ApiException as e:
        logger.error(f"WordLift API Exception: {e}")
        return f"WordLift API Error: {e.status} - {e.reason}\n{e.body}"
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return f"Error: {str(e)}"

# ==================== DELETE OPERATIONS ====================

@mcp.tool()
def delete_entities(entity_ids: str) -> str:
    """
    Deletes entities from the WordLift Knowledge Graph by their IDs.

    Args:
        entity_ids: Comma-separated list of entity IRIs or IDs to delete.

    Returns:
        A status message indicating success or failure.
    """
    try:
        api_client = get_api_client()
        api_instance = wordlift_client.EntitiesApi(api_client)

        # Convert comma-separated string to list
        id_list = [id.strip() for id in entity_ids.split(",")]

        api_instance.delete_entities(id=id_list)

        return f"Successfully deleted {len(id_list)} entities from WordLift KG."

    except ApiException as e:
        logger.error(f"WordLift API Exception: {e}")
        return f"WordLift API Error: {e.status} - {e.reason}\n{e.body}"
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return f"Error: {str(e)}"

# ==================== FILE OPERATIONS ====================

@mcp.tool()
def upload_turtle_file(file_path: str, operation: str = "upsert") -> str:
    """
    Reads a Turtle (.ttl) file, validates it, and uploads it to WordLift.

    Args:
        file_path: Absolute path to the .ttl file.
        operation: Operation to perform. Options: "create", "upsert", "patch". Default: "upsert".

    Returns:
        A status message indicating success or failure.
    """
    if not os.path.exists(file_path):
        return f"Error: File not found at {file_path}"

    try:
        # Read and parse the file
        g = rdflib.Graph()
        g.parse(file_path, format="turtle")
        triple_count = len(g)
        logger.info(f"Parsed {triple_count} triples from {file_path}")

        # Serialize back to Turtle
        turtle_content = g.serialize(format="turtle")

        # Upload to WordLift based on operation
        api_client = get_api_client()
        api_instance = wordlift_client.EntitiesApi(api_client)

        if operation == "create":
            api_instance.create_entities(
                body=turtle_content,
                _content_type='text/turtle'
            )
            action = "created"
        elif operation == "patch":
            api_instance.patch_entities(
                body=turtle_content,
                _content_type='text/turtle'
            )
            action = "patched"
        else:  # default to upsert
            api_instance.create_or_update_entities(
                body=turtle_content,
                _content_type='text/turtle'
            )
            action = "upserted"

        return f"Successfully {action} {triple_count} triples from {file_path} to WordLift KG."

    except ApiException as e:
        logger.error(f"WordLift API Exception: {e}")
        return f"WordLift API Error: {e.status} - {e.reason}\n{e.body}"
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return f"Error: {str(e)}"

if __name__ == "__main__":
    mcp.run()
