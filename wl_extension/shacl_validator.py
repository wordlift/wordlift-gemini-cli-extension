#!/usr/bin/env python3
"""
SHACL Validator for WordLift Knowledge Graph
Validates JSON-LD entities against SHACL shapes before upload.
"""

import json
from typing import Dict, List, Any, Tuple, Optional
from pathlib import Path


class SHACLValidator:
    """Validates JSON-LD entities against SHACL shapes."""

    def __init__(self, shapes_file: Optional[str] = None):
        """
        Initialize SHACL validator.

        Args:
            shapes_file: Path to SHACL shapes file (Turtle or JSON-LD format)
        """
        self.shapes = self._load_default_shapes()

        if shapes_file:
            self.load_shapes_file(shapes_file)

    def _load_default_shapes(self) -> Dict[str, Any]:
        """Load default SHACL shapes for common schema.org types."""
        return {
            "Product": {
                "required": ["@id", "@type", "name", "gtin14"],
                "recommended": ["description", "brand", "offers", "image"],
                "constraints": {
                    "@type": lambda v: v == "Product",
                    "gtin14": lambda v: isinstance(v, str) and len(v) == 14 and v.isdigit(),
                    "name": lambda v: isinstance(v, str) and len(v) > 0,
                    "offers": lambda v: isinstance(v, dict) and v.get("@type") == "Offer"
                }
            },
            "Organization": {
                "required": ["@id", "@type", "name"],
                "recommended": ["url", "logo", "description"],
                "constraints": {
                    "@type": lambda v: v == "Organization",
                    "name": lambda v: isinstance(v, str) and len(v) > 0,
                    "url": lambda v: isinstance(v, str) and v.startswith("http")
                }
            },
            "Person": {
                "required": ["@id", "@type", "name"],
                "recommended": ["jobTitle", "email"],
                "constraints": {
                    "@type": lambda v: v == "Person",
                    "name": lambda v: isinstance(v, str) and len(v) > 0
                }
            },
            "WebPage": {
                "required": ["@id", "@type", "url", "name"],
                "recommended": ["description", "datePublished"],
                "constraints": {
                    "@type": lambda v: v in ["WebPage", "Article", "BlogPosting"],
                    "url": lambda v: isinstance(v, str) and v.startswith("http"),
                    "name": lambda v: isinstance(v, str) and len(v) > 0
                }
            },
            "Offer": {
                "required": ["@type", "price", "priceCurrency"],
                "recommended": ["availability", "url"],
                "constraints": {
                    "@type": lambda v: v == "Offer",
                    "price": lambda v: isinstance(v, (str, int, float)),
                    "priceCurrency": lambda v: isinstance(v, str) and len(v) == 3,
                    "availability": lambda v: isinstance(v, str) and "schema.org" in v
                }
            },
            "Brand": {
                "required": ["@id", "@type", "name"],
                "recommended": ["logo", "url"],
                "constraints": {
                    "@type": lambda v: v == "Brand",
                    "name": lambda v: isinstance(v, str) and len(v) > 0
                }
            }
        }

    def load_shapes_file(self, shapes_file: str):
        """
        Load SHACL shapes from file.

        Args:
            shapes_file: Path to shapes file
        """
        # For now, this is a placeholder
        # In production, you'd parse Turtle or JSON-LD shapes files
        # using libraries like rdflib or pyshacl
        print(f"Loading SHACL shapes from {shapes_file}")
        # TODO: Implement actual SHACL shapes parsing

    def validate(self, entity: Dict[str, Any], strict: bool = False) -> Tuple[bool, List[str], List[str]]:
        """
        Validate an entity against SHACL shapes.

        Args:
            entity: JSON-LD entity to validate
            strict: If True, recommended fields become required

        Returns:
            Tuple of (is_valid, errors, warnings)
        """
        errors = []
        warnings = []

        # Check for @context
        if "@context" not in entity:
            errors.append("Missing @context")
        elif entity["@context"] not in ["https://schema.org", "http://schema.org"]:
            errors.append(f"Invalid @context: {entity['@context']}")

        # Get entity type
        entity_type = entity.get("@type")
        if not entity_type:
            errors.append("Missing @type")
            return (False, errors, warnings)

        # Check if we have shapes for this type
        if entity_type not in self.shapes:
            warnings.append(f"No SHACL shape defined for type: {entity_type}")
            return (len(errors) == 0, errors, warnings)

        shape = self.shapes[entity_type]

        # Check required fields
        for field in shape.get("required", []):
            if field not in entity:
                errors.append(f"Missing required field: {field}")

        # Check recommended fields
        if strict:
            for field in shape.get("recommended", []):
                if field not in entity:
                    errors.append(f"Missing recommended field (strict mode): {field}")
        else:
            for field in shape.get("recommended", []):
                if field not in entity:
                    warnings.append(f"Missing recommended field: {field}")

        # Apply constraints
        constraints = shape.get("constraints", {})
        for field, constraint_func in constraints.items():
            if field in entity:
                try:
                    if not constraint_func(entity[field]):
                        errors.append(f"Constraint failed for field '{field}': {entity[field]}")
                except Exception as e:
                    errors.append(f"Error validating field '{field}': {e}")

        # Special validation for nested objects
        if entity_type == "Product":
            # Validate offers
            if "offers" in entity:
                offer_valid, offer_errors, offer_warnings = self.validate(entity["offers"], strict)
                if not offer_valid:
                    errors.extend([f"Offer: {e}" for e in offer_errors])
                warnings.extend([f"Offer: {w}" for w in offer_warnings])

            # Validate brand
            if "brand" in entity and isinstance(entity["brand"], dict):
                brand_valid, brand_errors, brand_warnings = self.validate(entity["brand"], strict)
                if not brand_valid:
                    errors.extend([f"Brand: {e}" for e in brand_errors])
                warnings.extend([f"Brand: {w}" for w in brand_warnings])

        # Check IRI format
        if "@id" in entity:
            iri = entity["@id"]
            if not iri.startswith("http"):
                errors.append(f"@id must be a valid HTTP(S) IRI: {iri}")

            # For products, check GS1 Digital Link format
            if entity_type == "Product":
                if "/01/" not in iri:
                    errors.append(f"Product @id should follow GS1 Digital Link format: {iri}")

        is_valid = len(errors) == 0
        return (is_valid, errors, warnings)

    def validate_batch(self, entities: List[Dict[str, Any]], strict: bool = False) -> Dict[str, Any]:
        """
        Validate multiple entities.

        Args:
            entities: List of JSON-LD entities
            strict: If True, recommended fields become required

        Returns:
            Dictionary with validation results
        """
        results = {
            "total": len(entities),
            "valid": 0,
            "invalid": 0,
            "entities": []
        }

        for idx, entity in enumerate(entities):
            is_valid, errors, warnings = self.validate(entity, strict)

            entity_result = {
                "index": idx,
                "id": entity.get("@id", "unknown"),
                "type": entity.get("@type", "unknown"),
                "valid": is_valid,
                "errors": errors,
                "warnings": warnings
            }

            if is_valid:
                results["valid"] += 1
            else:
                results["invalid"] += 1

            results["entities"].append(entity_result)

        return results

    def get_validation_report(self, results: Dict[str, Any]) -> str:
        """
        Generate a human-readable validation report.

        Args:
            results: Results from validate_batch()

        Returns:
            Formatted report string
        """
        lines = []
        lines.append("=" * 60)
        lines.append("SHACL VALIDATION REPORT")
        lines.append("=" * 60)
        lines.append(f"Total entities: {results['total']}")
        lines.append(f"Valid: {results['valid']}")
        lines.append(f"Invalid: {results['invalid']}")
        lines.append("")

        # Show invalid entities
        invalid_entities = [e for e in results['entities'] if not e['valid']]
        if invalid_entities:
            lines.append("INVALID ENTITIES:")
            lines.append("-" * 60)
            for entity in invalid_entities:
                lines.append(f"\n{entity['type']} - {entity['id']}")
                for error in entity['errors']:
                    lines.append(f"  ✗ {error}")

        # Show warnings
        entities_with_warnings = [e for e in results['entities'] if e['warnings']]
        if entities_with_warnings:
            lines.append("\nWARNINGS:")
            lines.append("-" * 60)
            for entity in entities_with_warnings:
                if entity['warnings']:
                    lines.append(f"\n{entity['type']} - {entity['id']}")
                    for warning in entity['warnings']:
                        lines.append(f"  ⚠ {warning}")

        lines.append("\n" + "=" * 60)

        return "\n".join(lines)


