# dbt Staging Models - JSON Flattening Examples

This directory contains **two complete examples** demonstrating how to use dbt to load and flatten JSON files from Snowflake VARIANT columns into structured tables.

## Overview

Both examples follow the same pattern:
1. Load JSON file to Snowflake as VARIANT (using Python script)
2. Use dbt with `LATERAL FLATTEN` to extract nested structures
3. Create normalized tables ready for analysis or Knowledge Graph ingestion

## Data Flow

```
JSON Files
    ↓ keys/scripts/load_traits_to_snowflake.py
CHAKER_TEMP.PUBLIC.*_RAW (VARIANT columns)
    ↓ dbt models
CHAKER_TEMP.PUBLIC.TRAIT_* (flattened tables)
    ↓ kg/model/core/trait.py
RelationalAI Knowledge Graph
```

## Example 1: Hierarchical Ontology

**Directory:** [newcomb_example/](newcomb_example/)
**Source:** `keys/Newcomb_refined.json`

**Demonstrates:**
- Extracting metadata from nested objects
- Flattening objects into tables
- Handling 2-level nested hierarchies (parent-child relationships)
- Preserving hierarchical relationships with `parent_value_id`
- Working with arrays of synonyms

**Models:** 5 SQL files demonstrating metadata extraction, category flattening, and hierarchical value handling

**Use Cases:** Taxonomies, product catalogs, org charts, configuration trees

[→ See full documentation](newcomb_example/README.md)

## Example 2: Reference Mappings

**Directory:** [synonyms_example/](synonyms_example/)
**Source:** `keys/trait_synonyms.json`

**Demonstrates:**
- Flattening nested objects (sources)
- Flattening key-value pairs (synonym→source mappings)
- Flattening arrays within key-value pairs
- Multi-level object traversal (category → synonym → definition)
- Type casting (integers, booleans)
- Filtering metadata keys

**Models:** 3 SQL files demonstrating source metadata, mapping tables, and detailed definitions

**Use Cases:** Reference data with citations, glossaries, cross-referencing systems

[→ See full documentation](synonyms_example/README.md)

## Quick Start

### 1. Load JSON to Snowflake

```bash
python keys/scripts/load_traits_to_snowflake.py
```

Creates VARIANT tables:
- `CHAKER_TEMP.PUBLIC.TRAIT_NEWCOMB_RAW`
- `CHAKER_TEMP.PUBLIC.TRAIT_SYNONYMS_RAW`

### 2. Run dbt Models

```bash
# Run both examples
dbt run --select newcomb_example.* synonyms_example.*

# Or run individually
dbt run --select newcomb_example.*
dbt run --select synonyms_example.*
```

### 3. Query Results

```sql
-- Example 1: Hierarchical data
SELECT * FROM chaker_temp.public.trait_newcomb_traits;
SELECT * FROM chaker_temp.public.trait_newcomb_values;

-- Example 2: Reference mappings
SELECT * FROM chaker_temp.public.trait_synonym_sources;
SELECT * FROM chaker_temp.public.trait_synonym_mappings;
```

## Common Patterns

### Pattern 1: Flatten Object Keys
```sql
LATERAL FLATTEN(input => json_data:traits) trait
trait.key::string AS trait_key
trait.value:id::string AS trait_id
```

### Pattern 2: Flatten Arrays
```sql
LATERAL FLATTEN(input => trait.value:synonyms, outer => true) syn
syn.value::string AS synonym
```

### Pattern 3: Handle Multi-Level Nesting
```sql
-- Level 1
LATERAL FLATTEN(input => parent.value:values) child
-- Level 2
LATERAL FLATTEN(input => child.value:values) grandchild
-- Union results
SELECT * FROM level1 UNION ALL SELECT * FROM level2
```

### Pattern 4: Type Casting from VARIANT
```sql
field:year::integer AS year
field:verified::boolean AS verified
field:name::string AS name
```

## Testing

Both examples include dbt tests:

```bash
dbt test --select newcomb_example.*
dbt test --select synonyms_example.*
```

Tests cover:
- `not_null` - Required fields
- `unique` - Primary keys
- `relationships` - Foreign keys
- `accepted_values` - Enum validation

## Change Tracking for RAI

All models include this post-hook for RelationalAI integration:
```sql
{{ config(post_hook='alter table {{this}} set change_tracking=true') }}
```

## Integration with RelationalAI

After flattening, the data is loaded into a Knowledge Graph:

```python
# See kg/model/core/trait.py
m.Trait = m.Concept("Trait", identify_by={"id": m.TraitId})
m.Trait.key = relationship to TraitKey
m.Trait.description = relationship to TraitDescription
m.Trait.synonym = multi-valued relationship to TraitSynonym
```

Query the KG:
```bash
uv run -m kg.apps.trait_examples all_traits
uv run -m kg.apps.trait_examples trait_synonyms --trait-id growth_form
```

## Files in This Directory

```
staging/
├── README.md                    # This file
├── _source.yml                  # Source table definitions
├── newcomb_example/             # Example 1: Hierarchical ontology
│   ├── README.md               # Detailed documentation
│   ├── trait_newcomb_*.sql     # 5 flattening models
│   └── trait_newcomb.yml       # Model documentation & tests
├── synonyms_example/            # Example 2: Reference mappings
│   ├── README.md               # Detailed documentation
│   ├── trait_synonym_*.sql     # 3 flattening models
│   └── trait_synonyms.yml      # Model documentation & tests
└── [other staging models...]    # Observation & taxon models
```

## Learn More

- **Newcomb Example:** Complete walkthrough of hierarchical data flattening
- **Synonyms Example:** Complete walkthrough of reference mapping flattening
- **Python Loader:** [keys/scripts/load_traits_to_snowflake.py](../../keys/scripts/load_traits_to_snowflake.py)
- **RAI Integration:** [kg/model/core/trait.py](../../kg/model/core/trait.py)
- **Query Examples:** [kg/apps/trait_examples.py](../../kg/apps/trait_examples.py)
