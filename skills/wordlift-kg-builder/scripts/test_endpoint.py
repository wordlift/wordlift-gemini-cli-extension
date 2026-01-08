#!/usr/bin/env python3
"""
Test script to verify Sitemap Import API endpoint.
"""

import os
import sys
from scripts.wordlift_client import WordLiftClient


def test_sitemap_endpoint():
    """Test the sitemap import endpoint."""

    api_key = os.environ.get('WORDLIFT_API_KEY')
    if not api_key:
        print("Error: WORDLIFT_API_KEY environment variable not set")
        sys.exit(1)

    print("Testing Sitemap Import API Endpoint")
    print("="*60)

    client = WordLiftClient(api_key)

    print(f"\nBase URL: {client.base_url}")
    print(f"Endpoint: {client.base_url}/sitemap-imports")
    print(f"Expected: https://api.wordlift.io/sitemap-imports")

    # Test with a small URL list (not a full sitemap)
    test_urls = ["https://example.com/test-page"]

    print(f"\nAttempting to import test URL...")
    print(f"URL: {test_urls[0]}")

    try:
        results = client.import_from_urls(test_urls)
        print(f"\n✓ Success! Endpoint is working correctly.")
        print(f"  Imported {len(results)} page(s)")

        if results:
            print(f"\n  Response sample:")
            print(f"  {results[0]}")

        return True

    except Exception as e:
        print(f"\n✗ Error: {e}")
        print(f"\nIf you see a 404 error, verify:")
        print(f"  1. Endpoint is: https://api.wordlift.io/sitemap-imports")
        print(f"  2. API key is valid")
        print(f"  3. You have permission to use the Sitemap Import API")

        return False


if __name__ == '__main__':
    success = test_sitemap_endpoint()
    sys.exit(0 if success else 1)