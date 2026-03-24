#!/usr/bin/env python3
"""Flatten JSON files to CSV using pandas."""

import json
import pandas as pd
from pathlib import Path

# Paths
KEYS_DIR = Path(__file__).parent.parent
SYNONYM_FILE = KEYS_DIR / "trait_synonyms.json"
OUTPUT_DIR = KEYS_DIR / "flattened_csv"
OUTPUT_DIR.mkdir(exist_ok=True)

def flatten_synonyms():
    """Flatten trait_synonyms.json into 3 CSV files."""
    with open(SYNONYM_FILE) as f:
        data = json.load(f)

    # 1. Flatten sources
    sources = []
    for source_id, source_data in data.get("sources", {}).items():
        sources.append({
            "source_id": source_id,
            "source_name": source_data.get("name"),
            "author": source_data.get("author"),
            "year": source_data.get("year"),
            "source_type": source_data.get("type"),
            "isbn": source_data.get("isbn"),
            "doi": source_data.get("doi"),
            "url": source_data.get("url"),
            "publisher": source_data.get("publisher"),
            "journal": source_data.get("journal"),
        })
    pd.DataFrame(sources).to_csv(OUTPUT_DIR / "synonym_sources.csv", index=False)

    # 2. Flatten synonym-to-source mappings
    mappings = []
    for synonym, source_ids in data.get("synonymToSource", {}).items():
        for source_id in source_ids:
            mappings.append({"synonym": synonym, "source_id": source_id})
    pd.DataFrame(mappings).to_csv(OUTPUT_DIR / "synonym_mappings.csv", index=False)

    # 3. Flatten definitions
    definitions = []
    for category, terms in data.get("synonymDefinitions", {}).items():
        if category == "_metadata":
            continue
        for synonym, defn_data in terms.items():
            if synonym == "traitId" or not isinstance(defn_data, dict):
                continue
            definitions.append({
                "category": category,
                "synonym": synonym,
                "definition": defn_data.get("definition"),
                "common_language_definition": defn_data.get("commonLanguageDefinition"),
                "source_id": defn_data.get("source"),
                "page": defn_data.get("page"),
            })
    pd.DataFrame(definitions).to_csv(OUTPUT_DIR / "synonym_definitions.csv", index=False)

    print(f"Created {len(sources)} sources, {len(mappings)} mappings, {len(definitions)} definitions")
    print(f"Output: {OUTPUT_DIR}")

if __name__ == "__main__":
    flatten_synonyms()
