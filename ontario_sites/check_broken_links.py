#!/usr/bin/env python3
"""
Phase 1 Validation Step 3: Identify Broken Internal Links
Finds links to pages that should exist but weren't downloaded.
"""

import os
import re
from pathlib import Path
from urllib.parse import urlparse, unquote
from html.parser import HTMLParser
from collections import defaultdict


class LinkExtractor(HTMLParser):
    """Extract href attributes from HTML."""
    
    def __init__(self):
        super().__init__()
        self.href_links = []
        
    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        if 'href' in attrs_dict:
            self.href_links.append(attrs_dict['href'])


def is_internal_link(link, base_domain):
    """Check if link is internal (same domain)."""
    link = link.strip()
    
    # Skip empty, javascript, and fragment-only links
    if not link or link.startswith('javascript:') or link.startswith('#'):
        return False
    
    # Relative links are internal
    if not link.startswith('http://') and not link.startswith('https://'):
        return True
    
    # Absolute links - check if same domain
    parsed = urlparse(link)
    if parsed.netloc == base_domain or parsed.netloc == 'www.' + base_domain:
        return True
    
    return False


def extract_file_path(link, base_domain):
    """
    Extract local file path from a link.
    Converts URLs to expected local file paths.
    """
    link = link.strip()
    
    # Handle relative links
    if not link.startswith('http://') and not link.startswith('https://'):
        # Remove fragment
        link = link.split('#')[0]
        return link
    
    # Handle absolute links to same domain
    parsed = urlparse(link)
    path = parsed.path
    query = parsed.query
    
    # Build the base filename
    base_name = path.split('/')[-1]
    
    # If there's a query, append it
    if query:
        params = {}
        for pair in query.split('&'):
            if '=' in pair:
                k, v = pair.split('=', 1)
                params[k] = v
        
        if 'id' in params:
            return f"{base_name}?id={params['id']}"
        elif 'type' in params:
            return f"{base_name}?type={params['type']}"
        else:
            return base_name
    
    return base_name


