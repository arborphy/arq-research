import relationalai.semantics as rai
from relationalai.semantics.snowflake import Table


def define_taxonomy(m: rai.Model):
    """
    This module defines the hierarchical relationships derived from
    parent-child relationships in the source data.
    """

    # Define hierarchical relationships in the GBIF taxonomy backbone.
    #
    # NOTE: these are *taxonomy-rank views* over Taxon.
    # The unified, user-facing Species abstraction is `m.Species` (name-based)
    # and is mapped to the taxonomy backbone in `kg.model.derived.species`.
    ts = m.TaxonSpecies.ref()
    tg = m.TaxonGenus.ref()
    tf = m.TaxonFamily.ref()
    to = m.TaxonOrder.ref()
    tc = m.TaxonClass.ref()
    tp = m.TaxonPhylum.ref()
    tk = m.TaxonKingdom.ref()

    # Genus relationships
    m.Taxon.genus = m.Property("{Taxon} comprises {TaxonGenus}")
    rai.define(ts.genus(tg)).where(ts.parent(tg))
    rai.define(tg.genus(tg))


    # Family relationships
    m.Taxon.family = m.Property("{Taxon} comprises {TaxonFamily}")
    rai.define(ts.family(tf)).where(
        ts.parent(tg),
        tg.parent(tf),
    )
    rai.define(tg.family(tf)).where(tg.parent(tf))
    rai.define(tf.family(tf))

    # Order relationships
    m.Taxon.order = m.Property("{Taxon} comprises {TaxonOrder}")
    rai.define(ts.order(to)).where(
        ts.parent(tg),
        tg.parent(tf),
        tf.parent(to),
    )
    rai.define(tg.order(to)).where(
        tg.parent(tf),
        tf.parent(to),
    )
    rai.define(tf.order(to)).where(tf.parent(to))
    rai.define(to.order(to))

    # Class relationships
    m.Taxon.class_ = m.Property("{Taxon} comprises {TaxonClass}")
    rai.define(ts.class_(tc)).where(
        ts.parent(tg),
        tg.parent(tf),
        tf.parent(to),
        to.parent(tc),
    )
    rai.define(tg.class_(tc)).where(
        tg.parent(tf),
        tf.parent(to),
        to.parent(tc),
    )
    rai.define(tf.class_(tc)).where(
        tf.parent(to),
        to.parent(tc),
    )
    rai.define(to.class_(tc)).where(to.parent(tc))
    rai.define(tc.class_(tc))

    # Phylum relationships
    m.Taxon.phylum = m.Property("{Taxon} comprises {TaxonPhylum}")
    rai.define(ts.phylum(tp)).where(
        ts.parent(tg),
        tg.parent(tf),
        tf.parent(to),
        to.parent(tc),
        tc.parent(tp),
    )
    rai.define(tg.phylum(tp)).where(
        tg.parent(tf),
        tf.parent(to),
        to.parent(tc),
        tc.parent(tp),
    )
    rai.define(tf.phylum(tp)).where(
        tf.parent(to),
        to.parent(tc),
        tc.parent(tp),
    )
    rai.define(to.phylum(tp)).where(
        to.parent(tc),
        tc.parent(tp),
    )
    rai.define(tc.phylum(tp)).where(tc.parent(tp))
    rai.define(tp.phylum(tp))

    # Kingdom relationships
    m.Taxon.kingdom = m.Property("{Taxon} comprises {TaxonKingdom}")
    rai.define(ts.kingdom(tk)).where(
        ts.parent(tg),
        tg.parent(tf),
        tf.parent(to),
        to.parent(tc),
        tc.parent(tp),
        tp.parent(tk),
    )
    rai.define(tg.kingdom(tk)).where(
        tg.parent(tf),
        tf.parent(to),
        to.parent(tc),
        tc.parent(tp),
        tp.parent(tk),
    )
    rai.define(tf.kingdom(tk)).where(
        tf.parent(to),
        to.parent(tc),
        tc.parent(tp),
        tp.parent(tk),
    )
    rai.define(to.kingdom(tk)).where(
        to.parent(tc),
        tc.parent(tp),
        tp.parent(tk),
    )
    rai.define(tc.kingdom(tk)).where(
        tc.parent(tp),
        tp.parent(tk),
    )
    rai.define(tp.kingdom(tk)).where(tp.parent(tk))
    rai.define(tk.kingdom(tk))

    # ---- Unified Species hierarchy edges ----
    # Define Species -> Taxon* edges via Species.taxon (defined in derived/species).
    sp = m.Species.ref()
    tx = m.TaxonSpecies.ref()

    m.Species.genus = m.Relationship("{Species} has genus {TaxonGenus}")
    rai.define(sp.genus(tg)).where(sp.taxon(tx), tx.genus(tg))

    m.Species.family = m.Relationship("{Species} has family {TaxonFamily}")
    rai.define(sp.family(tf)).where(sp.taxon(tx), tx.family(tf))

    m.Species.order = m.Relationship("{Species} has order {TaxonOrder}")
    rai.define(sp.order(to)).where(sp.taxon(tx), tx.order(to))

    m.Species.class_ = m.Relationship("{Species} has class {TaxonClass}")
    rai.define(sp.class_(tc)).where(sp.taxon(tx), tx.class_(tc))

    m.Species.phylum = m.Relationship("{Species} has phylum {TaxonPhylum}")
    rai.define(sp.phylum(tp)).where(sp.taxon(tx), tx.phylum(tp))

    m.Species.kingdom = m.Relationship("{Species} has kingdom {TaxonKingdom}")
    rai.define(sp.kingdom(tk)).where(sp.taxon(tx), tx.kingdom(tk))
