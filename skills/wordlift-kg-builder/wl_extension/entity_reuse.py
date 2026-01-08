#!/usr/bin/env python3
"""
Entity Reuse Manager
Checks for existing entities in KG and reuses them to avoid duplicates.
"""

from typing import Dict, List, Optional, Any
try:
    from .wordlift_client import WordLiftClient
    from .id_generator import generate_entity_id, generate_slug
except (ImportError, ValueError):
    from wordlift_client import WordLiftClient
    from id_generator import generate_entity_id, generate_slug


class EntityReuseManager:
    """Manages entity reuse to avoid duplicates in the Knowledge Graph."""

    def __init__(self, client: WordLiftClient, dataset_uri: str):
        """
        Initialize entity reuse manager.

        Args:
            client: WordLift API client
            dataset_uri: Base dataset URI
        """
        self.client = client
        self.dataset_uri = dataset_uri
        self._cache = {
            'organizations': {},
            'people': {},
            'brands': {},
            'places': {}
        }

    def get_or_create_organization(self, org_data: Dict[str, Any]) -> str:
        """
        Get existing organization IRI or create new one.

        Args:
            org_data: Organization data (must have 'name')

        Returns:
            Organization IRI
        """
        if 'name' not in org_data:
            raise ValueError("Organization must have a 'name' field")

        name = org_data['name']

        # Check cache
        if name in self._cache['organizations']:
            return self._cache['organizations'][name]

        # Generate expected IRI
        org_iri = generate_entity_id(self.dataset_uri, "organization", name)

        # Check if exists in KG
        existing = self.client.get_entity_by_url(org_iri)

        if existing:
            print(f"✓ Reusing existing organization: {name}")
            self._cache['organizations'][name] = org_iri
            return org_iri

        # Query by name (in case different slug was used)
        result = self.client.graphql_query("""
            query($name: String!) {
              entities(
                query: {
                  typeConstraint: { in: ["http://schema.org/Organization"] }
                  nameConstraint: { in: [$name] }
                }
                rows: 1
              ) {
                iri
                name: string(name: "schema:name")
              }
            }
        """, variables={"name": name})

        entities = result.get('entities', [])
        if entities:
            existing_iri = entities[0]['iri']
            print(f"✓ Found existing organization by name: {name}")
            self._cache['organizations'][name] = existing_iri
            return existing_iri

        # Create new organization
        print(f"+ Creating new organization: {name}")
        try:
            from .entity_builder import EntityBuilder
        except (ImportError, ValueError):
            from entity_builder import EntityBuilder
        builder = EntityBuilder(self.dataset_uri)

        org = builder.build_organization(org_data)
        self.client.create_or_update_entity(org)

        self._cache['organizations'][name] = org_iri
        return org_iri

    def get_or_create_person(self, person_data: Dict[str, Any]) -> str:
        """
        Get existing person IRI or create new one.

        Args:
            person_data: Person data (must have 'name')

        Returns:
            Person IRI
        """
        if 'name' not in person_data:
            raise ValueError("Person must have a 'name' field")

        name = person_data['name']

        # Check cache
        if name in self._cache['people']:
            return self._cache['people'][name]

        # Generate expected IRI
        person_iri = generate_entity_id(self.dataset_uri, "person", name)

        # Check if exists
        existing = self.client.get_entity_by_url(person_iri)

        if existing:
            print(f"✓ Reusing existing person: {name}")
            self._cache['people'][name] = person_iri
            return person_iri

        # Query by name
        result = self.client.graphql_query("""
            query($name: String!) {
              entities(
                query: {
                  typeConstraint: { in: ["http://schema.org/Person"] }
                  nameConstraint: { in: [$name] }
                }
                rows: 1
              ) {
                iri
                name: string(name: "schema:name")
              }
            }
        """, variables={"name": name})

        entities = result.get('entities', [])
        if entities:
            existing_iri = entities[0]['iri']
            print(f"✓ Found existing person by name: {name}")
            self._cache['people'][name] = existing_iri
            return existing_iri

        # Create new person
        print(f"+ Creating new person: {name}")
        person_entity = {
            "@context": "https://schema.org",
            "@type": "Person",
            "@id": person_iri,
            "name": name
        }

        # Add optional fields
        if 'jobTitle' in person_data:
            person_entity['jobTitle'] = person_data['jobTitle']
        if 'email' in person_data:
            person_entity['email'] = person_data['email']
        if 'url' in person_data:
            person_entity['url'] = person_data['url']

        self.client.create_or_update_entity(person_entity)

        self._cache['people'][name] = person_iri
        return person_iri

    def get_or_create_brand(self, brand_data: Any) -> Dict[str, Any]:
        """
        Get existing brand IRI or create new one.

        Args:
            brand_data: Brand name (string) or brand object (dict)

        Returns:
            Brand entity with IRI
        """
        # Handle string input
        if isinstance(brand_data, str):
            brand_name = brand_data
            brand_dict = {'name': brand_name}
        else:
            brand_name = brand_data.get('name')
            brand_dict = brand_data

        if not brand_name:
            raise ValueError("Brand must have a name")

        # Check cache
        if brand_name in self._cache['brands']:
            return {
                "@type": "Brand",
                "@id": self._cache['brands'][brand_name],
                "name": brand_name
            }

        # Generate expected IRI
        brand_iri = generate_entity_id(self.dataset_uri, "brand", brand_name)

        # Check if exists
        existing = self.client.get_entity_by_url(brand_iri)

        if existing:
            print(f"✓ Reusing existing brand: {brand_name}")
            self._cache['brands'][brand_name] = brand_iri
            return {
                "@type": "Brand",
                "@id": brand_iri,
                "name": brand_name
            }

        # Query by name
        result = self.client.graphql_query("""
            query($name: String!) {
              entities(
                query: {
                  typeConstraint: { in: ["http://schema.org/Brand"] }
                  nameConstraint: { in: [$name] }
                }
                rows: 1
              ) {
                iri
                name: string(name: "schema:name")
              }
            }
        """, variables={"name": brand_name})

        entities = result.get('entities', [])
        if entities:
            existing_iri = entities[0]['iri']
            print(f"✓ Found existing brand by name: {brand_name}")
            self._cache['brands'][brand_name] = existing_iri
            return {
                "@type": "Brand",
                "@id": existing_iri,
                "name": brand_name
            }

        # Create new brand
        print(f"+ Creating new brand: {brand_name}")
        brand_entity = {
            "@context": "https://schema.org",
            "@type": "Brand",
            "@id": brand_iri,
            "name": brand_name
        }

        # Add optional fields
        if isinstance(brand_dict, dict):
            if 'logo' in brand_dict:
                brand_entity['logo'] = brand_dict['logo']
            if 'url' in brand_dict:
                brand_entity['url'] = brand_dict['url']

        self.client.create_or_update_entity(brand_entity)

        self._cache['brands'][brand_name] = brand_iri
        return {
            "@type": "Brand",
            "@id": brand_iri,
            "name": brand_name
        }

    def get_existing_entities_by_type(self, entity_type: str, limit: int = 1000) -> List[Dict[str, Any]]:
        """
        Get all existing entities of a specific type.

        Args:
            entity_type: Schema.org type (e.g., 'Organization', 'Person')
            limit: Maximum number to retrieve

        Returns:
            List of entities with iri and name
        """
        result = self.client.graphql_query(f"""
            query {{
              entities(
                query: {{
                  typeConstraint: {{ in: ["http://schema.org/{entity_type}"] }}
                }}
                rows: {limit}
              ) {{
                iri
                name: string(name: "schema:name")
              }}
            }}
        """)

        return result.get('entities', [])

    def preload_cache(self):
        """
        Preload cache with existing entities to speed up lookups.
        """
        print("Preloading entity cache...")

        # Load organizations
        orgs = self.get_existing_entities_by_type('Organization')
        for org in orgs:
            if org.get('name'):
                self._cache['organizations'][org['name']] = org['iri']
        print(f"  Loaded {len(orgs)} organizations")

        # Load people
        people = self.get_existing_entities_by_type('Person')
        for person in people:
            if person.get('name'):
                self._cache['people'][person['name']] = person['iri']
        print(f"  Loaded {len(people)} people")

        # Load brands
        brands = self.get_existing_entities_by_type('Brand')
        for brand in brands:
            if brand.get('name'):
                self._cache['brands'][brand['name']] = brand['iri']
        print(f"  Loaded {len(brands)} brands")

    def clear_cache(self):
        """Clear the entity cache."""
        self._cache = {
            'organizations': {},
            'people': {},
            'brands': {},
            'places': {}
        }


# Example usage
if __name__ == '__main__':
    import os

    api_key = os.environ.get('WORDLIFT_API_KEY')
    dataset_uri = "https://data.wordlift.io/wl123"

    client = WordLiftClient(api_key)
    reuse_manager = EntityReuseManager(client, dataset_uri)

    # Preload cache for faster lookups
    reuse_manager.preload_cache()

    # Get or create organization
    publisher_iri = reuse_manager.get_or_create_organization({
        'name': 'Example Publisher',
        'url': 'https://example.com',
        'logo': 'https://example.com/logo.png'
    })

    print(f"Publisher IRI: {publisher_iri}")

    # Get or create brand (will reuse if already exists)
    brand = reuse_manager.get_or_create_brand('Nike')
    print(f"Brand: {brand}")