def validate_before_upload(entities: List[Dict[str, Any]], strict: bool = False) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Validate entities and split into valid/invalid lists.

    Args:
        entities: List of JSON-LD entities
        strict: If True, recommended fields become required

    Returns:
        Tuple of (valid_entities, invalid_entities_with_errors)
    """
    validator = SHACLValidator()
    results = validator.validate_batch(entities, strict)

    # Print report
    print(validator.get_validation_report(results))

    # Split entities
    valid_entities = []
    invalid_entities = []

    for entity_result in results['entities']:
        idx = entity_result['index']
        entity = entities[idx]

        if entity_result['valid']:
            valid_entities.append(entity)
        else:
            invalid_entities.append({
                'entity': entity,
                'errors': entity_result['errors']
            })

    return valid_entities, invalid_entities


# Example usage
if __name__ == '__main__':
    validator = SHACLValidator()

    # Valid product
    product = {
        "@context": "https://schema.org",
        "@type": "Product",
        "@id": "https://data.wordlift.io/wl123/01/12345678901231",
        "name": "Example Product",
        "gtin14": "12345678901231",
        "description": "A great product",
        "offers": {
            "@type": "Offer",
            "price": "29.99",
            "priceCurrency": "USD",
            "availability": "https://schema.org/InStock"
        }
    }

    is_valid, errors, warnings = validator.validate(product)
    print(f"Valid: {is_valid}")
    if errors:
        print(f"Errors: {errors}")
    if warnings:
        print(f"Warnings: {warnings}")

    # Invalid product (missing required fields)
    invalid_product = {
        "@context": "https://schema.org",
        "@type": "Product",
        "@id": "https://data.wordlift.io/wl123/product/test",
        "description": "Missing name and GTIN"
    }

    is_valid, errors, warnings = validator.validate(invalid_product)
    print(f"\nInvalid product valid: {is_valid}")
    print(f"Errors: {errors}")