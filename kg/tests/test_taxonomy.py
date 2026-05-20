"""Tests for taxonomy hierarchy use cases.

Verifies the Blue Aster (Symphyotrichum laeve) taxonomy DAG from
docs/DataModel Sketch.md using RAI queries.
"""

from relationalai.semantics import define, select, where

from kg.model.core.taxonomy import (
    Domain, Kingdom, Phylum, Class, Order, Family, Genus, Species, Subspecies, TaxonVariety,
)
from kg.model.core.predicates import has_part


class TestTaxonomyHierarchy:
    """Verify the full taxonomy DAG for Blue Aster."""

    def test_domain_exists(self, blue_aster_hierarchy):
        """Query that the Eukarya domain was created."""
        df = where(Domain.name == "Eukarya").select(Domain.name).to_df()
        assert len(df) == 1
        assert df.iloc[0]["name"] == "Eukarya"

    def test_species_exists(self, blue_aster_hierarchy):
        """Query that Symphyotrichum laeve species was created."""
        df = where(Species.name == "Symphyotrichum laeve").select(
            Species.name, Species.inat_link
        ).to_df()
        assert len(df) == 1
        assert df.iloc[0]["name"] == "Symphyotrichum laeve"
        assert "inaturalist.org" in df.iloc[0]["inat_link"]

    def test_domain_to_kingdom_link(self, blue_aster_hierarchy):
        """Verify Eukarya -> Plantae relationship."""
        child = Domain.has_part
        df = where(
            Domain.name == "Eukarya",
        ).select(
            Domain.name.alias("domain"), child.name.alias("kingdom")
        ).to_df()
        assert len(df) == 1
        assert df.iloc[0]["kingdom"] == "Plantae"

    def test_genus_to_species_link(self, blue_aster_hierarchy):
        """Verify Symphyotrichum -> Symphyotrichum laeve relationship."""
        child = Genus.has_part
        df = where(
            Genus.name == "Symphyotrichum",
        ).select(
            Genus.name.alias("genus"), child.name.alias("species")
        ).to_df()
        assert len(df) == 1
        assert df.iloc[0]["species"] == "Symphyotrichum laeve"

    def test_full_hierarchy_chain(self, blue_aster_hierarchy):
        """Traverse the full hierarchy from Domain to Species."""
        kingdoms = Domain.has_part
        phyla = kingdoms.has_part
        classes = phyla.has_part
        orders = classes.has_part
        families = orders.has_part
        genera = families.has_part
        spp = genera.has_part

        df = where(
            Domain.name == "Eukarya",
        ).select(
            Domain.name.alias("domain"),
            kingdoms.name.alias("kingdom"),
            phyla.name.alias("phylum"),
            classes.name.alias("class"),
            orders.name.alias("order"),
            families.name.alias("family"),
            genera.name.alias("genus"),
            spp.name.alias("species"),
        ).to_df()

        assert len(df) == 1
        row = df.iloc[0]
        assert row["domain"] == "Eukarya"
        assert row["kingdom"] == "Plantae"
        assert row["phylum"] == "Tracheophyta"
        assert row["class"] == "Magnoliopsida"
        assert row["order"] == "Asterales"
        assert row["family"] == "Asteraceae"
        assert row["genus"] == "Symphyotrichum"
        assert row["species"] == "Symphyotrichum laeve"

    def test_all_kingdoms_under_eukarya(self, blue_aster_hierarchy):
        """Query all kingdoms under the Eukarya domain."""
        child = Domain.has_part
        df = where(
            Domain.name == "Eukarya",
        ).select(child.name).to_df()
        assert len(df) >= 1
        names = df["name"].tolist()
        assert "Plantae" in names


class TestSubspecies:
    """Verify subspecies can be added below species."""

    def test_subspecies_link(self, blue_aster_hierarchy):
        """Add and query a subspecies under Symphyotrichum laeve."""
        define(
            var_laeve := Subspecies.new(name="Symphyotrichum laeve var. laeve"),
            has_part(blue_aster_hierarchy["species"], var_laeve),
        )

        s = Species.ref()
        child = Subspecies.ref()
        df = where(
            s.name == "Symphyotrichum laeve",
            has_part(s, child),
        ).select(child.name).to_df()
        assert len(df) >= 1
        names = df["name"].tolist()
        assert "Symphyotrichum laeve var. laeve" in names


class TestSpeciesObservationProperties:
    """Verify new Species properties added from iNaturalist observation data."""

    def test_species_common_name(self, blue_aster_hierarchy):
        """Species should have a common name."""
        df = where(Species.name == "Symphyotrichum laeve").select(
            Species.common_name
        ).to_df()
        assert len(df) == 1
        assert df.iloc[0]["common_name"] == "smooth blue aster"

    def test_species_inat_taxon_id(self, blue_aster_hierarchy):
        """Species should have an iNaturalist taxon id."""
        df = where(Species.name == "Symphyotrichum laeve").select(
            Species.inat_taxon_id
        ).to_df()
        assert len(df) == 1
        assert df.iloc[0]["inat_taxon_id"] == "129607"

    def test_species_iconic_taxon(self, blue_aster_hierarchy):
        """Species should have an iconic taxon label."""
        df = where(Species.name == "Symphyotrichum laeve").select(
            Species.iconic_taxon
        ).to_df()
        assert len(df) == 1
        assert df.iloc[0]["iconic_taxon"] == "Plantae"


class TestTaxonVariety:
    """Verify TaxonVariety can be created and linked to a Subspecies."""

    def test_variety_exists(self, taxon_variety_fixture):
        """TaxonVariety should be queryable by name."""
        df = where(TaxonVariety.name == "smooth").select(TaxonVariety.name).to_df()
        assert len(df) == 1
        assert df.iloc[0]["name"] == "smooth"

    def test_variety_linked_to_subspecies(self, taxon_variety_fixture):
        """Subspecies should contain the variety via varieties relationship."""
        child = Subspecies.has_part
        df = where(
            Subspecies.name == "Symphyotrichum laeve var. laeve",
        ).select(child.name.alias("variety_name")).to_df()
        assert len(df) >= 1
        assert "smooth" in df["variety_name"].tolist()

    def test_variety_reachable_from_species(self, taxon_variety_fixture):
        """Traverse Species -> Subspecies -> TaxonVariety."""
        subsp = Species.has_part
        variety = subsp.has_part
        df = where(
            Species.name == "Symphyotrichum laeve",
        ).select(variety.name.alias("variety_name")).to_df()
        assert len(df) >= 1
        assert "smooth" in df["variety_name"].tolist()
