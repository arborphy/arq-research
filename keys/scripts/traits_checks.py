#!/usr/bin/env python3
"""
Trait synonyms validation and consistency checks.

This script validates trait_synonyms.json and checks for consistency
between different sections of the file.
"""
import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
TRAITS_FILE = ROOT / "trait_synonyms.json"

# Extended terms for scanning - includes common botanical terms
BOTANICAL_TERMS = [
    "zygomorphic", "actinomorphic", "alternate", "opposite", "whorled",
    "basal", "rosette", "herbaceous", "vine", "acaulescent", "decussate",
    "distichous", "capitulum", "dimerous", "trimerous", "tetramerous",
    "pentamerous", "hexamerous", "polymerous", "scandent", "liana",
    "verticillate", "phyllotaxis", "phyllotaxy", "aphyllous"
]

TERMS_PATTERN = re.compile(
    "|".join(re.escape(term) for term in BOTANICAL_TERMS),
    re.IGNORECASE
)


def load_json(path: Path) -> Dict[str, Any]:
    """Load and parse JSON file with better error handling."""
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"ERROR: File not found: {path}", file=sys.stderr)
        sys.exit(1)
    except PermissionError:
        print(f"ERROR: Permission denied reading: {path}", file=sys.stderr)
        sys.exit(1)


def validate_json(file_path: Optional[Path] = None) -> int:
    """Validate JSON syntax and basic structure."""
    target_file = file_path or TRAITS_FILE
    
    try:
        data = load_json(target_file)
        
        # Basic structure validation
        required_sections = ["sources", "synonymToSource", "synonymDefinitions"]
        missing_sections = [s for s in required_sections if s not in data]
        
        if missing_sections:
            print(f"JSON structure warning: Missing sections: {missing_sections}")
            return 1
            
        print(f"JSON OK: {target_file}")
        return 0
        
    except json.JSONDecodeError as e:
        print(f"JSON INVALID: {target_file}")
        print(f"  Error: {e}")
        print(f"  Line {e.lineno}, Column {e.colno}")
        return 1


def get_defined_sources(data: Dict[str, Any]) -> Set[str]:
    """Extract all source IDs defined in the sources section."""
    sources = data.get("sources", {})
    if not isinstance(sources, dict):
        return set()
    return set(sources.keys())


def iter_sources_in_definitions(node: Any, path: str = "") -> Iterable[Tuple[str, str]]:
    """Recursively find all source references with their paths."""
    if isinstance(node, dict):
        if "source" in node and isinstance(node["source"], str):
            yield (node["source"], path)
        for key, value in node.items():
            new_path = f"{path}.{key}" if path else key
            yield from iter_sources_in_definitions(value, new_path)
    elif isinstance(node, list):
        for i, value in enumerate(node):
            new_path = f"{path}[{i}]"
            yield from iter_sources_in_definitions(value, new_path)


def get_referenced_sources(data: Dict[str, Any]) -> Tuple[Set[str], Dict[str, List[str]]]:
    """Get all referenced sources and their locations."""
    refs: Set[str] = set()
    locations: Dict[str, List[str]] = {}

    # From synonymToSource: values are lists of source IDs
    sts = data.get("synonymToSource", {})
    if isinstance(sts, dict):
        for synonym, source_list in sts.items():
            if isinstance(source_list, list):
                for sid in source_list:
                    if isinstance(sid, str):
                        refs.add(sid)
                        locations.setdefault(sid, []).append(f"synonymToSource.{synonym}")

    # From synonymDefinitions: collect any .source fields
    sdefs = data.get("synonymDefinitions", {})
    for source_id, path in iter_sources_in_definitions(sdefs, "synonymDefinitions"):
        refs.add(source_id)
        locations.setdefault(source_id, []).append(path)

    return refs, locations


def check_sources(verbose: bool = False) -> int:
    """Check source ID consistency with optional verbose output."""
    data = load_json(TRAITS_FILE)
    defined = get_defined_sources(data)
    referenced, locations = get_referenced_sources(data)

    undef = sorted(referenced - defined)
    unused = sorted(defined - referenced)

    print("=== Source ID Check ===")
    print("Undefined (referenced but not defined):")
    if undef:
        for s in undef:
            print(f"  {s}")
            if verbose and s in locations:
                for loc in locations[s][:3]:  # Show first 3 locations
                    print(f"    used in: {loc}")
                if len(locations[s]) > 3:
                    print(f"    ... and {len(locations[s]) - 3} more locations")
    else:
        print("  (none)")
    
    print()
    print("Defined but never referenced:")
    if unused:
        for s in unused:
            print(f"  {s}")
    else:
        print("  (none)")

    return 0 if not undef else 2


def get_synonyms_from_sources(data: Dict[str, Any]) -> Set[str]:
    """Extract synonym keys from synonymToSource section."""
    sts = data.get("synonymToSource", {})
    return set(sts.keys()) if isinstance(sts, dict) else set()


def get_synonyms_from_defs(data: Dict[str, Any]) -> Set[str]:
    """Extract synonym keys from synonymDefinitions section."""
    sdefs = data.get("synonymDefinitions", {})
    if not isinstance(sdefs, dict):
        return set()

    keys: Set[str] = set()
    for top_k, top_v in sdefs.items():
        if top_k == "_metadata":
            continue
        if isinstance(top_v, dict):
            for k in top_v.keys():
                if k == "traitId":
                    continue
                keys.add(k)
    return keys


