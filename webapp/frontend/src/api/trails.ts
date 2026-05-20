import { fetchJson, postJson } from "./client";

export interface TrailMeta {
  osm_id: string;
  name: string;
  highway: string;
  surface: string;
}

export interface TrailObservation {
  inat_id: string;
  latitude: number;
  longitude: number;
  date: string;
  image_url: string;
  species: string;
}

export function fetchTrails(): Promise<{ data: TrailMeta[] }> {
  return fetchJson("/trails");
}

export function fetchAllTrailCells(): Promise<{ data: string[]; total: number }> {
  return fetchJson("/trails/cells");
}

export function fetchAllTrailEcosites(): Promise<{ data: string[]; total: number }> {
  return fetchJson("/trails/ecosites");
}

export function fetchTrailEcosites(osmId: string): Promise<{ data: string[]; total: number }> {
  return fetchJson(`/trails/${encodeURIComponent(osmId)}/ecosites`);
}

export interface EcositeCell {
  ecosite_id: string;
  h3_index: string;
}

export function fetchAllTrailEcositeCells(): Promise<{ data: EcositeCell[]; total: number }> {
  return fetchJson("/trails/ecosite-cells");
}

export function fetchTrailEcositeCells(osmId: string): Promise<{ data: EcositeCell[]; total: number }> {
  return fetchJson(`/trails/${encodeURIComponent(osmId)}/ecosite-cells`);
}

export function fetchAllTrailObservations(): Promise<{ data: TrailObservation[]; total: number }> {
  return fetchJson("/trails/observations");
}

export function fetchTrailCells(osmId: string): Promise<{ data: string[]; total: number }> {
  return fetchJson(`/trails/${encodeURIComponent(osmId)}/cells`);
}

export function fetchTrailObservations(osmId: string): Promise<{ data: TrailObservation[]; total: number }> {
  return fetchJson(`/trails/${encodeURIComponent(osmId)}/observations`);
}

export function fetchTrailSpecies(osmId: string): Promise<{ data: string[]; total: number }> {
  return fetchJson(`/trails/${encodeURIComponent(osmId)}/species`);
}

export type FeatureValues = Record<string, { value: string; species_count: number }[]>;

export function fetchTrailFeatures(osmId: string): Promise<{ data: FeatureValues }> {
  return fetchJson(`/trails/${encodeURIComponent(osmId)}/features`);
}

export type FilterItem = { feature: string; value: string };

export function filterTrailSpecies(osmId: string, filters: FilterItem[]): Promise<{ data: string[]; total: number }> {
  return postJson(`/trails/${encodeURIComponent(osmId)}/species/filter`, filters);
}
