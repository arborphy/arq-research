import { fetchJson } from "./client";

export function fetchEcosites(): Promise<{ data: string[] }> {
  return fetchJson("/ecosites");
}

export function fetchEcositeCells(ecositeId: string): Promise<{ data: string[]; total: number }> {
  return fetchJson(`/ecosites/${encodeURIComponent(ecositeId)}/cells`);
}

export function fetchEcositeCompactedCells(ecositeId: string): Promise<{ data: string[]; total: number }> {
  return fetchJson(`/ecosites/${encodeURIComponent(ecositeId)}/cells/compacted`);
}

export function fetchEcositesWithObservations(): Promise<{ data: string[]; total: number }> {
  return fetchJson("/ecosites/with-observations");
}

export function fetchEcositeSpecies(ecositeId: string): Promise<{ data: string[]; total: number }> {
  return fetchJson(`/ecosites/${encodeURIComponent(ecositeId)}/species`);
}
