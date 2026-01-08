#!/usr/bin/env python3
"""
Entity Verification Utility
Verifies that entities are actually persisted in the Knowledge Graph.

WordLift can return 200 OK for entity creation even when using invalid IRI patterns.
This utility provides comprehensive verification methods to ensure entities are truly persisted.
"""

import time
import requests
from typing import Dict, Any, Tuple, Optional
from wordlift_client import WordLiftClient


def verify_entity_persisted(iri: str, wait_seconds: int = 2) -> Tuple[bool, str]:
    """
    Verify entity is actually persisted in Knowledge Graph.

    WordLift can accept invalid IRI patterns (return 200 OK) but not persist them.
    This function checks if an entity is truly accessible.

    Args:
        iri: The entity IRI to verify
        wait_seconds: Seconds to wait before checking (for async processing)

    Returns:
        Tuple of (is_persisted, message)

    Example:
        >>> is_persisted, msg = verify_entity_persisted(
        ...     "https://data.wordlift.io/wl123/destination/venice"
        ... )
        >>> if not is_persisted:
        ...     print(f"Failed: {msg}")
    """
    # Wait for async processing
    if wait_seconds > 0:
        time.sleep(wait_seconds)

    # Test 1: Check .html is accessible
    try:
        response = requests.get(f"{iri}.html", timeout=10)

        if response.status_code != 200:
            return False, f"HTML endpoint returned {response.status_code}"

        if "No local triples" in response.text:
            return False, "Entity not persisted (no local triples)"

    except requests.RequestException as e:
        return False, f"HTML endpoint error: {e}"

    # Test 2: Check .json has data
    try:
        response = requests.get(f"{iri}.json", timeout=10)

        if response.status_code != 200:
            return False, f"JSON endpoint returned {response.status_code}"

        data = response.json()

        if not data or len(data) == 0:
            return False, "JSON endpoint returned empty data"

    except requests.RequestException as e:
        return False, f"JSON endpoint error: {e}"
    except ValueError as e:
        return False, f"Invalid JSON response: {e}"

    return True, "Entity successfully persisted and dereferenceable"


def verify_via_graphql(client: WordLiftClient, iri: str,
                       wait_seconds: int = 5) -> Tuple[bool, str, Optional[Dict]]:
    """
    Verify entity is indexed in GraphQL.

    Note: GraphQL index updates asynchronously (1-5 minutes typical).
    Use verify_entity_persisted() first for immediate verification.

    Args:
        client: WordLift API client
        iri: The entity IRI to verify
        wait_seconds: Seconds to wait for indexing

    Returns:
        Tuple of (is_indexed, message, entity_data)
    """
    if wait_seconds > 0:
        time.sleep(wait_seconds)

    try:
        result = client.graphql_query('''
            query($iri: Ref!) {
                resource(iri: $iri) {
                    iri
                    name: string(name: "schema:name")
                    type: refs(name: "rdf:type")
                }
            }
        ''', {"iri": iri})

        entity = result.get('resource')

        if not entity:
            return False, "Entity not found in GraphQL index", None

        return True, "Entity indexed in GraphQL", entity

    except Exception as e:
        return False, f"GraphQL query error: {e}", None


def verify_entity_complete(client: WordLiftClient, iri: str,
                          check_graphql: bool = True) -> Dict[str, Any]:
    """
    Run complete verification suite on an entity.

    Args:
        client: WordLift API client
        iri: The entity IRI to verify
        check_graphql: Whether to check GraphQL indexing (slower)

    Returns:
        Dictionary with verification results
    """
    results = {
        'iri': iri,
        'persisted': False,
        'dereferenceable': False,
        'graphql_indexed': False,
        'messages': []
    }

    # Check dereferenceability
    is_persisted, msg = verify_entity_persisted(iri)
    results['persisted'] = is_persisted
    results['dereferenceable'] = is_persisted
    results['messages'].append(f"Dereferenceability: {msg}")

    if not is_persisted:
        results['messages'].append("⚠️  Entity not persisted - check IRI pattern")
        return results

    # Check GraphQL indexing
    if check_graphql:
        is_indexed, msg, entity = verify_via_graphql(client, iri)
        results['graphql_indexed'] = is_indexed
        results['messages'].append(f"GraphQL: {msg}")

        if entity:
            results['entity_data'] = entity

    return results


def check_iri_pattern(iri: str) -> Tuple[bool, str]:
    """
    Check if IRI follows valid WordLift path patterns.

    Valid patterns:
    - /01/{GTIN-14} for products
    - /organization/{slug}
    - /place/{slug}
    - /person/{slug}
    - /destination/{slug}
    - /article/{slug}

    Args:
        iri: The IRI to check

    Returns:
        Tuple of (is_valid, message)
    """
    # Extract path from IRI
    if '//' not in iri:
        return False, "Invalid IRI format"

    path = iri.split('//', 1)[1]  # Remove protocol
    if '/' not in path:
        return False, "No path in IRI"

    path = '/' + '/'.join(path.split('/')[2:])  # Remove domain, keep path

    valid_patterns = [
        '/01/',  # Products (GS1 Digital Link)
        '/organization/',
        '/place/',
        '/person/',
        '/destination/',
        '/article/',
        '/webpage/',
        '/brand/',
        '/event/',
        '/service/'
    ]

    for pattern in valid_patterns:
        if pattern in path:
            # Additional validation for products
            if pattern == '/01/':
                # Should be /01/GTIN-14
                parts = path.split('/01/')
                if len(parts) == 2:
                    gtin = parts[1].split('/')[0]
                    if len(gtin) == 14 and gtin.isdigit():
                        return True, f"Valid product IRI (GS1 Digital Link)"
                    else:
                        return False, f"Invalid GTIN-14 in product IRI: {gtin}"

            return True, f"Valid IRI pattern: {pattern}"

    # Check for invalid patterns
    if '/sejour/' in path or '/country/' in path:
        return False, "Invalid pattern: auto-generated from sitemap (e.g., /sejour/country/)"

    if path.count('/') > 3:
        return False, "Invalid pattern: too many nested paths"

    return False, "IRI pattern not recognized - may not be persisted"


# Example usage
if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("Usage: python entity_verifier.py <IRI> [API_KEY]")
        sys.exit(1)

    iri = sys.argv[1]
    api_key = sys.argv[2] if len(sys.argv) > 2 else None

    print(f"Verifying entity: {iri}\n")

    # Check IRI pattern
    is_valid_pattern, pattern_msg = check_iri_pattern(iri)
    print(f"IRI Pattern: {pattern_msg}")
    if not is_valid_pattern:
        print("⚠️  Warning: IRI may not be persisted due to invalid pattern\n")

    # Check dereferenceability
    print("\nChecking dereferenceability...")
    is_persisted, msg = verify_entity_persisted(iri)
    print(f"Result: {msg}")

    if is_persisted:
        print("✓ Entity is persisted and dereferenceable")
    else:
        print("✗ Entity is NOT persisted")
        sys.exit(1)

    # Check GraphQL (if API key provided)
    if api_key:
        print("\nChecking GraphQL indexing...")
        client = WordLiftClient(api_key)
        is_indexed, msg, entity = verify_via_graphql(client, iri, wait_seconds=10)
        print(f"Result: {msg}")

        if is_indexed and entity:
            print(f"  Entity: {entity.get('name', 'Unknown')}")
            print(f"  Types: {entity.get('type', [])}")
        elif not is_indexed:
            print("  Note: GraphQL indexing can take 1-5 minutes")