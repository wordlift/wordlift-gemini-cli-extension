#!/usr/bin/env python3
"""
WordLift API Client
Handles interaction with WordLift's GraphQL and REST APIs.
"""

import requests
import json
from typing import Dict, List, Optional, Any


class WordLiftClient:
    """Client for interacting with WordLift APIs."""

    def __init__(self, api_key: str, base_url: str = "https://api.wordlift.io"):
        """
        Initialize WordLift client.

        Args:
            api_key: WordLift API key
            base_url: Base URL for WordLift API
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.headers = {
            "Authorization": f"Key {api_key}",
            "Content-Type": "application/json"
        }

    def import_from_sitemap(self, sitemap_url: str) -> List[Dict[str, Any]]:
        """
        Import URLs from a sitemap.xml file.

        API Endpoint: POST https://api.wordlift.io/sitemap-imports

        Args:
            sitemap_url: URL to the sitemap.xml file

        Returns:
            List of imported page data (parsed from NDJSON response)

        Raises:
            requests.HTTPError: If the API request fails

        Example:
            >>> client = WordLiftClient(api_key)
            >>> results = client.import_from_sitemap("https://example.com/sitemap.xml")
            >>> print(f"Imported {len(results)} pages")
        """
        url = f"{self.base_url}/sitemap-imports"

        payload = {"sitemap_url": sitemap_url}

        try:
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
        except requests.HTTPError as e:
            error_msg = f"Sitemap import failed: {e}"
            if response.status_code == 404:
                error_msg += f"\nEndpoint used: {url}"
                error_msg += "\nNote: Correct endpoint is https://api.wordlift.io/sitemap-imports"
            try:
                error_detail = response.json()
                error_msg += f"\nAPI Response: {error_detail}"
            except:
                error_msg += f"\nAPI Response: {response.text}"
            raise requests.HTTPError(error_msg)

        # Parse NDJSON response (each line is a separate JSON object)
        results = []
        for line in response.text.strip().split('\n'):
            if line:
                try:
                    results.append(json.loads(line))
                except json.JSONDecodeError as e:
                    print(f"Warning: Failed to parse line: {line[:100]}... Error: {e}")

        return results

    def import_from_urls(self, urls: List[str]) -> List[Dict[str, Any]]:
        """
        Import specific URLs directly.

        API Endpoint: POST https://api.wordlift.io/sitemap-imports

        Args:
            urls: List of URLs to import

        Returns:
            List of imported page data (parsed from NDJSON response)

        Raises:
            requests.HTTPError: If the API request fails

        Example:
            >>> client = WordLiftClient(api_key)
            >>> results = client.import_from_urls([
            ...     "https://example.com/page1.html",
            ...     "https://example.com/page2.html"
            ... ])
        """
        url = f"{self.base_url}/sitemap-imports"

        payload = {"urls": urls}

        try:
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
        except requests.HTTPError as e:
            error_msg = f"URL import failed: {e}"
            if response.status_code == 404:
                error_msg += f"\nEndpoint used: {url}"
                error_msg += "\nNote: Correct endpoint is https://api.wordlift.io/sitemap-imports"
            try:
                error_detail = response.json()
                error_msg += f"\nAPI Response: {error_detail}"
            except:
                error_msg += f"\nAPI Response: {response.text}"
            raise requests.HTTPError(error_msg)

        # Parse NDJSON response
        results = []
        for line in response.text.strip().split('\n'):
            if line:
                try:
                    results.append(json.loads(line))
                except json.JSONDecodeError as e:
                    print(f"Warning: Failed to parse line: {line[:100]}... Error: {e}")

        return results

    def graphql_query(self, query: str, variables: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Execute a GraphQL query against WordLift KG.

        Args:
            query: GraphQL query string
            variables: Optional query variables

        Returns:
            Query response data

        Raises:
            requests.HTTPError: If request fails
        """
        url = f"{self.base_url}/graphql"

        payload = {"query": query}
        if variables:
            payload["variables"] = variables

        response = requests.post(url, headers=self.headers, json=payload)
        response.raise_for_status()

        result = response.json()

        if 'errors' in result:
            raise Exception(f"GraphQL errors: {result['errors']}")

        return result.get('data', {})

    def get_entities_by_type(self, entity_type: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get entities of a specific type from the KG.

        Args:
            entity_type: Schema.org type (e.g., 'Product', 'Organization')
            limit: Maximum number of entities to return

        Returns:
            List of entities
        """
        query = f"""
        query {{
          entities(
            query: {{ typeConstraint: {{ in: ["http://schema.org/{entity_type}"] }} }}
            page: 0
            rows: {limit}
          ) {{
            iri
            types: refs(name: "rdf:type")
            name: string(name: "schema:name")
            url: string(name: "schema:url")
          }}
        }}
        """

        result = self.graphql_query(query)
        return result.get('entities', [])

    def get_products(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get all products from the KG.

        Args:
            limit: Maximum number of products to return

        Returns:
            List of product entities
        """
        query = f"""
        query {{
          products(page: 0, rows: {limit}) {{
            iri
            name: string(name: "schema:name")
            gtin: string(name: "schema:gtin14")
            sku: string(name: "schema:sku")
            brand: resource(name: "schema:brand") {{
              name: string(name: "schema:name")
            }}
            price: resource(name: "schema:offers") {{
              price: string(name: "schema:price")
              currency: string(name: "schema:priceCurrency")
            }}
          }}
        }}
        """

        result = self.graphql_query(query)
        return result.get('products', [])

    def get_entity_by_url(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Get an entity by its URL.

        Args:
            url: Entity URL/IRI

        Returns:
            Entity data or None if not found
        """
        query = """
        query($url: String!) {
          entity(url: $url) {
            iri
            types: refs(name: "rdf:type")
            name: string(name: "schema:name")
            description: string(name: "schema:description")
          }
        }
        """

        try:
            result = self.graphql_query(query, variables={"url": url})
            return result.get('entity')
        except Exception:
            return None

    def entity_exists(self, entity_id: str) -> bool:
        """
        Check if an entity exists in the KG.

        Args:
            entity_id: Entity IRI

        Returns:
            True if entity exists
        """
        entity = self.get_entity_by_url(entity_id)
        return entity is not None

    def create_or_update_entity(self, entity: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create or update an entity using the /dataset endpoint.

        Args:
            entity: JSON-LD entity data

        Returns:
            Response data
        """
        if '@id' not in entity:
            raise ValueError("Entity must have an @id field")

        url = f"{self.base_url}/dataset"
        params = {
            "uri": entity['@id'],
            "private": False
        }

        headers = {
            "Authorization": f"Key {self.api_key}",
            "Content-Type": "application/ld+json"
        }

        response = requests.post(
            url,
            params=params,
            headers=headers,
            data=json.dumps(entity)
        )
        response.raise_for_status()

        return response.json() if response.text else {}

    def batch_create_or_update(self, entities: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Create or update multiple entities in a batch.

        Args:
            entities: List of JSON-LD entities

        Returns:
            Response data
        """
        url = f"{self.base_url}/dataset/batch"

        batch_data = []
        for entity in entities:
            if '@id' not in entity:
                raise ValueError(f"Entity must have an @id field: {entity}")

            batch_data.append({
                "uri": entity['@id'],
                "model": json.dumps(entity),
                "private": False
            })

        response = requests.post(url, headers=self.headers, json=batch_data)
        response.raise_for_status()

        return response.json()

    def patch_entity(self, entity_id: str, patches: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Patch an entity using JSON Patch operations.

        Args:
            entity_id: Entity IRI
            patches: List of JSON Patch operations
                Each operation is a dict with:
                - op: 'add', 'remove', 'replace', 'move', 'copy', or 'test'
                - path: JSON Pointer path (e.g., '/https://schema.org/image')
                - value: Value for the operation (for add, replace)

        Returns:
            Response data

        Example patches:
            [
                {"op": "add", "path": "/https://schema.org/image", "value": "https://example.com/image.jpg"},
                {"op": "replace", "path": "/https://schema.org/price", "value": "29.99"},
                {"op": "remove", "path": "/https://schema.org/oldProperty"}
            ]
        """
        url = f"{self.base_url}/entities"
        params = {"id": entity_id}

        headers = {
            "Authorization": f"Key {self.api_key}",
            "Content-Type": "application/json-patch+json"
        }

        response = requests.patch(url, params=params, headers=headers, json=patches)
        response.raise_for_status()

        return response.json() if response.text else {}

    def delete_entity(self, entity_id: str) -> None:
        """
        Delete an entity from the KG.

        Args:
            entity_id: Entity IRI
        """
        url = f"{self.base_url}/dataset"
        params = {"uri": entity_id}

        response = requests.delete(url, headers=self.headers, params=params)
        response.raise_for_status()

    def get_products_by_gtin_list(self, gtins: List[str]) -> List[Dict[str, Any]]:
        """
        Get products by a list of GTINs.

        Args:
            gtins: List of GTIN-14 strings

        Returns:
            List of matching products
        """
        # Build query with GTIN filter
        query = f"""
        query {{
          products(
            query: {{
              gtin14Constraint: {{ in: {json.dumps(gtins)} }}
            }}
            rows: {len(gtins)}
          ) {{
            iri
            name: string(name: "schema:name")
            gtin: string(name: "schema:gtin14")
            sku: string(name: "schema:sku")
            dateModified: string(name: "schema:dateModified")
          }}
        }}
        """

        result = self.graphql_query(query)
        return result.get('products', [])

    def get_all_product_gtins(self) -> List[str]:
        """
        Get all GTINs currently in the KG.

        Returns:
            List of GTIN-14 strings
        """
        query = """
        query {
          products(rows: 10000) {
            gtin: string(name: "schema:gtin14")
          }
        }
        """

        result = self.graphql_query(query)
        products = result.get('products', [])

        return [p['gtin'] for p in products if p.get('gtin')]


if __name__ == '__main__':
    import os

    # Example usage
    api_key = os.environ.get('WORDLIFT_API_KEY')
    if not api_key:
        print("Set WORDLIFT_API_KEY environment variable")
        exit(1)

    client = WordLiftClient(api_key)

    # Get products
    products = client.get_products(limit=10)
    print(f"Found {len(products)} products")
    for product in products:
        print(f"  - {product.get('name')} (GTIN: {product.get('gtin')})")