export interface SpeciesCoOccurrenceCount {
  co_occurring_count: number;
  species: string;
}

export interface SpeciesCoOccurrence {
  co_occurring_species: string;
}

export interface ObservationPoint {
  lat: number;
  lon: number;
  date: string;
  inat_id: string;
  image_url: string;
}

export interface CoOccurringObservation {
  lat: number;
  lon: number;
  date: string;
  inat_id: string;
  species_name: string;
}

export interface SharedFeature {
  feature: string;
  value: string;
  species_count: number;
}

export interface H3CellInfo {
  h3_index: string;
  co_occurrence_count: number;
}

export interface FeatureValueCount {
  value: string;
  species_count: number;
}

export interface DebugQuery {
  id: string;
  timestamp: string;
  source: string;
  dsl: string;
  file: string;
  line: number;
}

export interface VisibleSpecies {
  species: string;
  image_url: string;
  inat_id: string;
  date: string;
}

export interface NewcombKeyInfo {
  group_number: string;
  flower_type: string;
  plant_type: string;
  leaf_type: string;
}

export interface ApiResponse<T> {
  data: T[];
  total: number;
}

export interface PredicateSummary {
  concept_type: string;
  predicate: string;
  count: number;
}

export interface PredicatePair {
  child: string;
  parent: string;
  concept_type: string;
}

export interface PredicateGraphNode {
  id: string;
  label: string;
  concept_type: string;
}

export interface PredicateGraphEdge {
  source: string;
  target: string;
  type?: string;
}
