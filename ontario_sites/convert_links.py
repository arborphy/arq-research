#!/usr/bin/env python3
"""
Convert absolute URLs in downloaded HTML files to relative paths.
This ensures downloaded content works offline with links pointing to local files.
"""

import os
import re
from pathlib import Path

# Base directories for the downloaded sites
BASE_DIR = Path(__file__).parent

def convert_html_links(html_file):
    """Convert absolute URLs in HTML file to relative paths."""
    
    # Domains and their local paths
    domain_map = {
        'ontariowildflowers.com': BASE_DIR / 'ontariowildflowers.com',
        'ontariotrees.com': BASE_DIR / 'ontariotrees.com',
    }
    
    with open(html_file, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    original_content = content
    
    # Convert href links
    # Pattern matches: href="http://domain/path" or href="https://domain/path"
    # Also handles links to domain root without trailing slash
    for domain, local_path in domain_map.items():
        # Convert http to https with path
        content = re.sub(
            rf'href="https?://{re.escape(domain)}/',
            rf'href="../',
            content
        )
        # Convert links to domain root (without trailing slash)
        content = re.sub(
            rf'href="https?://{re.escape(domain)}"',
            rf'href="../"',
            content
        )
        # Convert www. variant
        content = re.sub(
            rf'href="https?://www\.{re.escape(domain)}/',
            rf'href="../',
            content
        )
        content = re.sub(
            rf'href="https?://www\.{re.escape(domain)}"',
            rf'href="../"',
            content
        )
    
    # Convert src links (for images, scripts, etc.)
    for domain, local_path in domain_map.items():
        content = re.sub(
            rf'src="https?://{re.escape(domain)}/',
            r'src="../',
            content
        )
        content = re.sub(
            rf'src="https?://{re.escape(domain)}"',
            r'src="../"',
            content
        )
    
    # Write back if changed
    if content != original_content:
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False

def main():
    """Process all HTML files in the downloaded directories."""
    
    total_files = 0
    converted_files = 0
    
    for site_dir in ['ontariowildflowers.com', 'ontariotrees.com']:
        site_path = BASE_DIR / site_dir
        if not site_path.exists():
            continue
            
        for html_file in site_path.rglob('*.html'):
            total_files += 1
            if convert_html_links(html_file):
                converted_files += 1
                print(f"Converted: {html_file.relative_to(BASE_DIR)}")
    
    print(f"\nTotal HTML files: {total_files}")
    print(f"Files converted: {converted_files}")

if __name__ == '__main__':
    main()
