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
from dotenv import load_dotenv

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

def upgrade_entity(client, iri, new_type=None, new_props=None):
    """
    Fetches an entity, updates its type/properties, and syncs it back.
    
    Args:
        client: WordLiftClient instance
        iri: The entity URI to update
        new_type: (Optional) The new Schema.org type (e.g., "Product")
        new_props: (Optional) Dictionary of properties to add/update
    """
    print(f"Fetching entity: {iri}...")
    
    # 1. Fetch current basic data
    # We use a broad query to get the label and description to preserve them
    query = """
    query($iri: Ref!) {
      resource(iri: $iri) {
        iri
        name: string(name: "schema:name")
        description: string(name: "schema:description")
        url: string(name: "schema:url")
        image: string(name: "schema:image")
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

    # 2. Build the updated JSON-LD object
    updated_entity = {
        "@context": "https://schema.org",
        "@id": iri,
    }
    
    if new_type:
        updated_entity["@type"] = new_type
    
    # Preserve key fields found in KG
    if resource.get('name'): updated_entity['name'] = resource['name']
    if resource.get('description'): updated_entity['description'] = resource['description']
    if resource.get('url'): updated_entity['url'] = resource['url']
    if resource.get('image'): updated_entity['image'] = resource['image']

    # Merge new properties
    if new_props:
        updated_entity.update(new_props)

    print(f"Updating entity with Type: {updated_entity.get('@type', 'Unchanged')} and {len(new_props or {})} new properties...")
    
    # 3. Sync back
    try:
        client.create_or_update_entity(updated_entity)
        print(f"Successfully updated {iri}")
        return True
    except Exception as e:
        print(f"Update failed: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Upgrade or modify an existing entity in WordLift.')
    parser.add_argument('iri', help='The URI of the entity to update')
    parser.add_argument('--type', help='The new Schema.org type (e.g., TouristDestination)')
    parser.add_argument('--props', help='JSON string of properties to add (e.g., \'{"alternateName": "X"}\'')
    parser.add_argument('--api-key', help='WordLift API Key (optional, defaults to env var)')
    
    args = parser.parse_args()

    load_dotenv()
    api_key = args.api_key or os.getenv("WORDLIFT_API_KEY")
    
    if not api_key:
        print("Error: API Key not provided.")
        sys.exit(1)

    client = WordLiftClient(api_key)
    
    props = None
    if args.props:
        try:
            props = json.loads(args.props)
        except json.JSONDecodeError:
            print("Error: --props must be valid JSON.")
            sys.exit(1)

    upgrade_entity(client, args.iri, new_type=args.type, new_props=props)

if __name__ == "__main__":
    main()
