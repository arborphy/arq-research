# Example 1: Flattening Newcomb Trait Ontology

This example demonstrates how to load and flatten the **Newcomb_refined.json** file, which contains a hierarchical botanical trait ontology.

## Source Data

**File:** `keys/Newcomb_refined.json`

**Structure:**
```json
{
  "metadata": {...},
  "traits": {
    "Flower Symmetry and Parts": {
      "id": "flower_symmetry_and_parts",
      "description": "...",
      "synonyms": ["floral symmetry", "perianth symmetry"],
      "values": [
        {
          "id": "irregular",
          "label": "Irregular Flowers",
          "description": "...",
          "synonyms": ["zygomorphic", "bilateral symmetry"],
          "values": [...]  // Nested subcategories
        }
      ]
    }
  }
}
```

## Pipeline

```
keys/Newcomb_refined.json
    ↓ (keys/scripts/load_traits_to_snowflake.py)
CHAKER_TEMP.PUBLIC.TRAIT_NEWCOMB_RAW (VARIANT)
    ↓ (dbt models below)
Flattened Tables
```

## dbt Models

### 1. [trait_newcomb_metadata.sql](trait_newcomb_metadata.sql)
Extracts ontology metadata (title, version, source information).

**Output:** Single row with metadata fields

### 2. [trait_newcomb_traits.sql](trait_newcomb_traits.sql)
Flattens top-level trait categories.

**Output:** One row per trait category
```sql
trait_id: "flower_symmetry_and_parts"
trait_key: "Flower Symmetry and Parts"
description: "Symmetry type and number of petals..."
```

### 3. [trait_newcomb_trait_synonyms.sql](trait_newcomb_trait_synonyms.sql)
Flattens trait-level synonyms.

**Output:** One row per trait-synonym pair
```sql
trait_id: "flower_symmetry_and_parts"
synonym: "floral symmetry"
```

### 4. [trait_newcomb_values.sql](trait_newcomb_values.sql)
Flattens trait values with **2-level nesting support**.

**Output:** One row per trait value at any nesting level
```sql
trait_id: "growth_form"
value_id: "wildflower"
label: "Wildflower"
parent_value_id: NULL
nesting_level: 1

trait_id: "growth_form"
value_id: "forb"
label: "Forb"
parent_value_id: "wildflower"
nesting_level: 2
```

### 5. [trait_newcomb_value_synonyms.sql](trait_newcomb_value_synonyms.sql)
Flattens value-level synonyms at all nesting levels.

**Output:** One row per value-synonym pair
```sql
value_id: "irregular"
synonym: "zygomorphic"
nesting_level: 1
```

## Key Features Demonstrated

### 1. **Extracting Metadata**
```sql
json_data:metadata:title::string as title
json_data:metadata:version::string as version
```

### 2. **Flattening Objects**
```sql
lateral flatten(input => json_data:traits) trait
trait.key::string as trait_key
trait.value:id::string as trait_id
```

### 3. **Flattening Arrays**
```sql
lateral flatten(input => trait.value:synonyms, outer => true) syn
syn.value::string as synonym
```

### 4. **Handling Nested Hierarchies (2 levels)**
```sql
-- Level 1
lateral flatten(input => trait.value:values) val

-- Level 2 (nested)
lateral flatten(input => val.value:values) nested_val
```

### 5. **Union for Multiple Levels**
```sql
-- Combine level 1 and level 2 values
select * from trait_values_level1
union all
select * from trait_values_level2
```

### 6. **Preserving Relationships**
```sql
parent_value_id: val.value:id::string  -- Links child to parent
nesting_level: 1 or 2  -- Tracks depth
```

## Running This Example

```bash
# 1. Load JSON to Snowflake
python keys/scripts/load_traits_to_snowflake.py

# 2. Run dbt models
dbt run --select newcomb_example.*

# 3. Query results
select * from chaker_temp.public.trait_newcomb_traits;
select * from chaker_temp.public.trait_newcomb_values;
```

## Use Cases

This pattern is useful for:
- **Hierarchical taxonomies** with parent-child relationships
- **Multi-level categories** (e.g., product catalogs, org charts)
- **Nested configurations** (e.g., application settings)
- **Ontologies and knowledge graphs** with classification hierarchies

## Example Queries

### Get trait hierarchy
```sql
select
    t.trait_key,
    parent.label as parent_value,
    child.label as child_value
from trait_newcomb_values child
join trait_newcomb_traits t on child.trait_id = t.trait_id
left join trait_newcomb_values parent
    on child.parent_value_id = parent.value_id
where child.nesting_level = 2
order by t.trait_key, parent.label;
```

### Find all synonyms for a value
```sql
select
    v.label,
    array_agg(distinct vs.synonym) as all_synonyms
from trait_newcomb_values v
left join trait_newcomb_value_synonyms vs
    on v.value_id = vs.value_id
where v.value_id = 'irregular'
group by v.label;
```
