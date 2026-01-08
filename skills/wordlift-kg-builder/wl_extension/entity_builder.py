#!/usr/bin/env python3
"""
JSON-LD Entity Builder for WordLift Knowledge Graph
Creates properly structured JSON-LD entities with correct IDs.
"""

import json
from typing import Dict, List, Optional, Any
from datetime import datetime
try:
    from .id_generator import generate_product_id, generate_entity_id, normalize_gtin, generate_slug
except (ImportError, ValueError):
    from id_generator import generate_product_id, generate_entity_id, normalize_gtin, generate_slug


class EntityBuilder:
    """Builds JSON-LD entities with proper structure and IDs."""

    def __init__(self, dataset_uri: str, context_description: Optional[str] = None, reuse_manager=None):
        """
        Initialize entity builder.

        Args:
            dataset_uri: Base dataset URI (HTTPS, no trailing slash)
            context_description: Optional description of the dataset context
            reuse_manager: Optional EntityReuseManager for reusing existing entities
        """
        self.dataset_uri = dataset_uri.rstrip('/')
        self.context_description = context_description
        self.reuse_manager = reuse_manager

    def build_product(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build a Product entity with GS1 Digital Link ID.

        Args:
            data: Dictionary containing product data with keys:
                - gtin: Required GTIN
                - name: Product name
                - description: Product description
                - brand: Brand name or dict with brand info
                - image: Image URL or list of URLs
                - offers: Offer data (price, currency, availability)
                - sku: SKU
                - serial: Optional serial number
                - lot: Optional lot/batch number
                - additional fields...

        Returns:
            JSON-LD Product entity
        """
        if 'gtin' not in data:
            raise ValueError("Product must have a 'gtin' field")

        # Generate GS1 Digital Link ID
        product_id = generate_product_id(
            self.dataset_uri,
            data['gtin'],
            serial=data.get('serial'),
            lot=data.get('lot')
        )

        # Normalize GTIN for storage
        gtin_14 = normalize_gtin(data['gtin'])

        # Build base product entity
        entity = {
            "@context": "https://schema.org",
            "@type": "Product",
            "@id": product_id,
            "gtin14": gtin_14,
        }

        # Add name
        if 'name' in data:
            entity['name'] = data['name']

        # Add description
        if 'description' in data:
            entity['description'] = data['description']

        # Add SKU
        if 'sku' in data:
            entity['sku'] = data['sku']

        # Add brand
        if 'brand' in data:
            entity['brand'] = self._build_brand(data['brand'])

        # Add image(s)
        if 'image' in data:
            entity['image'] = data['image'] if isinstance(data['image'], list) else [data['image']]

        # Add offers
        if 'offers' in data:
            entity['offers'] = self._build_offer(data['offers'])
        elif 'price' in data:
            entity['offers'] = self._build_offer({
                'price': data['price'],
                'priceCurrency': data.get('currency', data.get('priceCurrency', 'USD')),
                'availability': data.get('availability', 'https://schema.org/InStock')
            })

        # Add aggregateRating if present
        if 'aggregateRating' in data:
            entity['aggregateRating'] = data['aggregateRating']
        elif 'rating' in data or 'ratingValue' in data:
            entity['aggregateRating'] = {
                "@type": "AggregateRating",
                "ratingValue": data.get('rating', data.get('ratingValue')),
                "reviewCount": data.get('reviewCount', data.get('review_count'))
            }

        # Add additional properties
        additional_fields = ['mpn', 'model', 'color', 'size', 'weight', 'width', 'height', 'depth']
        for field in additional_fields:
            if field in data:
                entity[field] = data[field]

        return entity

    def _build_brand(self, brand_data: Any) -> Dict[str, Any]:
        """Build a Brand entity."""
        # If reuse manager is available, use it to get or create brand
        if self.reuse_manager:
            return self.reuse_manager.get_or_create_brand(brand_data)

        # Otherwise, build brand inline
        if isinstance(brand_data, str):
            # Simple brand name
            brand_id = generate_entity_id(self.dataset_uri, "brand", brand_data)
            return {
                "@type": "Brand",
                "@id": brand_id,
                "name": brand_data
            }
        elif isinstance(brand_data, dict):
            # Brand with more details
            if '@id' not in brand_data and 'name' in brand_data:
                brand_data['@id'] = generate_entity_id(self.dataset_uri, "brand", brand_data['name'])
            if '@type' not in brand_data:
                brand_data['@type'] = "Brand"
            return brand_data
        return brand_data

    def _build_offer(self, offer_data: Dict[str, Any]) -> Dict[str, Any]:
        """Build an Offer entity."""
        offer = {
            "@type": "Offer",
        }

        if 'price' in offer_data:
            offer['price'] = str(offer_data['price'])

        if 'priceCurrency' in offer_data:
            offer['priceCurrency'] = offer_data['priceCurrency']

        if 'availability' in offer_data:
            # Ensure availability is a schema.org URL
            availability = offer_data['availability']
            if not availability.startswith('http'):
                # Convert common values to schema.org URLs
                availability_map = {
                    'InStock': 'https://schema.org/InStock',
                    'OutOfStock': 'https://schema.org/OutOfStock',
                    'PreOrder': 'https://schema.org/PreOrder',
                    'Discontinued': 'https://schema.org/Discontinued',
                }
                offer['availability'] = availability_map.get(availability, f'https://schema.org/{availability}')
            else:
                offer['availability'] = availability

        if 'url' in offer_data:
            offer['url'] = offer_data['url']

        if 'seller' in offer_data:
            offer['seller'] = offer_data['seller']

        return offer

    def build_organization(self, data: Dict[str, Any], natural_key: Optional[str] = None) -> Dict[str, Any]:
        """
        Build an Organization entity.

        Args:
            data: Dictionary containing organization data
            natural_key: Natural key for ID generation (defaults to name)

        Returns:
            JSON-LD Organization entity
        """
        if not natural_key and 'name' not in data:
            raise ValueError("Organization must have a 'name' or natural_key")

        natural_key = natural_key or data['name']
        org_id = generate_entity_id(self.dataset_uri, "Organization", natural_key)

        entity = {
            "@context": "https://schema.org",
            "@type": "Organization",
            "@id": org_id,
        }

        # Add common Organization properties
        org_fields = ['name', 'url', 'logo', 'description', 'email', 'telephone', 'address']
        for field in org_fields:
            if field in data:
                entity[field] = data[field]

        return entity

    def build_webpage(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build a WebPage entity with slug-based ID.

        Args:
            data: Dictionary containing webpage data with:
                - url: Required page URL
                - name or headline: Page title
                - slug: Optional custom slug (otherwise generated from URL or title)
                - Other WebPage properties

        Returns:
            JSON-LD WebPage entity
        """
        if 'url' not in data:
            raise ValueError("WebPage must have a 'url' field")

        # Generate slug for the ID
        if 'slug' in data:
            slug = data['slug']
        elif 'name' in data:
            # Use name/title to generate slug
            slug = generate_slug(data['name'])
        elif 'headline' in data:
            slug = generate_slug(data['headline'])
        else:
            # Extract from URL path as fallback
            from urllib.parse import urlparse
            parsed = urlparse(data['url'])
            path = parsed.path.strip('/')
            if path:
                # Use the last segment of the path
                slug = path.split('/')[-1]
                # Remove file extensions
                slug = slug.split('.')[0]
            else:
                # Homepage or no path
                slug = 'homepage'

        # Generate ID using slug
        try:
            from .id_generator import generate_entity_id
        except (ImportError, ValueError):
            from id_generator import generate_entity_id
        webpage_id = generate_entity_id(self.dataset_uri, "webpage", slug)

        # Build entity
        entity = {
            "@context": "https://schema.org",
            "@type": data.get('@type', "WebPage"),
            "@id": webpage_id,
            "url": data['url'],
        }

        # Add common WebPage properties
        webpage_fields = ['name', 'headline', 'description', 'datePublished',
                         'dateModified', 'author', 'publisher', 'image', 'mainEntity']
        for field in webpage_fields:
            if field in data:
                entity[field] = data[field]

        return entity

    def build_batch_request(self, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Build a batch request for creating/updating multiple entities.

        Args:
            entities: List of JSON-LD entities

        Returns:
            List of batch request objects
        """
        batch = []
        for entity in entities:
            if '@id' not in entity:
                raise ValueError("All entities must have an @id field")

            batch.append({
                "uri": entity['@id'],
                "model": json.dumps(entity),
                "private": False  # Set to True if entities should be private
            })

        return batch


def create_product_from_scraped_data(dataset_uri: str, scraped_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Helper function to create a product entity from scraped webpage data.

    Args:
        dataset_uri: Base dataset URI
        scraped_data: Dictionary with scraped product data

    Returns:
        JSON-LD Product entity
    """
    builder = EntityBuilder(dataset_uri)

    # Map common scraped field names to expected format
    product_data = {}

    # GTIN extraction (try multiple possible field names)
    for gtin_field in ['gtin', 'gtin13', 'gtin14', 'gtin12', 'gtin8', 'ean', 'upc']:
        if gtin_field in scraped_data and scraped_data[gtin_field]:
            product_data['gtin'] = scraped_data[gtin_field]
            break

    if 'gtin' not in product_data:
        raise ValueError("No GTIN found in scraped data")

    # Map other fields
    field_mappings = {
        'name': ['name', 'title', 'product_name'],
        'description': ['description', 'product_description'],
        'sku': ['sku', 'product_sku'],
        'brand': ['brand', 'product_brand', 'manufacturer'],
        'image': ['image', 'product_image', 'images'],
        'price': ['price', 'product_price'],
        'currency': ['currency', 'priceCurrency', 'product_currency'],
        'availability': ['availability', 'product_availability', 'stock_status'],
        'rating': ['rating', 'ratingValue', 'product_rating'],
        'reviewCount': ['reviewCount', 'review_count', 'product_review_count'],
    }

    for target_field, source_fields in field_mappings.items():
        for source_field in source_fields:
            if source_field in scraped_data and scraped_data[source_field]:
                product_data[target_field] = scraped_data[source_field]
                break

    return builder.build_product(product_data)


if __name__ == '__main__':
    # Example usage
    dataset_uri = "https://example.com"
    builder = EntityBuilder(dataset_uri, "Product catalog for Example.com")

    # Build a product
    product = builder.build_product({
        'gtin': '12345678901231',
        'name': 'Example Product',
        'description': 'A great product',
        'brand': 'Example Brand',
        'price': '29.99',
        'currency': 'USD',
        'image': 'https://example.com/image.jpg',
        'sku': 'EX-001'
    })

    print(json.dumps(product, indent=2))