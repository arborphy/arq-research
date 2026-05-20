import { fetchJson } from "./client";

export const LOCATION_LEVELS = ["Park", "City", "State", "Country"] as const;
export type LocationLevel = typeof LOCATION_LEVELS[number];
export const CONTAINER_LEVELS = ["EcoSite", ...LOCATION_LEVELS] as const;
export type ContainerLevel = typeof CONTAINER_LEVELS[number];
export type SubjectLevel = "Observation" | LocationLevel;

export interface PlaceLevel {
  level: LocationLevel;
  name: string;
  within: number;
  direct: number;
}

export interface WithinPair {
  subject: string;
  container: string;
  count?: number;
}

export async function getPlaceHierarchy(): Promise<{ data: PlaceLevel[] }> {
  return fetchJson("/spatial/places");
}

export async function getWithinPairs(
  subject: SubjectLevel,
  container: ContainerLevel,
): Promise<{ data: WithinPair[]; subject: string; container: string }> {
  return fetchJson(`/spatial/within?subject=${subject}&container=${container}`);
}