def check_broken_links(site_path, site_name, sample_size=50):
    """
    Check for broken internal links in HTML files.
    
    Returns:
        Dictionary with broken link analysis
    """
    html_files = list(Path(site_path).rglob('*.html'))
    
    # Sample files if requested
    if sample_size > 0 and len(html_files) > sample_size:
        import random
        html_files = random.sample(html_files, sample_size)
    
    print(f"\n{'='*60}")
    print(f"Checking broken links in {site_name}")
    print(f"{'='*60}")
    print(f"Analyzing {len(html_files)} HTML files")
    
    # Track all internal links and their sources
    internal_links = defaultdict(list)  # link -> [source_files]
    missing_files = defaultdict(int)    # missing_file -> count
    
    for html_file in html_files:
        try:
            with open(html_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            parser = LinkExtractor()
            parser.feed(content)
            
            for link in parser.href_links:
                if is_internal_link(link, site_name):
                    rel_path = extract_file_path(link, site_name)
                    internal_links[rel_path].append(str(html_file.relative_to(site_path)))
                    
        except Exception as e:
            print(f"Error processing {html_file}: {e}")
    
    # Check which files are missing
    print(f"\nTotal internal links found: {len(internal_links)}")
    
    for link_path, sources in internal_links.items():
        # Normalize the path - remove any leading slashes
        normalized = link_path.lstrip('/').lstrip('./')
        
        if not normalized:
            continue
            
        # Check if file exists
        possible_files = []
        
        # For links with query parameters (e.g., species.php?id=123)
        if '?' in normalized:
            possible_files.append(site_path / 'main' / f"{normalized}.html")
        else:
            # For links without query parameters
            possible_files.append(site_path / normalized)
            possible_files.append(site_path / f"{normalized}.html")
            possible_files.append(site_path / 'main' / normalized)
            possible_files.append(site_path / 'main' / f"{normalized}.html")
            possible_files.append(site_path / 'id' / normalized)
            possible_files.append(site_path / 'id' / f"{normalized}.html")
        
        exists = any(p.exists() for p in possible_files)
        
        if not exists:
            missing_files[normalized] += len(sources)
    
    # Categorize missing files
    categories = {
        'species': [],
        'family': [],
        'genus': [],
        'group': [],
        'habitat': [],
        'colour': [],
        'season': [],
        'petals': [],
        'tour': [],
        'other': []
    }
    
    for missing, count in sorted(missing_files.items(), key=lambda x: -x[1]):
        if 'species.php' in missing:
            categories['species'].append((missing, count))
        elif 'family.php' in missing:
            categories['family'].append((missing, count))
        elif 'genus.php' in missing:
            categories['genus'].append((missing, count))
        elif 'group.php' in missing:
            categories['group'].append((missing, count))
        elif 'habitat.php' in missing:
            categories['habitat'].append((missing, count))
        elif 'colour' in missing or 'colour_thumbs' in missing:
            categories['colour'].append((missing, count))
        elif 'season.php' in missing:
            categories['season'].append((missing, count))
        elif 'petals.php' in missing:
            categories['petals'].append((missing, count))
        elif 'species_tour' in missing:
            categories['tour'].append((missing, count))
        else:
            categories['other'].append((missing, count))
    
    return {
        'site_name': site_name,
        'files_analyzed': len(html_files),
        'total_internal_links': len(internal_links),
        'missing_files': missing_files,
        'categories': categories,
        'total_missing': sum(missing_files.values())
    }


def generate_broken_links_report(results):
    """Generate report of broken links analysis."""
    report = []
    report.append("\n" + "="*70)
    report.append("PHASE 1 VALIDATION - STEP 3: BROKEN INTERNAL LINKS")
    report.append("="*70)
    
    total_missing = 0
    total_links = 0
    
    for result in results:
        site = result['site_name']
        report.append(f"\n{site}:")
        report.append(f"  Files analyzed: {result['files_analyzed']}")
        report.append(f"  Total internal links: {result['total_internal_links']}")
        report.append(f"  Missing files referenced: {result['total_missing']}")
        
        total_missing += result['total_missing']
        total_links += result['total_internal_links']
        
        categories = result['categories']
        
        # Report by category
        for cat_name, items in categories.items():
            if items:
                report.append(f"\n  {cat_name.upper()} pages missing ({len(items)} unique):")
                for missing, count in items[:10]:  # Show top 10
                    report.append(f"    - {missing} (referenced {count} times)")
                if len(items) > 10:
                    report.append(f"    ... and {len(items) - 10} more")
    
    report.append("\n" + "-"*70)
    report.append("SUMMARY:")
    report.append(f"  Total internal links checked: {total_links}")
    report.append(f"  Total missing file references: {total_missing}")
    
    if total_links > 0:
        integrity = ((total_links - total_missing) / total_links) * 100
        report.append(f"  Link integrity score: {integrity:.1f}%")
    
    # Assessment
    report.append("\n" + "="*70)
    report.append("ASSESSMENT:")
    report.append("="*70)
    
    if total_missing == 0:
        report.append("✓ EXCELLENT: No broken internal links found")
    elif total_missing < total_links * 0.05:
        report.append(f"✓ GOOD: Less than 5% broken links ({total_missing}/{total_links})")
    elif total_missing < total_links * 0.10:
        report.append(f"⚠️  ACCEPTABLE: 5-10% broken links ({total_missing}/{total_links})")
    else:
        report.append(f"⚠️  WARNING: More than 10% broken links ({total_missing}/{total_links})")
    
    if total_missing > 0:
        report.append("\nRecommendations:")
        report.append("- Missing pages may be: out of scope, never existed, or deleted")
        report.append("- Run targeted wget for specific missing page types if needed")
        report.append("- Cross-reference with site index for expected pages")
    
    return "\n".join(report)


def main():
    """Main function to check broken links for both sites."""
    script_dir = Path(__file__).parent
    
    print("Phase 1 Validation - Step 3: Identify Broken Internal Links")
    print("="*60)
    
    sites = [
        ('ontariotrees.com', 'ontariotrees.com'),
        ('ontariowildflowers.com', 'ontariowildflowers.com'),
    ]
    
    results = []
    for site_name, site_dir in sites:
        site_path = script_dir / site_dir
        if site_path.exists():
            result = check_broken_links(site_path, site_name, sample_size=100)
            results.append(result)
        else:
            print(f"Warning: {site_path} not found")
    
    # Generate and print report
    report = generate_broken_links_report(results)
    print(report)
    
    # Save report
    report_file = script_dir / 'broken_links_analysis.txt'
    with open(report_file, 'w') as f:
        f.write(report)
    print(f"\nReport saved to: {report_file}")
    
    return results


if __name__ == '__main__':
    main()
