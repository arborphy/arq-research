import relationalai.semantics as rai
from relationalai.semantics.snowflake import Table


def define_taxonomy(m: rai.Model):
    """
    This module defines the hierarchical relationships derived from
    parent-child relationships in the source data.
    """

    # Define hierarchical relationships
    # References for each taxonomic rank
    s = m.Species.ref()
    g = m.Genus.ref()
    f = m.Family.ref()
    o = m.Order.ref()
    c = m.Class.ref()
    p = m.Phylum.ref()
    k = m.Kingdom.ref()

    # Genus relationships
    m.Taxon.genus = m.Property("{Taxon} comprises {Genus}")
    rai.define(
        s.genus(g)
    ).where(
        s.parent(g)
    )
    rai.define(g.genus(g))


    # Family relationships
    m.Taxon.family = m.Property("{Taxon} comprises {Family}")
    rai.define(
        s.family(f)
    ).where(
        s.parent(g),
        g.parent(f)
    )
    rai.define(
        g.family(f)
    ).where(
        g.parent(f),
    )
    rai.define(f.family(f))

    # Order relationships
    m.Taxon.order = m.Property("{Taxon} comprises {Order}")
    rai.define(
        s.order(o)
    ).where(
        s.parent(g),
        g.parent(f),
        f.parent(o)
    )
    rai.define(
        g.order(o)
    ).where(
        g.parent(f),
        f.parent(o)
    )
    rai.define(
        f.order(o)
    ).where(
        f.parent(o),
    )
    rai.define(o.order(o))

    # Class relationships
    m.Taxon.class_ = m.Property("{Taxon} comprises {Class}")
    rai.define(
        s.class_(c)
    ).where(
        s.parent(g),
        g.parent(f),
        f.parent(o),
        o.parent(c)
    )
    rai.define(
        g.class_(c)
    ).where(
        g.parent(f),
        f.parent(o),
        o.parent(c)
    )
    rai.define(
        f.class_(c)
    ).where(
        f.parent(o),
        o.parent(c)
    )
    rai.define(
        o.class_(c)
    ).where(
        o.parent(c),
    )
    rai.define(c.class_(c))

    # Phylum relationships
    m.Taxon.phylum = m.Property("{Taxon} comprises {Phylum}")
    rai.define(
        s.phylum(p)
    ).where(
        s.parent(g),
        g.parent(f),
        f.parent(o),
        o.parent(c),
        c.parent(p)
    )
    rai.define(
        g.phylum(p)
    ).where(
        g.parent(f),
        f.parent(o),
        o.parent(c),
        c.parent(p)
    )
    rai.define(
        f.phylum(p)
    ).where(
        f.parent(o),
        o.parent(c),
        c.parent(p)
    )
    rai.define(
        o.phylum(p)
    ).where(
        o.parent(c),
        c.parent(p)
    )
    rai.define(
        c.phylum(p)
    ).where(
        c.parent(p),
    )
    rai.define(p.phylum(p))

    # Kingdom relationships
    m.Taxon.kingdom = m.Property("{Taxon} comprises {Kingdom}")
    rai.define(
        s.kingdom(k)
    ).where(
        s.parent(g),
        g.parent(f),
        f.parent(o),
        o.parent(c),
        c.parent(p),
        p.parent(k)
    )
    rai.define(
        g.kingdom(k)
    ).where(
        g.parent(f),
        f.parent(o),
        o.parent(c),
        c.parent(p),
        p.parent(k)
    )
    rai.define(
        f.kingdom(k)
    ).where(
        f.parent(o),
        o.parent(c),
        c.parent(p),
        p.parent(k)
    )
    rai.define(
        o.kingdom(k)
    ).where(
        o.parent(c),
        c.parent(p),
        p.parent(k)
    )
    rai.define(
        c.kingdom(k)
    ).where(
        c.parent(p),
        p.parent(k)
    )
    rai.define(
        p.kingdom(k)
    ).where(
        p.parent(k),
    )
    rai.define(k.kingdom(k))
