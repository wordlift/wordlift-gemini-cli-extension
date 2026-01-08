#!/usr/bin/env python3
"""
Markup Validator for JSON-LD
Validates JSON-LD markup before uploading to Knowledge Graph.
"""

import json
from typing import Dict, List, Any, Optional, Tuple


class MarkupValidator:
    """Validates JSON-LD markup structure and content."""

    REQUIRED_CONTEXT = ["https://schema.org", "http://schema.org"]

    def validate(self, markup: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate JSON-LD markup.

        Args:
            markup: JSON-LD markup dictionary

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []

        # Check @context
        if "@context" not in markup:
            errors.append("Missing @context")
        elif markup["@context"] not in self.REQUIRED_CONTEXT:
            errors.append(f"Invalid @context: {markup['@context']}. Must be schema.org")

        # Check @type
        if "@type" not in markup:
            errors.append("Missing @type")

        # Check @id
        if "@id" not in markup:
            errors.append("Missing @id")
        elif not markup["@id"].startswith(("http://", "https://")):
            errors.append(f"@id must be a valid URL: {markup['@id']}")

        # Validate based on type
        if "@type" in markup:
            type_errors = self._validate_by_type(markup)
            errors.extend(type_errors)

        return (len(errors) == 0, errors)

    def _validate_by_type(self, markup: Dict[str, Any]) -> List[str]:
        """Validate based on entity type."""
        entity_type = markup.get("@type")
        errors = []

        if entity_type == "Product":
            errors.extend(self._validate_product(markup))
        elif entity_type == "Organization":
            errors.extend(self._validate_organization(markup))
        elif entity_type in ["WebPage", "Article", "BlogPosting"]:
            errors.extend(self._validate_webpage(markup))

        return errors

    def _validate_product(self, markup: Dict[str, Any]) -> List[str]:
        """Validate Product entity."""
        errors = []

        # Check for name
        if "name" not in markup:
            errors.append("Product missing required field: name")

        # Check for GTIN (strongly recommended)
        has_gtin = any(k in markup for k in ["gtin", "gtin8", "gtin12", "gtin13", "gtin14"])
        if not has_gtin:
            errors.append("Product should have a GTIN field (gtin, gtin13, gtin14, etc.)")

        # Validate offers if present
        if "offers" in markup:
            offer_errors = self._validate_offer(markup["offers"])
            errors.extend(offer_errors)

        # Check brand
        if "brand" in markup:
            brand = markup["brand"]
            if isinstance(brand, dict):
                if "@type" not in brand:
                    errors.append("Product brand object missing @type")
                if "name" not in brand:
                    errors.append("Product brand object missing name")

        return errors

    def _validate_offer(self, offer: Dict[str, Any]) -> List[str]:
        """Validate Offer entity."""
        errors = []

        if not isinstance(offer, dict):
            return ["Offer must be an object"]

        if "@type" not in offer or offer["@type"] != "Offer":
            errors.append("Offer missing @type: Offer")

        if "price" not in offer:
            errors.append("Offer missing required field: price")

        if "priceCurrency" not in offer:
            errors.append("Offer missing required field: priceCurrency")

        # Validate availability if present
        if "availability" in offer:
            avail = offer["availability"]
            if isinstance(avail, str) and not avail.startswith("http"):
                errors.append(f"Offer availability should be a schema.org URL: {avail}")

        return errors

    def _validate_organization(self, markup: Dict[str, Any]) -> List[str]:
        """Validate Organization entity."""
        errors = []

        if "name" not in markup:
            errors.append("Organization missing required field: name")

        if "url" in markup and not markup["url"].startswith(("http://", "https://")):
            errors.append(f"Organization url must be a valid URL: {markup['url']}")

        return errors

    def _validate_webpage(self, markup: Dict[str, Any]) -> List[str]:
        """Validate WebPage entity."""
        errors = []

        if "url" not in markup:
            errors.append("WebPage missing required field: url")
        elif not markup["url"].startswith(("http://", "https://")):
            errors.append(f"WebPage url must be a valid URL: {markup['url']}")

        if "name" not in markup and "headline" not in markup:
            errors.append("WebPage should have either name or headline")

        return errors

    def validate_batch(self, markups: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Validate multiple markups.

        Args:
            markups: List of JSON-LD markup dictionaries

        Returns:
            Dictionary with validation results
        """
        results = {
            "total": len(markups),
            "valid": 0,
            "invalid": 0,
            "errors": []
        }

        for idx, markup in enumerate(markups):
            is_valid, errors = self.validate(markup)

            if is_valid:
                results["valid"] += 1
            else:
                results["invalid"] += 1
                results["errors"].append({
                    "index": idx,
                    "id": markup.get("@id", "unknown"),
                    "type": markup.get("@type", "unknown"),
                    "errors": errors
                })

        return results


def validate_json_ld_string(json_string: str) -> Tuple[bool, List[str], Optional[Dict]]:
    """
    Validate JSON-LD markup from a string.

    Args:
        json_string: JSON-LD as a string

    Returns:
        Tuple of (is_valid, errors, parsed_markup)

    Example:
        >>> json_str = '{"@context": "https://schema.org", ...}'
        >>> is_valid, errors, markup = validate_json_ld_string(json_str)
    """
    try:
        # Try to parse as JSON
        markup = json.loads(json_string)
    except json.JSONDecodeError as e:
        return (False, [f"Invalid JSON: {e}"], None)

    # Validate the markup
    validator = MarkupValidator()
    is_valid, errors = validator.validate(markup)

    return (is_valid, errors, markup if is_valid else None)


# Backward compatibility alias
validate_markup_from_agent = validate_json_ld_string


if __name__ == '__main__':
    # Example usage
    validator = MarkupValidator()

    # Valid product markup
    product_markup = {
        "@context": "https://schema.org",
        "@type": "Product",
        "@id": "https://example.com/01/12345678901231",
        "name": "Example Product",
        "gtin14": "12345678901231",
        "offers": {
            "@type": "Offer",
            "price": "29.99",
            "priceCurrency": "USD",
            "availability": "https://schema.org/InStock"
        }
    }

    is_valid, errors = validator.validate(product_markup)
    print(f"Product valid: {is_valid}")
    if errors:
        print(f"Errors: {errors}")

    # Invalid product (missing required fields)
    invalid_product = {
        "@context": "https://schema.org",
        "@type": "Product",
        # Missing @id and name
        "description": "A product"
    }

    is_valid, errors = validator.validate(invalid_product)
    print(f"\nInvalid product valid: {is_valid}")
    print(f"Errors: {errors}")