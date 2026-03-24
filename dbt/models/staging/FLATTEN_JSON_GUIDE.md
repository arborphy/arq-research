# Flattening JSON with dbt and Snowflake


We're going to use two key snowflake features to normalize the JSON data into 3rd normal form

**VARIANT Column Type**: Stores JSON data natively in Snowflake. This is where the raw JSON is loaded. We can either load them manually (e.g. using SnowSQL) or use an external ingestion tools such as Fivetran or Airbyte.

**FLATTEN**: Explodes nested arrays/objects into rows. The `LATERAL` keyword allows joining the flattened results back to the source row. Check the [docs](https://docs.snowflake.com/en/sql-reference/functions/flatten) for more details

## Loading JSON as VARIANT

First, load raw JSON files into Snowflake tables with a VARIANT column:

```python
# Python script using snowflake-connector-python
cursor.execute(f"CREATE OR REPLACE TABLE {table_name} (json_data VARIANT, loaded_at TIMESTAMP_NTZ)")
cursor.execute(f"INSERT INTO {table_name} SELECT PARSE_JSON(%s), CURRENT_TIMESTAMP()", (json_string,))
```

or you can load the file from local machine using SnowSQL:

## Flattening to 3rd Normal Form

We will be using DBT to create the workflow for flattening the JSON. 


### 1. Define Source

This is basically the source from where DBT is going to pull the variant objects.

```sql
-- dbt/models/staging/_source.yml
sources:
  - name: traits
    tables:
      - name: synonyms_raw
        identifier: TRAIT_SYNONYMS_RAW
```

### 2. Flatten Top-Level Objects
This is where some manual work is required, in order to define how to flatten the JSON structure into separate tables. The goal is to create separate models for each entity, ensuring no repeating groups or transitive dependencies.

```sql
-- Extract source metadata (trait_synonym_sources.sql)
-- Flattens the "sources" object into a table with one row per source
SELECT
    src.key::string as source_id,
    src.value:name::string as source_name,
    src.value:author::string as author,
    src.value:type::string as source_type,
    src.value:year::integer as year,
    src.value:isbn::string as isbn,
    src.value:url::string as url,
    loaded_at
FROM {{ source('traits', 'synonyms_raw') }},
LATERAL FLATTEN(input => json_data:sources) src
```

### 3. Flatten Key-Value Mappings (Many-to-Many)

This pattern uses two FLATTEN operations: the first flattens the object keys to get synonyms, and the second flattens the array of values to get multiple source IDs per synonym. This creates a many-to-many relationship table.

```sql
-- Extract synonym-to-source mappings (trait_synonym_mappings.sql)
-- Flattens "synonymToSource" where each synonym maps to multiple sources
SELECT
    mapping.key::string as synonym,
    src_id.value::string as source_id,
    loaded_at
FROM {{ source('traits', 'synonyms_raw') }},
LATERAL FLATTEN(input => json_data:synonymToSource) mapping,
LATERAL FLATTEN(input => mapping.value) src_id
WHERE src_id.value is not null
```

### 4. Flatten Nested Category Definitions

For hierarchical JSON structures (object of objects), chain multiple FLATTEN operations. The first extracts categories, the second extracts terms within each category. The WHERE clause filters out metadata and ensures we only process valid definition objects.

```sql
-- Extract definitions nested under categories (trait_synonym_definitions.sql)
-- Two-level flatten: categories -> terms within each category
SELECT
    category.key::string as category,
    defn.key::string as synonym,
    defn.value:definition::string as definition,
    defn.value:commonLanguageDefinition::string as common_language_definition,
    defn.value:source::string as source_id,
    defn.value:page::integer as page,
    loaded_at
FROM {{ source('traits', 'synonyms_raw') }},
LATERAL FLATTEN(input => json_data:synonymDefinitions) category,
LATERAL FLATTEN(input => category.value) defn
WHERE category.key != '_metadata'
  AND defn.key != 'traitId'
  AND typeof(defn.value) = 'OBJECT'
```

## Running the Models

After defining your dbt models, execute them to create the flattened tables in Snowflake. The `--select` flag allows you to run specific models or patterns. 

```bash
# Run all staging models
dbt run --select staging.*

# Run the synonyms example
dbt run --select 'staging.trait_synonym_*'
```

#### Semantic model

Once the data is flattened, we can use RAI to map the tables to the the semantic model. For examples, check `kg/model/trait.py` and `kg/apps/trait_examples.py`