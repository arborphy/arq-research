"""
Trait Query Examples

This module provides example queries for analyzing botanical trait data from the
Newcomb wildflower identification ontology and trait synonym sources, including
trait categories, descriptions, synonyms, and their authoritative sources.

Run queries using `uv run -m kg.apps.trait_examples <function> <args>`

Basic Trait Queries:
- `uv run -m kg.apps.trait_examples all_traits`
- `uv run -m kg.apps.trait_examples traits_with_synonym_count`
- `uv run -m kg.apps.trait_examples trait_synonyms --trait-id flower_symmetry_and_parts`
- `uv run -m kg.apps.trait_examples all_trait_synonyms`

Synonym Source Queries:
- `uv run -m kg.apps.trait_examples synonyms_from_books`
- `uv run -m kg.apps.trait_examples synonyms_by_source_type --source-type book`
- `uv run -m kg.apps.trait_examples synonym_with_sources --synonym actinomorphic`
- `uv run -m kg.apps.trait_examples synonyms_with_definitions_from_books`
- `uv run -m kg.apps.trait_examples source_statistics`
"""

import argparse
import inspect
import sys
from typing import Callable, Dict

import relationalai.semantics as rai

from kg.model import define_trait_model, ARQModel


def all_traits(arq: ARQModel) -> rai.Fragment:
    """List all trait categories with their keys and descriptions.

    Returns:
        A query fragment with columns:
        - trait_id: Machine-readable identifier (e.g., "flower_symmetry_and_parts")
        - trait_key: Human-readable name (e.g., "Flower Symmetry and Parts")
        - trait_description: Description of the trait category
    """
    return rai.where(
        arq.Trait.key(arq.TraitKey),
        arq.Trait.description(arq.TraitDescription),
    ).select(
        arq.Trait.id.alias("trait_id"),
        arq.TraitKey.alias("trait_key"),
        arq.TraitDescription.alias("trait_description"),
    )


def traits_with_synonym_count(arq: ARQModel) -> rai.Fragment:
    """Count synonyms for each trait category.

    Returns:
        A query fragment with columns:
        - trait_id: Machine-readable identifier
        - trait_key: Human-readable name
        - synonym_count: Number of synonyms for this trait
    """
    return rai.where(
        arq.Trait.key(arq.TraitKey),
        synonym_count := rai.count(arq.Trait.synonym).per(arq.Trait),
    ).select(
        arq.Trait.id.alias("trait_id"),
        arq.TraitKey.alias("trait_key"),
        synonym_count.alias("synonym_count"),
    )


def trait_synonyms(arq: ARQModel, trait_id: str = "flower_symmetry_and_parts") -> rai.Fragment:
    """Get all synonyms for a specific trait category.

    Args:
        trait_id: The trait identifier (default: "flower_symmetry_and_parts")

    Returns:
        A query fragment with columns:
        - trait_id: Machine-readable identifier
        - trait_key: Human-readable name
        - synonym: Synonym term for this trait
    """
    return rai.where(
        arq.Trait.id(trait_id),
        arq.Trait.key(arq.TraitKey),
        arq.Trait.synonym(arq.TraitSynonym),
    ).select(
        arq.Trait.id.alias("trait_id"),
        arq.TraitKey.alias("trait_key"),
        arq.TraitSynonym.alias("synonym"),
    )


def all_trait_synonyms(arq: ARQModel) -> rai.Fragment:
    """Get all trait categories with all their synonyms.

    Returns:
        A query fragment with columns:
        - trait_id: Machine-readable identifier
        - trait_key: Human-readable name
        - synonym: Synonym term
    """
    return rai.where(
        arq.Trait.key(arq.TraitKey),
        arq.Trait.synonym(arq.TraitSynonym),
    ).select(
        arq.Trait.id.alias("trait_id"),
        arq.TraitKey.alias("trait_key"),
        arq.TraitSynonym.alias("synonym"),
    )


