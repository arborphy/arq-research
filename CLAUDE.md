# Arborphy

A knowledge graph (KG) for wildflower and botanical data, built on RelationalAI + Snowflake.

## Stack

- **RelationalAI (RAI)** — knowledge graph, reasoning, semantic queries
- **Snowflake** — data warehouse, source/sink for RAI
- **DBT** — data transformations (if needed)
- **RAI Python SDK** — [`https://private.relational.ai/api/`](https://private.relational.ai/api/)

## Project Structure

```
data/        # Source CSVs (e.g. Newcomb wildflower guide extract)
docs/        # Data model sketches, app overview, example queries
```

## Development Principles

- **Keep code concise.** Prefer brevity. No unnecessary boilerplate.
- **Use existing libraries.** Don't reinvent what a library already does — but ask before adding a new dependency.
- **Ask before adding dependencies.** New packages require explicit approval.

## Domain Model (summary)

Core entities: `Taxa` (species/genus/hierarchy), `Feature`, `FeatureValue`, `Source`, `Observation`, `ReferenceFrame`.

Key predicates: `parent/child` (DAG), `hasFeature`, `hasValue`, `observedAt`, `isType`.

See `docs/DataModel Sketch.md` for full model and `docs/RefData & App Overview.md` for product context.

## Data

Primary seed data: `data/Newcomb_Species_Features_Consolidated.csv`
- Columns: species name, iNaturalist link, key group, flower type, plant type, leaf type, subgroups, description.

## Key RAI SDK Patterns

```python
from relationalai.semantics import Model, define, select, where, String, Integer

m = Model()

# Define concepts
Species = m.Concept("Species")
Feature = m.Concept("Feature")

# Define properties
Species.name = m.Property(f"{Species} is named {String:name}")
Feature.label = m.Property(f"{Feature} has label {String:label}")

# Load data
define(
    Species.new(name="Trillium grandiflorum"),
    Feature.new(label="flower_type"),
)

# Query
where(Species.name == "Trillium grandiflorum").select(Species.name).to_df()
```

Refer to the RAI SDK docs for `Model`, `Concept`, `Relationship`, `Property`, `define`, `where`, `select`.
