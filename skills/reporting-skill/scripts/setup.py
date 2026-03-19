#!/usr/bin/env python3
"""
Install all dependencies required by the SEO Performance Report skill.
Run this before any other scripts.
"""

import subprocess
import sys


PACKAGES = [
    "google-api-python-client",
    "google-auth-oauthlib",
    "google-analytics-data",
    "searchconsole",
    "pandas",
    "matplotlib",
    "seaborn",
    "numpy",
    "pycausalimpact",
    "openpyxl",
    "tqdm",
    "pyyaml",
    "fpdf2",
]


def main():
    print("📦 Installing SEO Performance Report dependencies...")
    for pkg in PACKAGES:
        print(f"   ▸ {pkg}")
    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "--quiet"] + PACKAGES
        )
        print("\n✅ All dependencies installed successfully!")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Installation failed: {e}")
        print("   Try running: pip install " + " ".join(PACKAGES))
        sys.exit(1)


if __name__ == "__main__":
    main()
