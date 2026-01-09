#!/usr/bin/env python3
"""
Phase 1 Validation Step 2: Check Link Types
Analyzes HTML files to classify links as relative, absolute (same domain), or absolute (external).
"""

import os
import re
from pathlib import Path
from collections import Counter
from html.parser import HTMLParser
from urllib.parse import urlparse


class LinkExtractor(HTMLParser):
    """Extract href and src attributes from HTML."""
    
    def __init__(self):
        super().__init__()
        self.href_links = []
        self.src_links = []
        
    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        if 'href' in attrs_dict:
            self.href_links.append(attrs_dict['href'])
        if 'src' in attrs_dict:
            self.src_links.append(attrs_dict['src'])


def classify_link(link, base_domain=None):
    """
    Classify a link as relative, same-domain absolute, or external absolute.
    
    Returns:
        'relative': Link is relative path (starts with ../, ./, or just filename)
        'same_domain': Absolute URL pointing to the same domain
        'external': Absolute URL pointing to different domain
    """
    link = link.strip()
    
    # Skip empty links, javascript links, and fragment-only links
    if not link or link.startswith('javascript:') or link.startswith('#'):
        return 'fragment/javascript'
    
    # Check for relative links
    if not link.startswith('http://') and not link.startswith('https://'):
        return 'relative'
    
    # Parse the URL
    parsed = urlparse(link)
    
    # Check if it's the same domain
    if base_domain and (parsed.netloc == base_domain or parsed.netloc == 'www.' + base_domain):
        return 'same_domain'
    
    return 'external'


def analyze_site_links(site_path, site_name, sample_size=20):
    """
    Analyze link types in HTML files for a single site.
    
    Args:
        site_path: Path to the site directory
        site_name: Name of the site (e.g., 'ontariotrees.com')
        sample_size: Number of files to sample (0 for all)
    
    Returns:
        Dictionary with link analysis results
    """
    html_files = list(Path(site_path).rglob('*.html'))
    
    # Sample files if requested
    if sample_size > 0 and len(html_files) > sample_size:
        import random
        html_files = random.sample(html_files, sample_size)
    
    print(f"\n{'='*60}")
    print(f"Analyzing {len(html_files)} HTML files from {site_name}")
    print(f"{'='*60}")
    
    # Counters for link classification
    link_types = Counter()
    all_links = []
    
    for html_file in html_files:
        try:
            with open(html_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            parser = LinkExtractor()
            parser.feed(content)
            
            # Process all extracted links
            for link in parser.href_links + parser.src_links:
                link_type = classify_link(link, site_name)
                link_types[link_type] += 1
                all_links.append((str(html_file.relative_to(site_path)), link_type, link))
                
        except Exception as e:
            print(f"Error processing {html_file}: {e}")
    
    return {
        'site_name': site_name,
        'files_analyzed': len(html_files),
        'total_links': sum(link_types.values()),
        'link_types': link_types,
        'sample_links': all_links[:50]  # First 50 links for review
    }


def calculate_percentages(counter):
    """Calculate percentages for each link type."""
    total = sum(counter.values())
    if total == 0:
        return {}
    return {k: (v / total * 100, v) for k, v in counter.items()}


def generate_report(results):
    """Generate a detailed report of link analysis."""
    report = []
    report.append("\n" + "="*70)
    report.append("PHASE 1 VALIDATION - STEP 2: LINK TYPE ANALYSIS")
    report.append("="*70)
    
    total_relative = 0
    total_same_domain = 0
    total_external = 0
    total_other = 0
    
    for result in results:
        site = result['site_name']
        counter = result['link_types']
        percentages = calculate_percentages(counter)
        
        report.append(f"\n{site}:")
        report.append(f"  Files analyzed: {result['files_analyzed']}")
        report.append(f"  Total links found: {result['total_links']}")
        report.append(f"  Link type breakdown:")
        
        for link_type in ['relative', 'same_domain', 'external', 'fragment/javascript']:
            if link_type in counter:
                pct, count = percentages[link_type]
                report.append(f"    - {link_type}: {count} ({pct:.1f}%)")
                
                if link_type == 'relative':
                    total_relative += count
                elif link_type == 'same_domain':
                    total_same_domain += count
                elif link_type == 'external':
                    total_external += count
                else:
                    total_other += count
    
    # Summary across all sites
    grand_total = total_relative + total_same_domain + total_external + total_other
    report.append("\n" + "-"*70)
    report.append("SUMMARY ACROSS ALL SITES:")
    report.append(f"  Total links analyzed: {grand_total}")
    report.append(f"  Relative links: {total_relative} ({total_relative/grand_total*100:.1f}%)")
    report.append(f"  Same-domain absolute: {total_same_domain} ({total_same_domain/grand_total*100:.1f}%)")
    report.append(f"  External absolute: {total_external} ({total_external/grand_total*100:.1f}%)")
    report.append(f"  Fragment/JavaScript: {total_other} ({total_other/grand_total*100:.1f}%)")
    
    # Assessment
    report.append("\n" + "="*70)
    report.append("ASSESSMENT:")
    report.append("="*70)
    
    if total_same_domain > 0:
        report.append(f"⚠️  WARNING: Found {total_same_domain} absolute links to same domain.")
        report.append("   These should be converted to relative paths for portability.")
        report.append("   Run convert_links.py to fix these links.")
    else:
        report.append("✓ GOOD: No same-domain absolute links found.")
    
    if total_relative / grand_total > 0.9:
        report.append("✓ EXCELLENT: 90%+ of links are relative (portable)")
    elif total_relative / grand_total > 0.7:
        report.append("✓ ACCEPTABLE: 70-90% of links are relative")
    else:
        report.append("⚠️  WARNING: Less than 70% of links are relative")
    
    if total_external > 0:
        report.append(f"ℹ️  Note: {total_external} external links found (these are expected)")
    
    return "\n".join(report)


def main():
    """Main function to analyze link types for both sites."""
    print("Phase 1 Validation - Step 2: Check Link Types")
    print("="*60)
    
    # Use the directory where the script is located
    base_dir = Path(__file__).parent
    
    sites = [
        ('ontariotrees.com', 'ontariotrees.com'),
        ('ontariowildflowers.com', 'ontariowildflowers.com'),
    ]
    
    results = []
    for site_name, site_dir in sites:
        site_path = base_dir / site_dir
        if site_path.exists():
            result = analyze_site_links(site_path, site_name, sample_size=30)
            results.append(result)
        else:
            print(f"Warning: {site_path} not found")
    
    # Generate and print report
    report = generate_report(results)
    print(report)
    
    # Save report to file
    report_file = base_dir / 'link_type_analysis.txt'
    with open(report_file, 'w') as f:
        f.write(report)
    print(f"\nReport saved to: {report_file}")
    
    return results


if __name__ == '__main__':
    main()
