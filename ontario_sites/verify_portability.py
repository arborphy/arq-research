#!/usr/bin/env python3
"""
Phase 1 Validation Step 4: Verify Link Portability
Ensures directory can be moved without breaking links.
"""

import os
import re
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlparse


class LinkExtractor(HTMLParser):
    """Extract href and src attributes from HTML."""
    
    def __init__(self):
        super().__init__()
        self.links = []
        
    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        if 'href' in attrs_dict:
            self.links.append(('href', attrs_dict['href']))
        if 'src' in attrs_dict:
            self.links.append(('src', attrs_dict['src']))


def check_portability(site_path, site_name):
    """
    Check for portability issues in HTML files.
    
    Returns:
        Dictionary with portability analysis
    """
    html_files = list(Path(site_path).rglob('*.html'))
    
    print(f"\n{'='*60}")
    print(f"Checking portability in {site_name}")
    print(f"{'='*60}")
    print(f"Analyzing {len(html_files)} HTML files")
    
    issues = {
        'absolute_file_paths': [],
        'hardcoded_home_dir': [],
        'absolute_http_urls': [],
        'relative_links': [],
        'fragment_only': [],
    }
    
    for html_file in html_files:
        try:
            with open(html_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            parser = LinkExtractor()
            parser.feed(content)
            
            for attr_type, link in parser.links:
                link = link.strip()
                
                if not link:
                    continue
                
                # Skip fragment-only links
                if link.startswith('#'):
                    issues['fragment_only'].append((str(html_file.relative_to(site_path)), attr_type, link))
                    continue
                
                # Check for absolute file paths
                if link.startswith('/') and not link.startswith('//'):
                    # Unix absolute path
                    if link.startswith('/Users/') or link.startswith('/home/') or link.startswith('/Users/'):
                        issues['absolute_file_paths'].append((str(html_file.relative_to(site_path)), attr_type, link))
                        continue
                
                # Check for hardcoded home directory
                if '/Users/margaretholen/' in link or '/home/margaretholen/' in link:
                    issues['hardcoded_home_dir'].append((str(html_file.relative_to(site_path)), attr_type, link))
                    continue
                
                # Check for absolute http/https URLs (same domain)
                if link.startswith('http://') or link.startswith('https://'):
                    parsed = urlparse(link)
                    if parsed.netloc == site_name or parsed.netloc == 'www.' + site_name:
                        issues['absolute_http_urls'].append((str(html_file.relative_to(site_path)), attr_type, link))
                    else:
                        # External links are OK for portability
                        pass
                    continue
                
                # Relative links are good
                if not link.startswith('file://'):
                    issues['relative_links'].append((str(html_file.relative_to(site_path)), attr_type, link))
                
        except Exception as e:
            print(f"Error processing {html_file}: {e}")
    
    return {
        'site_name': site_name,
        'files_analyzed': len(html_files),
        'issues': issues,
        'total_links': sum(len(v) for v in issues.values()),
    }


def generate_portability_report(results):
    """Generate portability assessment report."""
    report = []
    report.append("\n" + "="*70)
    report.append("PHASE 1 VALIDATION - STEP 4: LINK PORTABILITY")
    report.append("="*70)
    
    all_passed = True
    
    for result in results:
        site = result['site_name']
        issues = result['issues']
        
        report.append(f"\n{site}:")
        report.append(f"  Files analyzed: {result['files_analyzed']}")
        
        # Check each issue type
        if issues['absolute_file_paths']:
            report.append(f"\n  ❌ FAIL: Absolute file paths found ({len(issues['absolute_file_paths'])}):")
            for source, attr, link in issues['absolute_file_paths'][:5]:
                report.append(f"     {source}: {attr}=\"{link}\"")
            if len(issues['absolute_file_paths']) > 5:
                report.append(f"     ... and {len(issues['absolute_file_paths']) - 5} more")
            all_passed = False
        else:
            report.append(f"\n  ✓ No absolute file paths")
        
        if issues['hardcoded_home_dir']:
            report.append(f"\n  ❌ FAIL: Hardcoded home directory paths ({len(issues['hardcoded_home_dir'])}):")
            for source, attr, link in issues['hardcoded_home_dir'][:5]:
                report.append(f"     {source}: {attr}=\"{link}\"")
            if len(issues['hardcoded_home_dir']) > 5:
                report.append(f"     ... and {len(issues['hardcoded_home_dir']) - 5} more")
            all_passed = False
        else:
            report.append(f"  ✓ No hardcoded home directory paths")
        
        if issues['absolute_http_urls']:
            report.append(f"\n  ⚠️  WARNING: Same-domain absolute URLs ({len(issues['absolute_http_urls'])}):")
            for source, attr, link in issues['absolute_http_urls'][:5]:
                report.append(f"     {source}: {attr}=\"{link}\"")
            if len(issues['absolute_http_urls']) > 5:
                report.append(f"     ... and {len(issues['absolute_http_urls']) - 5} more")
            # These are portability issues but not critical
        else:
            report.append(f"  ✓ No same-domain absolute URLs")
        
        if issues['fragment_only']:
            report.append(f"\n  ℹ️  Fragment-only links: {len(issues['fragment_only'])} (acceptable)")
        
        report.append(f"\n  ✓ Relative links: {len(issues['relative_links'])} (portable)")
    
    # Overall assessment
    report.append("\n" + "="*70)
    report.append("PORTABILITY ASSESSMENT:")
    report.append("="*70)
    
    if all_passed:
        report.append("\n✅ PASS: Directory is portable!")
        report.append("  - No absolute file paths")
        report.append("  - No hardcoded home directory paths")
        report.append("  - Links use relative paths")
        report.append("  - Directory can be moved to any location")
        report.append("  - Directory can be copied to another machine")
    else:
        report.append("\n❌ FAIL: Portability issues found!")
        report.append("  - Some links will break when directory is moved")
        report.append("  - Run convert_links.py to fix absolute URLs")
    
    # Recommendations
    report.append("\n" + "-"*70)
    report.append("RECOMMENDATIONS:")
    report.append("-"*70)
    report.append("1. Keep directory structure intact when moving")
    report.append("2. Relative links will work regardless of parent directory")
    report.append("3. External http:// links require internet connection")
    report.append("4. For offline use, ensure all pages are downloaded")
    
    return "\n".join(report), all_passed


def test_directory_move(site_path, temp_dir):
    """
    Test if links work after moving directory to a new location.
    This is a dry-run test that simulates the move.
    """
    print(f"\n{'='*60}")
    print("PORTABILITY TEST (Simulation)")
    print(f"{'='*60}")
    
    # Check that relative links would work
    html_files = list(Path(site_path).rglob('*.html'))
    sample_size = min(10, len(html_files))
    
    print(f"Testing {sample_size} files for relative link validity...")
    
    valid = 0
    invalid = 0
    
    for html_file in html_files[:sample_size]:
        try:
            with open(html_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Check if file can be read and parsed
            parser = LinkExtractor()
            parser.feed(content)
            
            # Verify relative links point to existing files
            for attr_type, link in parser.links:
                link = link.strip()
                if link and not link.startswith('#') and not link.startswith('http'):
                    # This is a relative link
                    # Check if it would resolve correctly
                    if link.startswith('../'):
                        # Link goes up one directory
                        parent_dir = html_file.parent.parent
                        target = parent_dir / link.replace('../', '')
                        if target.exists():
                            valid += 1
                        else:
                            invalid += 1
                            print(f"  ⚠️  Missing: {html_file.name} -> {link}")
                    elif not link.startswith('/'):
                        # Relative link in same directory
                        target = html_file.parent / link
                        if target.exists():
                            valid += 1
                        else:
                            invalid += 1
                            print(f"  ⚠️  Missing: {html_file.name} -> {link}")
                            
        except Exception as e:
            print(f"  Error testing {html_file}: {e}")
    
    print(f"\nTest results: {valid} valid, {invalid} invalid")
    return invalid == 0


def main():
    """Main function to verify link portability."""
    script_dir = Path(__file__).parent
    
    print("Phase 1 Validation - Step 4: Verify Link Portability")
    print("="*60)
    
    sites = [
        ('ontariotrees.com', 'ontariotrees.com'),
        ('ontariowildflowers.com', 'ontariowildflowers.com'),
    ]
    
    results = []
    for site_name, site_dir in sites:
        site_path = script_dir / site_dir
        if site_path.exists():
            result = check_portability(site_path, site_dir)
            results.append(result)
        else:
            print(f"Warning: {site_path} not found")
    
    # Generate report
    report, passed = generate_portability_report(results)
    print(report)
    
    # Save report
    report_file = script_dir / 'portability_analysis.txt'
    with open(report_file, 'w') as f:
        f.write(report)
    print(f"\nReport saved to: {report_file}")
    
    # Test directory move simulation
    print("\n" + "="*60)
    print("TESTING RELATIVE LINK VALIDITY")
    print("="*60)
    
    for site_name, site_dir in sites:
        site_path = script_dir / site_dir
        if site_path.exists():
            test_directory_move(site_path, None)
    
    return passed


if __name__ == '__main__':
    main()
