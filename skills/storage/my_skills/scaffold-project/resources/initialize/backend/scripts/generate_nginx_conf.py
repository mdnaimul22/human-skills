#!/usr/bin/env python3
"""
Generate Nginx configuration file dynamically from settings.py config.
"""
import os
import sys

# Add src directory to path to load settings/helpers
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(PROJECT_ROOT)

try:
    from src.helpers import generate_nginx_config
except ImportError:
    print("Error: Could not import helper from src.helpers. Run this from project root.")
    sys.exit(1)

def main():
    if generate_nginx_config():
        output_path = os.path.join(PROJECT_ROOT, "deploy", "nginx", "nginx.conf")
        print(f"✅ Generated Nginx configuration successfully at {output_path}!")
    else:
        print("❌ Failed to generate Nginx configuration (template not found or error occurred).")
        sys.exit(1)

if __name__ == "__main__":
    main()
