import { useState, useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { getPredicateSummary, getPredicatePairs } from "../api/predicates";
import { LoadingState } from "../components/LoadingState";

const CONCEPT_COLORS: Record<string, string> = {
  "Species": "#2d6a4f",
  "Genus": "#606c38",
  "Family": "#283618",
  "Species → Genus": "#2d6a4f",
  "Genus → Family": "#606c38",
  "Feature": "#e76f51",
  "Category → Feature": "#e76f51",
  "ALL (Entity)": "#457b9d",
};

const DEFAULT_COLOR = "#888";

function colorFor(conceptType: string): string {
  return CONCEPT_COLORS[conceptType] ?? DEFAULT_COLOR;
}

export function PredicateExplorerPage() {
  const [filter, setFilter] = useState<"all" | "species" | "genus" | "feature">("all");

  const { data: summaryData, isLoading: summaryLoading } = useQuery({
    queryKey: ["predicate-summary"],
    queryFn: getPredicateSummary,
  });

  const { data: pairsData, isLoading: pairsLoading } = useQuery({
    queryKey: ["predicate-pairs", filter],
    queryFn: () => getPredicatePairs(filter, 50),
  });

  const summary = summaryData?.data ?? [];
  const pairs = pairsData?.data ?? [];

  const grouped = useMemo(() => {
    const map = new Map<string, typeof pairs>();
    for (const p of pairs) {
      const list = map.get(p.concept_type) ?? [];
      list.push(p);
      map.set(p.concept_type, list);
    }
    return map;
  }, [pairs]);

  if (summaryLoading) return <LoadingState message="Loading predicate data..." />;

  return (
    <div>
      <Link to="/">&larr; Home</Link>
      <h2>Global Predicate Explorer</h2>
      <p style={{ color: "#666", fontSize: "0.85rem", maxWidth: "700px" }}>
        Demonstrates how a single predicate defined on the base <code>Entity</code> concept
        works across multiple concept types with the same query.
      </p>

      {/* Summary cards */}
      <h3 style={{ marginBottom: "0.75rem" }}>part_of usage across concepts</h3>
      <div style={{ display: "flex", gap: "1rem", marginBottom: "2rem", flexWrap: "wrap" }}>
        {summary.map((s) => (
          <div
            key={s.concept_type}
            style={{
              border: `2px solid ${colorFor(s.concept_type)}`,
              borderRadius: "8px",
              padding: "1rem 1.5rem",
              minWidth: "160px",
              textAlign: "center",
            }}
          >
            <div style={{ fontSize: "2rem", fontWeight: "bold", color: colorFor(s.concept_type) }}>
              {s.count.toLocaleString()}
            </div>
            <div style={{ color: "#666", fontSize: "0.85rem", marginTop: "0.25rem" }}>{s.concept_type}</div>
          </div>
        ))}
      </div>

      {/* Filter + pairs table */}
      <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", marginBottom: "1rem" }}>
        <h3 style={{ margin: 0 }}>Pairs</h3>
        {(["all", "species", "genus", "feature"] as const).map((f) => {
          const labels: Record<string, string> = {
            all: "All",
            species: "Species → Genus",
            genus: "Genus → Family",
            feature: "Category → Feature",
          };
          return (
            <button
              key={f}
              onClick={() => setFilter(f)}
              style={{
                padding: "0.3rem 0.75rem",
                border: filter === f ? "2px solid #2d6a4f" : "1px solid #ccc",
                borderRadius: "4px",
                background: filter === f ? "#d8f3dc" : "white",
                cursor: "pointer",
                fontSize: "0.8rem",
              }}
            >
              {labels[f]}
            </button>
          );
        })}
      </div>

      {pairsLoading ? (
        <LoadingState message="Loading pairs..." />
      ) : (
        [...grouped.entries()].map(([conceptType, items]) => (
          <div key={conceptType} style={{ marginBottom: "1.5rem" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "0.5rem" }}>
              <span style={{
                width: "12px", height: "12px", borderRadius: "50%",
                background: colorFor(conceptType), display: "inline-block",
              }} />
              <strong style={{ fontSize: "0.9rem" }}>{conceptType}</strong>
              <span style={{ color: "#999", fontSize: "0.8rem" }}>({items.length} pairs)</span>
            </div>
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.8rem" }}>
              <thead>
                <tr style={{ borderBottom: "2px solid #e0e0e0" }}>
                  <th style={{ textAlign: "left", padding: "0.4rem" }}>Child</th>
                  <th style={{ textAlign: "center", padding: "0.4rem", color: "#999" }}>part_of</th>
                  <th style={{ textAlign: "left", padding: "0.4rem" }}>Parent</th>
                </tr>
              </thead>
              <tbody>
                {items.map((p, i) => (
                  <tr key={i} style={{ borderBottom: "1px solid #f0f0f0" }}>
                    <td style={{ padding: "0.3rem 0.4rem", fontFamily: "monospace" }}>{p.child}</td>
                    <td style={{ textAlign: "center", color: "#999" }}>&rarr;</td>
                    <td style={{ padding: "0.3rem 0.4rem", fontFamily: "monospace" }}>{p.parent}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ))
      )}
    </div>
  );
}
