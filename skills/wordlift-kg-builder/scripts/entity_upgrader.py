#!/usr/bin/env python3
"""
Entity Upgrader Script
Updates an existing entity's type and properties using a Fetch-Modify-Update pattern.
This is safer and more robust than JSON Patching for changing types or complex updates.
"""

import os
import sys
import json
import argparse
from typing import Dict, Any, Optional

# Ensure we can import the client
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

try:
    from wordlift_client import WordLiftClient
except ImportError:
    # Fallback if running from a different directory
    try:
        from scripts.wordlift_client import WordLiftClient
    except ImportError:
         print("Error: Could not import WordLiftClient.")
         sys.exit(1)


def upgrade_entity(client: WordLiftClient, iri: str, new_type: Optional[str] = None,
                   new_props: Optional[Dict[str, Any]] = None) -> bool:
    """
    Fetches an entity, updates its type/properties, and syncs it back.

    This uses the Fetch-Modify-Update pattern which is safer than PATCH for:
    - Changing entity types (e.g., WebPage → Article)
    - Adding complex nested properties
    - Preserving existing data while making structural changes

    Args:
        client: WordLiftClient instance
        iri: The entity URI to update
        new_type: (Optional) The new Schema.org type (e.g., "Product", "Article")
        new_props: (Optional) Dictionary of properties to add/update

    Returns:
        True if successful, False otherwise

    Example:
        >>> client = WordLiftClient(api_key)
        >>> upgrade_entity(
        ...     client,
        ...     "https://data.wordlift.io/wl123/webpage/about",
        ...     new_type="Article",
        ...     new_props={"author": {"@type": "Person", "name": "John Doe"}}
        ... )
    """
    print(f"Fetching entity: {iri}...")

    # 1. Fetch current basic data
    # We use a broad query to get key properties to preserve them
    query = """
    query($iri: Ref!) {
      resource(iri: $iri) {
        iri
        name: string(name: "schema:name")
        description: string(name: "schema:description")
        url: string(name: "schema:url")
        image: string(name: "schema:image")
        datePublished: string(name: "schema:datePublished")
        dateModified: string(name: "schema:dateModified")
      }
    }
    """
    try:
        data = client.graphql_query(query, variables={"iri": iri})
        resource = data.get('resource')
    except Exception as e:
        print(f"Error fetching entity: {e}")
        return False

    if not resource:
        print(f"Entity not found: {iri}")
        return False

    print(f"✓ Entity found: {resource.get('name', 'Untitled')}")

    # 2. Build the updated JSON-LD object
    updated_entity = {
        "@context": "https://schema.org",
        "@id": iri,
    }

    if new_type:
        updated_entity["@type"] = new_type
        print(f"  Changing type to: {new_type}")

    # Preserve key fields found in KG
    preserved_count = 0
    if resource.get('name'):
        updated_entity['name'] = resource['name']
        preserved_count += 1
    if resource.get('description'):
        updated_entity['description'] = resource['description']
        preserved_count += 1
    if resource.get('url'):
        updated_entity['url'] = resource['url']
        preserved_count += 1
    if resource.get('image'):
        updated_entity['image'] = resource['image']
        preserved_count += 1
    if resource.get('datePublished'):
        updated_entity['datePublished'] = resource['datePublished']
        preserved_count += 1
    if resource.get('dateModified'):
        updated_entity['dateModified'] = resource['dateModified']
        preserved_count += 1

    print(f"  Preserved {preserved_count} existing properties")

    # Merge new properties
    if new_props:
        updated_entity.update(new_props)
        print(f"  Adding {len(new_props)} new properties: {list(new_props.keys())}")

    # 3. Sync back
    print(f"\nUpdating entity...")
    try:
        client.create_or_update_entity(updated_entity)
        print(f"✓ Successfully updated {iri}")
        print(f"\nFinal entity:")
        print(f"  Type: {updated_entity.get('@type', 'Unchanged')}")
        print(f"  Properties: {len(updated_entity) - 2}")  # Minus @context and @id
        return True
    except Exception as e:
        print(f"✗ Update failed: {e}")
        return False


