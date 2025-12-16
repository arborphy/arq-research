import relationalai.semantics as rai


_RANKS_ORDERED = [
    ("Species", None),
    ("Genus", "genus"),
    ("Family", "family"),
    ("Order", "order"),
    ("Class", "class_"),
    ("Phylum", "phylum"),
    ("Kingdom", "kingdom"),
]


def define_taxonomy_strict(m: rai.Model):
    """Define rank properties using a strict rank-by-rank parent chain.

    This matches the SQL in the kata docs (Species->Genus->Family->...).
    It is intentionally strict: if the source taxonomy skips a rank
    (e.g., species parent is a family), then the skipped rank will not be
    inferred.
    """

    # Create Taxon properties for each rank above species
    for concept_name, prop_name in _RANKS_ORDERED:
        if prop_name is None:
            continue
        target_concept = getattr(m, concept_name)
        setattr(m.Taxon, prop_name, m.Property(f"{{Taxon}} comprises {{{concept_name}}}"))

    # For each (source_rank <= target_rank), define Taxon.<target_prop>
    # by requiring an exact chain of parent relationships through each
    # intermediate rank.
    for target_idx, (target_concept_name, target_prop) in enumerate(_RANKS_ORDERED):
        if target_prop is None:
            continue

        target_concept = getattr(m, target_concept_name)
        target_ref = target_concept.ref()

        # Reflexive case for the target rank itself.
        rai.define(getattr(target_ref, target_prop)(target_ref))

        for source_idx in range(0, target_idx):
            source_concept = getattr(m, _RANKS_ORDERED[source_idx][0])
            source_ref = source_concept.ref()

            # Build refs for intermediate ranks and compose parent-chain constraints.
            chain_refs = [getattr(m, _RANKS_ORDERED[i][0]).ref() for i in range(source_idx + 1, target_idx)]
            where_clauses = []

            if not chain_refs:
                # Direct parent to target
                where_clauses.append(source_ref.parent(target_ref))
            else:
                where_clauses.append(source_ref.parent(chain_refs[0]))
                for i in range(len(chain_refs) - 1):
                    where_clauses.append(chain_refs[i].parent(chain_refs[i + 1]))
                where_clauses.append(chain_refs[-1].parent(target_ref))

            rai.define(getattr(source_ref, target_prop)(target_ref)).where(*where_clauses)


def define_taxonomy_ancestor(m: rai.Model, *, max_hops: int = 8):
    """Define an ancestor graph edge and rank properties via ancestry.

    This is less strict and more "graphy": for any taxon `t` and rank concept
    `R`, `t.<rank_prop>(r)` holds if `r` is an ancestor of `t` and `r` is an
    instance of `R`.

    Because `relationalai.semantics` does not evaluate recursive rules here,
    we unroll a bounded transitive closure over `parent`.
    """

    t = m.Taxon.ref()

    m.Taxon.ancestor = m.Relationship("{Taxon} has ancestor {Taxon}")

    # Reflexive base
    rai.define(t.ancestor(t))

    # Unrolled transitive closure
    for distance in range(1, max_hops + 1):
        a = m.Taxon.ref()
        if distance == 1:
            rai.define(t.ancestor(a)).where(t.parent(a))
            continue

        intermediates = [m.Taxon.ref() for _ in range(distance - 1)]
        where_clauses = [t.parent(intermediates[0])]
        for i in range(len(intermediates) - 1):
            where_clauses.append(intermediates[i].parent(intermediates[i + 1]))
        where_clauses.append(intermediates[-1].parent(a))
        rai.define(t.ancestor(a)).where(*where_clauses)

    # Rank properties derived from ancestry
    for concept_name, prop_name in _RANKS_ORDERED:
        if prop_name is None:
            continue
        target_ref = getattr(m, concept_name).ref()
        setattr(m.Taxon, prop_name, m.Property(f"{{Taxon}} has {concept_name} ancestor {{{concept_name}}}"))
        rai.define(getattr(t, prop_name)(target_ref)).where(t.ancestor(target_ref))


def define_taxonomy(m: rai.Model):
    """Backward-compatible entrypoint.

    Defaults to strict rank-by-rank derivation.
    """
    define_taxonomy_strict(m)


def define_taxonomy_graphical(m: rai.Model):
    """Backward-compatible entrypoint for the ancestry-based approach."""
    define_taxonomy_ancestor(m)