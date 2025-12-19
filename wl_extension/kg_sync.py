#!/usr/bin/env python3
"""
Knowledge Graph Sync Orchestration
Main script for syncing product data to WordLift KG with daily updates.
"""

import json
import argparse
from pathlib import Path
from typing import List, Dict, Any, Set
from datetime import datetime

try:
    from .wordlift_client import WordLiftClient
    from .entity_builder import EntityBuilder, create_product_from_scraped_data
    from .id_generator import generate_product_id, normalize_gtin
except (ImportError, ValueError):
    from wordlift_client import WordLiftClient
    from entity_builder import EntityBuilder, create_product_from_scraped_data
    from id_generator import generate_product_id, normalize_gtin


class KGSyncOrchestrator:
    """Orchestrates syncing data to WordLift Knowledge Graph."""

    def __init__(self, api_key: str, dataset_uri: str, context_description: Optional[str] = None,
                 enable_validation: bool = True, enable_reuse: bool = True):
        """
        Initialize the sync orchestrator.

        Args:
            api_key: WordLift API key
            dataset_uri: Base dataset URI for generating IDs
            context_description: Optional context description
            enable_validation: Enable SHACL validation before upload
            enable_reuse: Enable entity reuse (check for existing entities)
        """
        self.client = WordLiftClient(api_key)
        self.dataset_uri = dataset_uri
        self.enable_validation = enable_validation
        self.enable_reuse = enable_reuse

        # Initialize reuse manager if enabled
        if enable_reuse:
            try:
                from .entity_reuse import EntityReuseManager
            except (ImportError, ValueError):
                from entity_reuse import EntityReuseManager
            self.reuse_manager = EntityReuseManager(self.client, dataset_uri)
            self.reuse_manager.preload_cache()
        else:
            self.reuse_manager = None

        # Initialize entity builder with reuse manager
        self.builder = EntityBuilder(dataset_uri, context_description, self.reuse_manager)

    def sync_products_from_file(self, input_file: str, batch_size: int = 50) -> Dict[str, Any]:
        """
        Sync products from a JSON file to the KG.

        Args:
            input_file: Path to JSON file with product data
            batch_size: Number of products to batch together

        Returns:
            Dictionary with sync statistics
        """
        print(f"Loading products from {input_file}...")
        with open(input_file, 'r') as f:
            products_data = json.load(f)

        if not isinstance(products_data, list):
            products_data = [products_data]

        return self.sync_products(products_data, batch_size)

    def sync_products(self, products_data: List[Dict[str, Any]], batch_size: int = 50) -> Dict[str, Any]:
        """
        Sync a list of products to the KG.

        Args:
            products_data: List of product data dictionaries
            batch_size: Number of products to batch together

        Returns:
            Dictionary with sync statistics
        """
        stats = {
            'total': len(products_data),
            'created': 0,
            'updated': 0,
            'errors': 0,
            'skipped': 0
        }

        # Get existing GTINs from KG
        print("Fetching existing products from KG...")
        existing_gtins = set(self.client.get_all_product_gtins())
        print(f"Found {len(existing_gtins)} existing products")

        # Process products in batches
        batches = [products_data[i:i + batch_size] for i in range(0, len(products_data), batch_size)]

        for batch_idx, batch in enumerate(batches):
            print(f"\nProcessing batch {batch_idx + 1}/{len(batches)} ({len(batch)} products)...")

            to_create = []
            to_update = []

            for product_data in batch:
                try:
                    # Build JSON-LD entity
                    entity = create_product_from_scraped_data(self.dataset_uri, product_data)

                    # Check if product exists
                    gtin_14 = entity['gtin14']

                    if gtin_14 in existing_gtins:
                        to_update.append(entity)
                    else:
                        to_create.append(entity)

                except Exception as e:
                    print(f"  Error processing product: {e}")
                    stats['errors'] += 1

            # Validate entities before upload
            if self.enable_validation:
                try:
                    from .shacl_validator import SHACLValidator
                except (ImportError, ValueError):
                    from shacl_validator import SHACLValidator
                validator = SHACLValidator()

                all_entities = to_create + to_update
                if all_entities:
                    print(f"  Validating {len(all_entities)} entities...")
                    results = validator.validate_batch(all_entities, strict=False)

                    if results['invalid'] > 0:
                        print(f"  ⚠ Warning: {results['invalid']} entities failed validation")
                        # Filter out invalid entities
                        valid_indices = [e['index'] for e in results['entities'] if e['valid']]
                        all_entities_validated = [all_entities[i] for i in valid_indices]

                        # Recalculate to_create and to_update from validated entities
                        to_create = [e for e in all_entities_validated if normalize_gtin(e['gtin14']) not in existing_gtins]
                        to_update = [e for e in all_entities_validated if normalize_gtin(e['gtin14']) in existing_gtins]

                        stats['errors'] += results['invalid']
                    else:
                        print(f"  ✓ All entities passed validation")

            # Create new products
            if to_create:
                try:
                    print(f"  Creating {len(to_create)} new products...")
                    self.client.batch_create_or_update(to_create)
                    stats['created'] += len(to_create)
                except Exception as e:
                    print(f"  Batch create error: {e}")
                    stats['errors'] += len(to_create)

            # Update existing products
            if to_update:
                try:
                    print(f"  Updating {len(to_update)} existing products...")
                    self.client.batch_create_or_update(to_update)
                    stats['updated'] += len(to_update)
                except Exception as e:
                    print(f"  Batch update error: {e}")
                    stats['errors'] += len(to_update)

        print("\n" + "="*50)
        print("Sync Complete!")
        print(f"Total products: {stats['total']}")
        print(f"Created: {stats['created']}")
        print(f"Updated: {stats['updated']}")
        print(f"Errors: {stats['errors']}")
        print(f"Skipped: {stats['skipped']}")
        print("="*50)

        return stats

    def incremental_update(self, products_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Perform an incremental update by patching only changed fields.
        More efficient than full entity replacement.

        Args:
            products_data: List of product data dictionaries

        Returns:
            Dictionary with update statistics
        """
        stats = {
            'total': len(products_data),
            'updated': 0,
            'no_changes': 0,
            'errors': 0
        }

        for product_data in products_data:
            try:
                # Build new entity
                new_entity = create_product_from_scraped_data(self.dataset_uri, product_data)
                entity_id = new_entity['@id']

                # Get existing entity
                existing = self.client.get_entity_by_url(entity_id)

                if not existing:
                    print(f"Product {entity_id} not found, skipping patch")
                    stats['errors'] += 1
                    continue

                # Generate patches for changed fields
                patches = self._generate_patches(existing, new_entity)

                if not patches:
                    print(f"No changes for {new_entity.get('name', entity_id)}")
                    stats['no_changes'] += 1
                    continue

                # Apply patches
                print(f"Patching {new_entity.get('name', entity_id)} ({len(patches)} changes)")
                self.client.patch_entity(entity_id, patches)
                stats['updated'] += 1

            except Exception as e:
                print(f"Error updating product: {e}")
                stats['errors'] += 1

        print("\n" + "="*50)
        print("Incremental Update Complete!")
        print(f"Total products: {stats['total']}")
        print(f"Updated: {stats['updated']}")
        print(f"No changes: {stats['no_changes']}")
        print(f"Errors: {stats['errors']}")
        print("="*50)

        return stats

    def _generate_patches(self, existing: Dict[str, Any], new: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate JSON Patch operations for changed fields.

        Args:
            existing: Existing entity data
            new: New entity data

        Returns:
            List of patch operations
        """
        patches = []

        # Fields to compare
        comparable_fields = [
            'schema:name', 'schema:description', 'schema:price',
            'schema:image', 'schema:sku', 'schema:availability'
        ]

        for field in comparable_fields:
            path = f"/https://{field.replace(':', '/')}"

            new_value = new.get(field.split(':')[1])
            existing_value = existing.get(field)

            if new_value != existing_value:
                if new_value is not None:
                    patches.append({
                        "op": "replace" if existing_value else "add",
                        "path": path,
                        "value": new_value
                    })
                elif existing_value:
                    patches.append({
                        "op": "remove",
                        "path": path
                    })

    def import_from_sitemap(self, sitemap_url: str) -> Dict[str, Any]:
        """
        Import pages from a sitemap using Sitemap Import API.

        Args:
            sitemap_url: URL to the XML sitemap

        Returns:
            Import statistics
        """
        print(f"Importing from sitemap: {sitemap_url}")

        try:
            results = self.client.import_from_sitemap(sitemap_url)

            stats = {
                'total': len(results),
                'success': sum(1 for r in results if r.get('status') == 'success'),
                'failed': sum(1 for r in results if r.get('status') != 'success')
            }

            print(f"\nImport complete!")
            print(f"  Total: {stats['total']}")
            print(f"  Success: {stats['success']}")
            print(f"  Failed: {stats['failed']}")

            return stats

        except Exception as e:
            print(f"Import failed: {e}")
            return {"error": str(e)}


def main():
    parser = argparse.ArgumentParser(description='Sync products to WordLift Knowledge Graph')
    parser.add_argument('--api-key', required=True, help='WordLift API key')
    parser.add_argument('--dataset-uri', required=True, help='Base dataset URI (e.g., https://data.wordlift.io/wl123)')
    parser.add_argument('--input', required=True, help='Input JSON file with product data')
    parser.add_argument('--batch-size', type=int, default=50, help='Batch size for uploads')
    parser.add_argument('--incremental', action='store_true', help='Use incremental patching instead of full updates')
    parser.add_argument('--context-description', help='Optional context description for the dataset')
    parser.add_argument('--no-validation', action='store_true', help='Disable SHACL validation before upload')
    parser.add_argument('--no-reuse', action='store_true', help='Disable entity reuse checking')

    args = parser.parse_args()

    orchestrator = KGSyncOrchestrator(
        api_key=args.api_key,
        dataset_uri=args.dataset_uri,
        context_description=args.context_description,
        enable_validation=not args.no_validation,
        enable_reuse=not args.no_reuse
    )

    if args.incremental:
        # Load products and do incremental update
        with open(args.input, 'r') as f:
            products_data = json.load(f)
        if not isinstance(products_data, list):
            products_data = [products_data]
        orchestrator.incremental_update(products_data)
    else:
        # Full sync
        orchestrator.sync_products_from_file(args.input, args.batch_size)


if __name__ == '__main__':
    main()