def upgrade_batch(client: WordLiftClient, iris: list, new_type: Optional[str] = None,
                  new_props: Optional[Dict[str, Any]] = None) -> Dict[str, int]:
    """
    Upgrade multiple entities with the same type/properties.

    Args:
        client: WordLiftClient instance
        iris: List of entity URIs to update
        new_type: (Optional) The new Schema.org type
        new_props: (Optional) Dictionary of properties to add/update

    Returns:
        Dictionary with success/failure counts
    """
    stats = {'success': 0, 'failed': 0, 'total': len(iris)}

    print(f"\n{'='*60}")
    print(f"BATCH UPGRADE: {len(iris)} entities")
    print(f"{'='*60}\n")

    for idx, iri in enumerate(iris, 1):
        print(f"\n[{idx}/{len(iris)}] Processing {iri}")
        print("-" * 60)

        if upgrade_entity(client, iri, new_type, new_props):
            stats['success'] += 1
        else:
            stats['failed'] += 1

    print(f"\n{'='*60}")
    print(f"BATCH COMPLETE")
    print(f"{'='*60}")
    print(f"Total: {stats['total']}")
    print(f"Success: {stats['success']}")
    print(f"Failed: {stats['failed']}")

    return stats


def main():
    parser = argparse.ArgumentParser(
        description='Upgrade or modify existing entities in WordLift Knowledge Graph.',
        epilog="""
Examples:
  # Change entity type
  python entity_upgrader.py https://data.wordlift.io/wl123/webpage/about --type Article

  # Add properties
  python entity_upgrader.py https://data.wordlift.io/wl123/webpage/about \\
    --props '{"author": {"@type": "Person", "name": "John Doe"}}'

  # Change type and add properties
  python entity_upgrader.py https://data.wordlift.io/wl123/webpage/about \\
    --type Article \\
    --props '{"author": {"@type": "Person", "name": "John Doe"}, "headline": "New Title"}'

  # Batch upgrade from file
  python entity_upgrader.py --batch-file iris.txt --type Article
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument('iri', nargs='?', help='The URI of the entity to update')
    parser.add_argument('--type', help='The new Schema.org type (e.g., Article, Product, TouristDestination)')
    parser.add_argument('--props', help='JSON string of properties to add (e.g., \'{"alternateName": "X"}\')')
    parser.add_argument('--api-key', help='WordLift API Key (optional, defaults to WORDLIFT_API_KEY env var)')
    parser.add_argument('--batch-file', help='File containing one IRI per line for batch upgrade')

    args = parser.parse_args()

    # Load from .env file if present
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

    api_key = args.api_key or os.getenv("WORDLIFT_API_KEY")

    if not api_key:
        print("Error: API Key not provided.")
        print("Use --api-key or set WORDLIFT_API_KEY environment variable.")
        sys.exit(1)

    if not args.iri and not args.batch_file:
        print("Error: Must provide either an IRI or --batch-file")
        parser.print_help()
        sys.exit(1)

    client = WordLiftClient(api_key)

    # Parse properties if provided
    props = None
    if args.props:
        try:
            props = json.loads(args.props)
        except json.JSONDecodeError as e:
            print(f"Error: --props must be valid JSON: {e}")
            sys.exit(1)

    # Batch or single upgrade
    if args.batch_file:
        # Read IRIs from file
        try:
            with open(args.batch_file, 'r') as f:
                iris = [line.strip() for line in f if line.strip()]

            if not iris:
                print(f"Error: No IRIs found in {args.batch_file}")
                sys.exit(1)

            stats = upgrade_batch(client, iris, new_type=args.type, new_props=props)
            sys.exit(0 if stats['failed'] == 0 else 1)

        except FileNotFoundError:
            print(f"Error: File not found: {args.batch_file}")
            sys.exit(1)
    else:
        # Single entity upgrade
        success = upgrade_entity(client, args.iri, new_type=args.type, new_props=props)
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()