def synonyms_from_books(arq: ARQModel) -> rai.Fragment:
    """Get all synonyms that are documented in book sources.

    Returns:
        A query fragment with columns:
        - synonym: The botanical term
        - source_name: Name of the book
        - author: Book author
        - year: Publication year
        - isbn: ISBN if available
    """
    return rai.where(
        arq.TraitSynonym.source(arq.SynonymSource),
        arq.SynonymSource.source_type(arq.SourceType),
        arq.SourceType == "book",
        arq.SynonymSource.name(arq.SourceName),
    ).select(
        arq.TraitSynonym.alias("synonym"),
        arq.SourceName.alias("source_name"),
        arq.SynonymSource.author.alias("author"),
        arq.SynonymSource.year,
        arq.SynonymSource.isbn,
    )


def synonyms_by_source_type(arq: ARQModel, source_type: str = "book") -> rai.Fragment:
    """Get all synonyms from sources of a specific type.

    Args:
        source_type: Type of source (e.g., "book", "journal_article", "database", "ontology")

    Returns:
        A query fragment with columns:
        - synonym: The botanical term
        - source_id: Source identifier
        - source_name: Name of the source
        - author: Author if available
        - year: Publication year if available
        - source_type: Type of source
    """
    return rai.where(
        arq.TraitSynonym.source(arq.SynonymSource),
        arq.SynonymSource.source_type(arq.SourceType),
        arq.SourceType == source_type,
        arq.SynonymSource.name(arq.SourceName),
    ).select(
        arq.TraitSynonym.alias("synonym"),
        arq.SynonymSource.id.alias("source_id"),
        arq.SourceName.alias("source_name"),
        author := rai.coalesce(arq.SynonymSource.author, "").alias("author"),
        year := rai.coalesce(arq.SynonymSource.year, 0).alias("year"),
        arq.SourceType.alias("source_type"),
    )


def synonym_with_sources(arq: ARQModel, synonym: str = "actinomorphic") -> rai.Fragment:
    """Get all sources that document a specific botanical term.

    Args:
        synonym: The botanical term to look up (default: "actinomorphic")

    Returns:
        A query fragment with columns:
        - synonym: The botanical term
        - source_name: Name of the source
        - source_type: Type of source (book, journal, etc.)
        - author: Author if available
        - year: Publication year if available
    """
    return rai.where(
        arq.TraitSynonym == synonym,
        arq.TraitSynonym.source(arq.SynonymSource),
        arq.SynonymSource.name(arq.SourceName),
        arq.SynonymSource.source_type(arq.SourceType),
    ).select(
        arq.TraitSynonym.alias("synonym"),
        arq.SourceName.alias("source_name"),
        arq.SourceType.alias("source_type"),
        author := rai.coalesce(arq.SynonymSource.author, "").alias("author"),
        year := rai.coalesce(arq.SynonymSource.year, 0).alias("year"),
    )


def synonyms_with_definitions_from_books(arq: ARQModel) -> rai.Fragment:
    """Get synonyms with their definitions from book sources.

    Returns:
        A query fragment with columns:
        - synonym: The botanical term
        - category: The trait category this definition belongs to
        - definition: Technical definition
        - common_definition: Plain language definition if available
        - source_name: Name of the book
        - author: Book author
        - year: Publication year
        - page: Page number if available
    """
    return rai.where(
        arq.TraitSynonym.definition_source(arq.SynonymSource),
        arq.SynonymSource.source_type(arq.SourceType),
        arq.SourceType == "book",
        arq.SynonymSource.name(arq.SourceName),
        arq.TraitSynonym.category(arq.SynonymCategory),
        arq.TraitSynonym.definition(arq.SynonymDefinition),
    ).select(
        arq.TraitSynonym.alias("synonym"),
        arq.SynonymCategory.alias("category"),
        arq.SynonymDefinition.alias("definition"),
        common_def := rai.coalesce(arq.TraitSynonym.common_definition, "").alias("common_definition"),
        arq.SourceName.alias("source_name"),
        author := rai.coalesce(arq.SynonymSource.author, "").alias("author"),
        year := rai.coalesce(arq.SynonymSource.year, 0).alias("year"),
        page := rai.coalesce(arq.TraitSynonym.definition_page, 0).alias("page"),
    )


