import { fetchJson } from "./client";

export async function getFamilies(): Promise<{ data: string[] }> {
  return fetchJson("/taxonomy-predicates/families");
}

export async function getFamilySpecies(
  familyName: string,
  predicate: "within_clade" | "part_of",
): Promise<{ data: string[]; total: number }> {
  return fetchJson(
    `/taxonomy-predicates/family/${encodeURIComponent(familyName)}/species?predicate=${predicate}`,
  );
}

export async function getFamilyGenera(
  familyName: string,
): Promise<{ data: { genus: string; species_count: number }[]; total: number }> {
  return fetchJson(`/taxonomy-predicates/family/${encodeURIComponent(familyName)}/genera`);
}

export async function getFamilyGraph(
  familyName: string,
): Promise<{ family: string; data: { genus: string; species: string }[] }> {
  return fetchJson(`/taxonomy-predicates/family/${encodeURIComponent(familyName)}/graph`);
}
