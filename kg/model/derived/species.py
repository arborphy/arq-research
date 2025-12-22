import relationalai.semantics as rai


def define_species(m: rai.Model) -> None:
    """Define the single, shared Species abstraction.

    Design goal:
    - “Species” should mean the same thing everywhere.
    - Different sources (GBIF taxonomy, USDA plants) attach to that one concept.

    Implementation:
    - Species is identified by CanonicalName (string).
    - Taxon (rank==species) links to Species via canonical_name.
    - Plant links to Species via scientific_name (same CanonicalName concept).
    - Species.trait is derived via Species.plant -> Plant.trait.

    Taxonomy-rank views remain available as Taxon* concepts (TaxonSpecies,
    TaxonGenus, ...) but are not the primary user-facing species entity.
    """

    # Single name-based species concept
    m.Species = m.Concept("Species", identify_by={"name": m.CanonicalName})

    tx = m.Taxon.ref()
    sp = m.Species.ref()
    p = m.Plant.ref()
    t = m.Trait.ref()
    cn = m.CanonicalName.ref()

    # Materialize Species instances from both sources.
    # NOTE: use explicit value refs (cn) to avoid type mismatches.
    rai.define(m.Species.new(name=cn)).where(
        tx.rank == "species",
        tx.canonical_name(cn),
    )
    rai.define(m.Species.new(name=cn)).where(p.scientific_name(cn))

    # Taxon (species rank) -> Species
    m.Taxon.species = m.Relationship("{Taxon} corresponds to species {Species}")
    rai.define(tx.species(sp)).where(
        tx.rank == "species",
        tx.canonical_name(cn),
        sp.name(cn),
    )

    # Species -> TaxonSpecies (for navigation into the taxonomy backbone)
    # Note: link to the rank-view concept so downstream rules can type-match.
    m.Species.taxon = m.Relationship("{Species} has GBIF taxon species {TaxonSpecies}")
    txs = m.TaxonSpecies.ref()
    rai.define(sp.taxon(txs)).where(
        sp.name(cn),
        txs.canonical_name(cn),
    )

    # Plant -> Species
    m.Plant.species = m.Relationship("{Plant} corresponds to species {Species}")
    rai.define(p.species(sp)).where(
        p.scientific_name(cn),
        sp.name(cn),
    )

    # Species -> Plant
    m.Species.plant = m.Relationship("{Species} has plant record {Plant}")
    rai.define(sp.plant(p)).where(
        sp.name(cn),
        p.scientific_name(cn),
    )

    # Species -> Trait
    m.Species.trait = m.Relationship("{Species} has trait {Trait}")
    rai.define(sp.trait(t)).where(
        sp.plant(p),
        p.trait(t),
    )

    # Convenience: Observation -> Species
    # (Observation.classification is a Taxon ref)
    m.Observation.species = m.Relationship("{Observation} corresponds to species {Species}")
    rai.define(m.Observation.species(m.Observation.classification.species))