def source_statistics(arq: ARQModel) -> rai.Fragment:
    """Get statistics on how many terms each source type contributes.

    Returns:
        A query fragment with columns:
        - source_type: Type of source
        - unique_synonyms: Number of unique terms from this source type
        - total_sources: Number of sources of this type
    """
    return rai.where(
        arq.SynonymSource.source_type(arq.SourceType),
        unique_synonyms := rai.count(rai.distinct(arq.TraitSynonym, arq.SourceType)).per(arq.SourceType),
        total_sources := rai.count(rai.distinct(arq.SynonymSource, arq.SourceType)).per(arq.SourceType),
        arq.TraitSynonym.source(arq.SynonymSource),
    ).select(
        arq.SourceType.alias("source_type"),
        unique_synonyms.alias("unique_synonyms"),
        total_sources.alias("total_sources"),
    )


def _get_query_functions() -> Dict[str, Callable]:
    """Get all query functions defined in this module.

    Returns a dictionary mapping function names to function objects.
    Only includes functions that take ARQModel as first parameter and
    return rai.Fragment.
    """
    current_module = sys.modules[__name__]
    query_functions = {}

    for name, obj in inspect.getmembers(current_module, inspect.isfunction):
        if name.startswith('_'):
            continue

        sig = inspect.signature(obj)
        params = list(sig.parameters.values())

        # Check if first parameter is ARQModel and return type is rai.Fragment
        if (params and
            params[0].annotation == ARQModel and
            sig.return_annotation == rai.Fragment):
            query_functions[name] = obj

    return query_functions


def main():
    """Main entry point for running queries from the command line.

    Usage:
        python -m kg.apps.trait_examples <query_name> [--param value ...]

    Example:
        python -m kg.apps.trait_examples all_traits
        python -m kg.apps.trait_examples trait_synonyms --trait-id growth_form
    """
    parser = argparse.ArgumentParser(
        description="Run trait example queries",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Get available query functions
    query_functions = _get_query_functions()

    if not query_functions:
        print("Error: No query functions found in this module", file=sys.stderr)
        sys.exit(1)

    parser.add_argument(
        'query_name',
        choices=list(query_functions.keys()),
        help=f"Name of the query to run. Available queries: {', '.join(query_functions.keys())}"
    )

    parser.add_argument(
        '--model-name',
        default='arq_trait',
        help='Name for the RAI model (default: arq_trait)'
    )

    # Parse known args first to get the query name
    args, remaining = parser.parse_known_args()

    # Get the selected query function
    query_func = query_functions[args.query_name]

    # Get the function signature to add appropriate parameters
    sig = inspect.signature(query_func)
    params = list(sig.parameters.values())[1:]  # Skip the first parameter (arq)

    # Add arguments for function parameters
    for param in params:
        param_name = f'--{param.name.replace("_", "-")}'
        param_type = param.annotation if param.annotation != inspect.Parameter.empty else str
        param_default = param.default if param.default != inspect.Parameter.empty else None

        parser.add_argument(
            param_name,
            type=param_type,
            default=param_default,
            help=f"Parameter {param.name} (type: {param_type.__name__})"
        )

    # Parse all arguments
    args = parser.parse_args()

    # Instantiate the model (trait-only)
    print(f"Initializing trait model: {args.model_name}")
    arq = define_trait_model(rai.Model(args.model_name))

    # Build kwargs for the query function
    kwargs = {}
    for param in params:
        value = getattr(args, param.name)
        if value is not None:
            kwargs[param.name] = value

    # Run the query
    print(f"Running query: {args.query_name}")
    if kwargs:
        print(f"Parameters: {kwargs}")

    result = query_func(arq, **kwargs)

    # Execute and display results
    df = result.to_df()
    print(f"\nResults ({len(df)} rows):")
    print(df)


if __name__ == '__main__':
    main()
