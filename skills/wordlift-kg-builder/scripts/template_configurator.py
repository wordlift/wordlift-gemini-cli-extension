#!/usr/bin/env python3
"""
Template Configuration for Bulk Imports
Interactive workflow to establish markup templates before bulk imports.
"""

import json
from typing import Dict, List, Any, Optional
from wordlift_client import WordLiftClient
from shacl_validator import SHACLValidator
from markup_validator import MarkupValidator


class TemplateConfigurator:
    """Configure markup templates by analyzing sample pages."""

    def __init__(self, client: WordLiftClient, dataset_uri: str):
        """
        Initialize template configurator.

        Args:
            client: WordLift API client
            dataset_uri: Base dataset URI
        """
        self.client = client
        self.dataset_uri = dataset_uri
        self.validator = SHACLValidator()
        self.markup_validator = MarkupValidator()

    def analyze_sample_pages(self, sample_urls: List[str]) -> List[Dict[str, Any]]:
        """
        Analyze sample pages to extract markup patterns.

        Args:
            sample_urls: List of sample URLs to analyze

        Returns:
            List of analysis results with proposed markup
        """
        print(f"\n{'='*60}")
        print(f"ANALYZING {len(sample_urls)} SAMPLE PAGES")
        print(f"{'='*60}\n")

        results = []

        for idx, url in enumerate(sample_urls, 1):
            print(f"[{idx}/{len(sample_urls)}] Analyzing: {url}")
            print("-" * 60)

            analysis = {
                'url': url,
                'proposed_markup': None,
                'detected_type': None,
                'validation_result': None,
                'recommendations': []
            }

            # Note: In production, this would call WordLift Agent API
            # For now, we'll create a template based on URL patterns
            analysis['detected_type'] = self._detect_content_type(url)
            analysis['proposed_markup'] = self._generate_template(url, analysis['detected_type'])

            # Validate the markup
            is_valid, errors, warnings = self.validator.validate(
                analysis['proposed_markup'],
                strict=False
            )

            analysis['validation_result'] = {
                'valid': is_valid,
                'errors': errors,
                'warnings': warnings
            }

            # Generate recommendations
            analysis['recommendations'] = self._generate_recommendations(
                analysis['proposed_markup'],
                warnings
            )

            results.append(analysis)

            # Print summary
            print(f"  Detected Type: {analysis['detected_type']}")
            print(f"  Validation: {'✓ VALID' if is_valid else '✗ INVALID'}")
            if errors:
                for error in errors:
                    print(f"    ✗ {error}")
            if warnings:
                for warning in warnings[:3]:  # Show first 3 warnings
                    print(f"    ⚠ {warning}")
            print()

        return results

    def _detect_content_type(self, url: str) -> str:
        """
        Detect content type from URL patterns.

        Args:
            url: Page URL

        Returns:
            Detected schema.org type
        """
        url_lower = url.lower()

        if '/blog/' in url_lower or '/post/' in url_lower:
            return 'BlogPosting'
        elif '/news/' in url_lower or '/article/' in url_lower:
            return 'Article'
        elif '/product/' in url_lower:
            return 'Product'
        elif '/event/' in url_lower:
            return 'Event'
        else:
            return 'WebPage'

    def _generate_template(self, url: str, content_type: str) -> Dict[str, Any]:
        """
        Generate markup template for a page.

        Args:
            url: Page URL
            content_type: Schema.org type

        Returns:
            JSON-LD template
        """
        from id_generator import generate_entity_id, generate_slug
        from urllib.parse import urlparse

        # Extract slug from URL
        parsed = urlparse(url)
        path_parts = [p for p in parsed.path.split('/') if p]
        slug = path_parts[-1] if path_parts else 'homepage'

        # Generate ID
        page_id = generate_entity_id(self.dataset_uri, "webpage", slug)

        # Base template
        template = {
            "@context": "https://schema.org",
            "@type": content_type,
            "@id": page_id,
            "url": url,
            "name": "[Page Title - to be extracted]",
            "description": "[Page Description - to be extracted]"
        }

        # Add type-specific properties
        if content_type in ['Article', 'BlogPosting']:
            template['headline'] = "[Article Headline - to be extracted]"
            template['datePublished'] = "[Date - to be extracted]"
            template['author'] = {
                "@type": "Person",
                "@id": f"{self.dataset_uri}/person/[author-slug]",
                "name": "[Author Name - to be extracted]"
            }
            template['publisher'] = {
                "@type": "Organization",
                "@id": f"{self.dataset_uri}/organization/[publisher-slug]",
                "name": "[Publisher Name - to be configured]"
            }

        return template

    def _generate_recommendations(self, markup: Dict[str, Any], warnings: List[str]) -> List[str]:
        """
        Generate recommendations for improving markup.

        Args:
            markup: Proposed markup
            warnings: Validation warnings

        Returns:
            List of recommendations
        """
        recommendations = []

        # Check for missing recommended fields
        if 'description' not in markup:
            recommendations.append("Add 'description' property for better SEO")

        if 'image' not in markup:
            recommendations.append("Add 'image' property for social sharing")

        if markup.get('@type') in ['Article', 'BlogPosting']:
            if 'author' not in markup:
                recommendations.append("Consider adding 'author' for content attribution")
            if 'datePublished' not in markup:
                recommendations.append("Add 'datePublished' for temporal context")

        return recommendations

    def display_configuration_summary(self, analyses: List[Dict[str, Any]]):
        """
        Display summary of analyzed pages for user review.

        Args:
            analyses: List of page analysis results
        """
        print(f"\n{'='*60}")
        print("CONFIGURATION SUMMARY")
        print(f"{'='*60}\n")

        # Detect common patterns
        types = [a['detected_type'] for a in analyses]
        most_common_type = max(set(types), key=types.count)

        print(f"Analyzed {len(analyses)} sample pages")
        print(f"Most common type: {most_common_type}")
        print()

        # Show unique types detected
        unique_types = set(types)
        print("Detected content types:")
        for content_type in unique_types:
            count = types.count(content_type)
            print(f"  • {content_type}: {count} page(s)")
        print()

        # Validation summary
        valid_count = sum(1 for a in analyses if a['validation_result']['valid'])
        print(f"Validation: {valid_count}/{len(analyses)} samples valid")
        print()

        # Common recommendations
        all_recommendations = []
        for analysis in analyses:
            all_recommendations.extend(analysis['recommendations'])

        if all_recommendations:
            unique_recommendations = list(set(all_recommendations))
            print("Recommendations:")
            for rec in unique_recommendations:
                print(f"  • {rec}")
            print()

    def generate_configuration_questions(self, analyses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate configuration questions based on analysis.

        Args:
            analyses: List of page analysis results

        Returns:
            Dictionary of configuration questions
        """
        types = [a['detected_type'] for a in analyses]
        most_common_type = max(set(types), key=types.count)

        questions = {
            'entity_type': {
                'question': 'What schema.org type should these pages use?',
                'detected': most_common_type,
                'options': ['WebPage', 'Article', 'BlogPosting', 'NewsArticle'],
                'recommendation': most_common_type
            },
            'has_author': {
                'question': 'Do your pages have authors?',
                'detected': 'author' in analyses[0]['proposed_markup'],
                'options': ['Yes - Extract and reuse', 'No - Skip', 'Yes - Use organization'],
                'recommendation': 'Yes - Extract and reuse' if most_common_type in ['Article', 'BlogPosting'] else 'No - Skip'
            },
            'publisher': {
                'question': 'Publisher/Organization information:',
                'fields': ['name', 'url', 'logo'],
                'recommendation': 'Configure for all pages'
            },
            'metadata': {
                'question': 'Which metadata properties should be extracted?',
                'options': [
                    'headline/name',
                    'description',
                    'datePublished',
                    'dateModified',
                    'image',
                    'keywords',
                    'breadcrumb'
                ],
                'defaults': ['headline/name', 'description', 'image']
            },
            'id_pattern': {
                'question': 'How should WebPage IDs be generated?',
                'options': [
                    'URL slug only (/webpage/about-us)',
                    'Full path (/webpage/company/about-us)',
                    'Custom pattern'
                ],
                'recommendation': 'URL slug only'
            }
        }

        return questions

    def save_template(self, template_config: Dict[str, Any], output_file: str):
        """
        Save approved template configuration.

        Args:
            template_config: Template configuration
            output_file: Output file path
        """
        with open(output_file, 'w') as f:
            json.dump(template_config, f, indent=2)

        print(f"\n✓ Template configuration saved to: {output_file}")

    def load_template(self, template_file: str) -> Dict[str, Any]:
        """
        Load saved template configuration.

        Args:
            template_file: Template file path

        Returns:
            Template configuration
        """
        with open(template_file, 'r') as f:
            return json.load(f)


def interactive_template_configuration(
    client: WordLiftClient,
    dataset_uri: str,
    sample_urls: List[str]
) -> Dict[str, Any]:
    """
    Run interactive template configuration workflow.

    Args:
        client: WordLift API client
        dataset_uri: Base dataset URI
        sample_urls: Sample URLs to analyze

    Returns:
        Approved template configuration
    """
    configurator = TemplateConfigurator(client, dataset_uri)

    # Step 1: Analyze samples
    print("\n🔍 STEP 1: ANALYZING SAMPLE PAGES")
    analyses = configurator.analyze_sample_pages(sample_urls)

    # Step 2: Display summary
    print("\n📊 STEP 2: CONFIGURATION SUMMARY")
    configurator.display_configuration_summary(analyses)

    # Step 3: Generate questions
    print("\n❓ STEP 3: CONFIGURATION QUESTIONS")
    questions = configurator.generate_configuration_questions(analyses)

    print("\nBased on the analysis, here are the recommended settings:")
    print(json.dumps(questions, indent=2))

    # Step 4: Build template config
    template_config = {
        'dataset_uri': dataset_uri,
        'entity_type': questions['entity_type']['recommendation'],
        'extract_author': questions['has_author']['recommendation'] == 'Yes - Extract and reuse',
        'metadata_fields': questions['metadata']['defaults'],
        'id_pattern': questions['id_pattern']['recommendation'],
        'sample_analyses': analyses,
        'timestamp': str(datetime.now())
    }

    # Step 5: Show final template
    print("\n✅ STEP 4: FINAL TEMPLATE")
    print(json.dumps(template_config, indent=2))

    return template_config


# Example usage
if __name__ == '__main__':
    import os
    from datetime import datetime

    api_key = os.environ.get('WORDLIFT_API_KEY')
    dataset_uri = "https://data.wordlift.io/wl123"

    sample_urls = [
        "https://example.com/blog/post-1",
        "https://example.com/blog/post-2",
        "https://example.com/about"
    ]

    client = WordLiftClient(api_key)

    # Run interactive configuration
    template_config = interactive_template_configuration(
        client,
        dataset_uri,
        sample_urls
    )

    # Save template
    configurator = TemplateConfigurator(client, dataset_uri)
    configurator.save_template(template_config, 'template_config.json')

    print("\n" + "="*60)
    print("Template configuration complete!")
    print("Review the configuration above and approve to proceed with bulk import.")
    print("="*60)