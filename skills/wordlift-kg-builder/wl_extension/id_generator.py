#!/usr/bin/env python3
"""
ID Generation Utilities for WordLift Knowledge Graph
Generates deterministic, dereferenceable IRIs for entities.
"""

import hashlib
import re
from typing import Optional


def normalize_gtin(gtin: str) -> str:
    """
    Normalize GTIN to 14 digits (GTIN-14 format).
    Left-pads with zeros and validates check digit.

    Args:
        gtin: GTIN string (can be 8, 12, 13, or 14 digits)

    Returns:
        Normalized 14-digit GTIN

    Raises:
        ValueError: If GTIN is invalid
    """
    # Remove any non-digit characters
    gtin = re.sub(r'\D', '', gtin)

    # Validate length
    if len(gtin) not in [8, 12, 13, 14]:
        raise ValueError(f"Invalid GTIN length: {len(gtin)}. Must be 8, 12, 13, or 14 digits.")

    # Left-pad to 14 digits
    gtin_14 = gtin.zfill(14)

    # Validate check digit
    if not validate_gtin_check_digit(gtin_14):
        raise ValueError(f"Invalid GTIN check digit: {gtin_14}")

    return gtin_14


def validate_gtin_check_digit(gtin: str) -> bool:
    """
    Validate GTIN check digit using GS1 algorithm.

    Args:
        gtin: 14-digit GTIN string

    Returns:
        True if check digit is valid
    """
    if len(gtin) != 14:
        return False

    # Calculate check digit
    digits = [int(d) for d in gtin[:-1]]  # All except check digit

    # Alternate multiplying by 3 and 1 from right to left
    total = sum(d * (3 if i % 2 == 0 else 1) for i, d in enumerate(reversed(digits)))

    # Check digit is what makes total divisible by 10
    calculated_check = (10 - (total % 10)) % 10
    actual_check = int(gtin[-1])

    return calculated_check == actual_check


def generate_product_id(dataset_uri: str, gtin: str, serial: Optional[str] = None, lot: Optional[str] = None) -> str:
    """
    Generate GS1 Digital Link identifier for a product.

    Format: {dataset_uri}/01/{GTIN-14}[/21/{serial}][/10/{lot}]

    Args:
        dataset_uri: Base dataset URI (HTTPS, no trailing slash)
        gtin: GTIN (will be normalized to GTIN-14)
        serial: Optional serial number
        lot: Optional lot/batch number

    Returns:
        GS1 Digital Link identifier

    Example:
        >>> generate_product_id("https://example.com", "12345678901231")
        'https://example.com/01/00012345678901231'

        >>> generate_product_id("https://example.com", "12345678901231", serial="ABC123")
        'https://example.com/01/00012345678901231/21/ABC123'
    """
    # Ensure dataset_uri has no trailing slash
    dataset_uri = dataset_uri.rstrip('/')

    # Normalize GTIN to 14 digits
    gtin_14 = normalize_gtin(gtin)

    # Build Digital Link path
    path = f"{dataset_uri}/01/{gtin_14}"

    if serial:
        path += f"/21/{serial}"

    if lot:
        path += f"/10/{lot}"

    return path


def generate_slug(text: str) -> str:
    """
    Generate URL-friendly slug from text.

    Args:
        text: Text to convert to slug

    Returns:
        URL-friendly slug (lowercase, hyphenated)

    Example:
        >>> generate_slug("Acme Corporation")
        'acme-corporation'
        >>> generate_slug("New York")
        'new-york'
    """
    # Convert to lowercase
    slug = text.lower()

    # Replace spaces and underscores with hyphens
    slug = re.sub(r'[\s_]+', '-', slug)

    # Remove non-alphanumeric characters (except hyphens)
    slug = re.sub(r'[^a-z0-9-]', '', slug)

    # Remove consecutive hyphens
    slug = re.sub(r'-+', '-', slug)

    # Remove leading/trailing hyphens
    slug = slug.strip('-')

    return slug


def generate_entity_id(dataset_uri: str, entity_class: str, natural_key: str) -> str:
    """
    Generate slug-based identifier for non-product entities.

    Format: {dataset_uri}/{entity_class}/{slug}

    Args:
        dataset_uri: Base dataset URI (HTTPS, no trailing slash)
        entity_class: Entity class name (e.g., 'organization', 'person', 'webpage')
        natural_key: Natural key or unique identifier for the entity

    Returns:
        Slug-based entity identifier

    Example:
        >>> generate_entity_id("https://data.wordlift.io/wl123", "organization", "Acme Corp")
        'https://data.wordlift.io/wl123/organization/acme-corp'
        >>> generate_entity_id("https://data.wordlift.io/wl123", "person", "John Doe")
        'https://data.wordlift.io/wl123/person/john-doe'
    """
    # Ensure dataset_uri has no trailing slash
    dataset_uri = dataset_uri.rstrip('/')

    # Convert entity_class to lowercase
    entity_class = entity_class.lower()

    # Generate slug from natural key
    slug = generate_slug(natural_key)

    return f"{dataset_uri}/{entity_class}/{slug}"


def extract_gtin_from_url(url: str) -> Optional[str]:
    """
    Extract GTIN from a GS1 Digital Link URL.

    Args:
        url: URL potentially containing a GTIN in Digital Link format

    Returns:
        Extracted GTIN or None

    Example:
        >>> extract_gtin_from_url("https://example.com/01/00012345678901231")
        '00012345678901231'
    """
    # Match GS1 Digital Link pattern: /01/{14-digit-gtin}
    match = re.search(r'/01/(\d{14})', url)
    if match:
        return match.group(1)
    return None


def is_product_url(url: str) -> bool:
    """
    Check if a URL is a GS1 Digital Link product URL.

    Args:
        url: URL to check

    Returns:
        True if URL contains GS1 Digital Link product identifier
    """
    return extract_gtin_from_url(url) is not None


if __name__ == '__main__':
    # Example usage
    dataset_uri = "https://data.wordlift.io/wl123"

    # Product with GTIN
    product_id = generate_product_id(dataset_uri, "12345678901231")
    print(f"Product ID: {product_id}")

    # Product with GTIN and serial
    product_id_serial = generate_product_id(dataset_uri, "12345678901231", serial="SN123")
    print(f"Product ID with serial: {product_id_serial}")

    # Non-product entity (slug-based)
    org_id = generate_entity_id(dataset_uri, "organization", "Acme Corporation")
    print(f"Organization ID: {org_id}")

    # Person entity
    person_id = generate_entity_id(dataset_uri, "person", "John Doe")
    print(f"Person ID: {person_id}")

    # Extract GTIN from URL
    gtin = extract_gtin_from_url(product_id)
    print(f"Extracted GTIN: {gtin}")