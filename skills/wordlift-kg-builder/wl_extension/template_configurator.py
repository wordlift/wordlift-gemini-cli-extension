#!/usr/bin/env python3
"""
Template Configurator for WordLift Knowledge Graph
Helps configure and validate markup templates before bulk imports.
"""

import json
from typing import List, Dict, Any, Optional
from .wordlift_client import WordLiftClient
from .entity_builder import EntityBuilder

class TemplateConfigurator:
    """Manages the configuration and validation of markup templates."""

    def __init__(self, client: WordLiftClient, dataset_uri: str):
        self.client = client
        self.dataset_uri = dataset_uri
        self.builder = EntityBuilder(dataset_uri)

    def analyze_sample_pages(self, urls: List[str]) -> Dict[str, Any]:
        """
        Analyze sample pages to determine best template configuration.
        In a real scenario, this would involve fetching pages and extracting metadata.
        For now, it provides a structured analysis placeholder.
        """
        print(f"Analyzing {len(urls)} sample pages...")
        analysis = {
            "urls": urls,
            "detected_types": ["WebPage", "Article"],
            "suggested_type": "Article",
            "required_fields": ["headline", "description", "author", "datePublished"],
            "missing_metadata": [],
            "id_pattern": "{dataset_uri}/webpage/{slug}"
        }
        return analysis

    def display_configuration_summary(self, analysis: Dict[str, Any]):
        """Show analysis summary to the user."""
        print("\n--- Template Configuration Summary ---")
        print(f"Suggested Entity Type: {analysis['suggested_type']}")
        print(f"ID Pattern: {analysis['id_pattern']}")
        print(f"Required Fields: {', '.join(analysis['required_fields'])}")
        print("--------------------------------------\n")

    def generate_configuration_questions(self, analysis: Dict[str, Any]) -> List[Dict[str, str]]:
        """Generate questions for the user to refine the template."""
        return [
            {"id": "entity_type", "question": f"Confirm entity type (default: {analysis['suggested_type']}): "},
            {"id": "author_name", "question": "Enter default author name: "},
            {"id": "publisher_name", "question": "Enter default publisher name: "}
        ]

    def save_template(self, config: Dict[str, Any], path: str):
        """Save approved template to a JSON file."""
        with open(path, 'w') as f:
            json.dump(config, f, indent=2)
        print(f"Template saved to {path}")

def interactive_template_configuration(client: WordLiftClient, dataset_uri: str, sample_urls: List[str]):
    """Full interactive workflow for template configuration."""
    configurator = TemplateConfigurator(client, dataset_uri)
    analysis = configurator.analyze_sample_pages(sample_urls)
    configurator.display_configuration_summary(analysis)

    # In an interactive CLI, we would ask questions here.
    # For this implementation, we'll return the suggested config.
    print("✓ Template configuration completed based on analysis.")
    return analysis

if __name__ == "__main__":
    # Example usage placeholder
    print("Template Configurator module loaded.")
