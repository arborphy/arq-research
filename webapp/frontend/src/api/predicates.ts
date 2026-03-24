import { fetchJson } from "./client";
import type {
  PredicateSummary,
  PredicatePair,
  PredicateGraphNode,
  PredicateGraphEdge,
} from "../types";

export async function getPredicateSummary(): Promise<{ data: PredicateSummary[] }> {
  return fetchJson("/predicates/summary");
}

export async function getPredicatePairs(
  conceptType: string = "all",
  limit: number = 50,
): Promise<{ data: PredicatePair[]; total: number }> {
  return fetchJson(`/predicates/pairs?concept_type=${conceptType}&limit=${limit}`);
}

export async function getPredicateGraph(): Promise<{
  nodes: PredicateGraphNode[];
  edges: PredicateGraphEdge[];
}> {
  return fetchJson("/predicates/graph");
}
