import { fetchJson } from "./client";
import type { ApiResponse, SpeciesCoOccurrenceCount, SpeciesCoOccurrence, ObservationPoint, CoOccurringObservation, SharedFeature, FeatureValueCount, H3CellInfo, DebugQuery } from "../types";

export function getTopSpecies(limit = 50) {
  return fetchJson<ApiResponse<SpeciesCoOccurrenceCount>>(
    `/co-occurrence/top?limit=${limit}`
  );
}

export function getSpeciesList() {
  return fetchJson<{ data: string[] }>("/co-occurrence/species-list");
}

export function getForSpecies(name: string, granularity: string = "day") {
  return fetchJson<ApiResponse<SpeciesCoOccurrence>>(
    `/co-occurrence/species/${encodeURIComponent(name)}?granularity=${granularity}`
  );
}

export function getSpeciesObservations(name: string) {
  return fetchJson<ApiResponse<ObservationPoint>>(
    `/geo/species/${encodeURIComponent(name)}/observations`
  );
}

export function getSpeciesCoOccurrenceCells(name: string) {
  return fetchJson<ApiResponse<H3CellInfo>>(
    `/geo/species/${encodeURIComponent(name)}/co-occurrence-cells`
  );
}

export function getSharedFeatures(name: string) {
  return fetchJson<ApiResponse<SharedFeature>>(
    `/co-occurrence/species/${encodeURIComponent(name)}/shared-features`
  );
}

export function getCoOccurringObservations(name: string) {
  return fetchJson<ApiResponse<CoOccurringObservation>>(
    `/geo/species/${encodeURIComponent(name)}/co-occurring-observations`
  );
}

export function getFeatures() {
  return fetchJson<{ data: Record<string, FeatureValueCount[]> }>("/features/");
}

export function getSpeciesByFeature(feature: string, value: string) {
  return fetchJson<ApiResponse<{ species: string }>>(
    `/features/species?feature=${encodeURIComponent(feature)}&value=${encodeURIComponent(value)}`
  );
}

export function getCoOccurrenceGraph() {
  return fetchJson<{
    nodes: string[];
    edges: { source: string; target: string }[];
    communities: Record<string, string>;
  }>("/co-occurrence/graph");
}

export function getNewcombKey(name: string) {
  return fetchJson<{ data: import("../types").NewcombKeyInfo | null }>(
    `/features/newcomb-key/${encodeURIComponent(name)}`
  );
}

export function getCells(dayOfYear?: number) {
  const qs = dayOfYear != null ? `?day_of_year=${dayOfYear}` : "";
  return fetchJson<{ data: { h3_index: string; observation_count: number }[] }>(`/geo/cells${qs}`);
}

export function getVisibleSpecies(h3Index: string, dayOfYear: number) {
  return fetchJson<ApiResponse<import("../types").VisibleSpecies>>(
    `/geo/visible?h3_index=${encodeURIComponent(h3Index)}&day_of_year=${dayOfYear}`
  );
}

export function getDebugQueries(limit = 20) {
  return fetchJson<{ data: DebugQuery[] }>(`/debug/queries?limit=${limit}`);
}