def check_coverage() -> int:
    """Check synonym coverage between sections."""
    data = load_json(TRAITS_FILE)
    src_syns = get_synonyms_from_sources(data)
    def_syns = get_synonyms_from_defs(data)

    missing_in_defs = sorted(src_syns - def_syns)
    missing_in_sources = sorted(def_syns - src_syns)

    print("=== Coverage Check ===")
    print("In synonymToSource but missing in synonymDefinitions:")
    if missing_in_defs:
        for s in missing_in_defs:
            print(f"  {s}")
    else:
        print("  (none)")
    
    print()
    print("In synonymDefinitions but missing in synonymToSource:")
    if missing_in_sources:
        for s in missing_in_sources:
            print(f"  {s}")
    else:
        print("  (none)")

    return 0 if not missing_in_defs and not missing_in_sources else 3


def scan_usage(pattern: Optional[str] = None, include_hidden: bool = False) -> int:
    """Scan for botanical terms with configurable pattern and file filtering."""
    search_pattern = TERMS_PATTERN
    if pattern:
        try:
            search_pattern = re.compile(pattern, re.IGNORECASE)
        except re.error as e:
            print(f"ERROR: Invalid regex pattern '{pattern}': {e}", file=sys.stderr)
            return 1

    files = []
    for name in os.listdir(ROOT):
        # Skip hidden files unless requested
        if not include_hidden and name.startswith('.'):
            continue
        if name.endswith((".json", ".txt", ".md")):
            files.append(ROOT / name)

    print("=== Usage Scan ===")
    found_any = False
    match_count = 0
    
    for fp in sorted(files):
        file_matches = 0
        try:
            with fp.open("r", encoding="utf-8", errors="replace") as f:
                for i, line in enumerate(f, 1):
                    matches = list(search_pattern.finditer(line))
                    if matches:
                        # Highlight matches in output
                        display_line = line.rstrip()
                        for match in reversed(matches):  # Reverse to preserve positions
                            term = match.group()
                            start, end = match.span()
                            display_line = (
                                display_line[:start] +
                                f"**{term}**" +
                                display_line[end:]
                            )
                        print(f"{fp.name}:{i}: {display_line}")
                        file_matches += len(matches)
                        found_any = True
        except Exception as e:
            print(f"WARN: could not read {fp}: {e}", file=sys.stderr)
            continue
        
        if file_matches > 0:
            match_count += file_matches
    
    if found_any:
        print(f"\nFound {match_count} term occurrences across {len([f for f in files if f.exists()])} files")
    else:
        print("No matching terms found")

    return 0


def main(argv: Iterable[str]) -> int:
    """Main entry point with improved argument parsing."""
    p = argparse.ArgumentParser(
        description="Trait synonyms validation and consistency checks",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s validate-json                    # Basic JSON validation
  %(prog)s check-sources --verbose          # Detailed source checking
  %(prog)s scan-usage --pattern "herb.*"    # Custom pattern search
  %(prog)s all                              # Run all checks
        """
    )
    
    sub = p.add_subparsers(dest="cmd", required=True, help="Available commands")

    # validate-json subcommand
    validate_parser = sub.add_parser("validate-json", help="Validate trait_synonyms.json syntax and structure")
    validate_parser.add_argument("--file", type=Path, help="Alternative file to validate")

    # check-sources subcommand
    sources_parser = sub.add_parser("check-sources", help="Verify referenced source IDs exist and list unused sources")
    sources_parser.add_argument("--verbose", "-v", action="store_true", help="Show detailed source usage locations")

    # check-coverage subcommand
    sub.add_parser("check-coverage", help="Compare synonyms coverage between sections")

    # scan-usage subcommand
    scan_parser = sub.add_parser("scan-usage", help="Search local files for botanical terms")
    scan_parser.add_argument("--pattern", help="Custom regex pattern to search for")
    scan_parser.add_argument("--include-hidden", action="store_true", help="Include hidden files in search")

    # all subcommand
    sub.add_parser("all", help="Run all checks")

    args = p.parse_args(list(argv))

    if args.cmd == "validate-json":
        return validate_json(args.file)
    elif args.cmd == "check-sources":
        return check_sources(args.verbose)
    elif args.cmd == "check-coverage":
        return check_coverage()
    elif args.cmd == "scan-usage":
        return scan_usage(args.pattern, args.include_hidden)
    elif args.cmd == "all":
        print("Running all trait synonym checks...\n")
        rc = 0
        checks = [
            ("JSON Validation", lambda: validate_json()),
            ("Source Check", lambda: check_sources()),
            ("Coverage Check", lambda: check_coverage()),
            ("Usage Scan", lambda: scan_usage())
        ]
        
        for name, check_fn in checks:
            print(f"--- {name} ---")
            code = check_fn()
            rc = rc or code
            print()
        
        if rc == 0:
            print("✓ All checks passed!")
        else:
            print("✗ Some checks failed - see output above")
        
        return rc

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

