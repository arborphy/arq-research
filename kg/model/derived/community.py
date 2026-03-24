"""Derived rule: Species communities via WCC on the co-occurrence graph.

Uses RAI's graph library to compute weakly connected components
on the species co-occurrence graph. Each component is a community.
"""
from relationalai.semantics import define
from relationalai.semantics.reasoners.graph import Graph

from kg.model import m
from kg.model.core.taxonomy import Species

# Build an undirected, unweighted graph where nodes are Species
# and edges are co-occurrence relationships
graph = Graph(m, directed=False, weighted=False, node_concept=Species)
Edge = graph.Edge

# Populate edges from Species.co_occurs_with
define(Edge.new(src=Species, dst=Species.co_occurs_with))

# Compute WCC
wcc = graph.weakly_connected_component()

# Store the community assignment as a relationship on Species
Species.community = m.Relationship(f"{Species} belongs to community {Species:community}")

s = Species.ref()
community = Species.ref()

define(Species.community(s, community)).where(
    wcc(s, community),
)
