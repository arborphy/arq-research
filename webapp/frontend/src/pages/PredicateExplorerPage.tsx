import { useState, useMemo, useCallback, useRef } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import ForceGraph2D from "react-force-graph-2d";
import { getPredicateSummary, getPredicatePairs, getPredicateGraph } from "../api/predicates";
import { LoadingState } from "../components/LoadingState";

const CONCEPT_COLORS: Record<string, string> = {
  "Species": "#2d6a4f",
  "Genus": "#606c38",
  "Kingdom": "#283618",
  "Species → Genus": "#2d6a4f",
  "Genus → Kingdom": "#606c38",
  "FeatureValue": "#e9c46a",
  "Feature": "#e76f51",
  "FeatureValue → Feature": "#e76f51",
  "ALL (Entity)": "#457b9d",
};

const DEFAULT_COLOR = "#888";

function colorFor(conceptType: string): string {
  return CONCEPT_COLORS[conceptType] ?? DEFAULT_COLOR;
}

export function PredicateExplorerPage() {
  const [filter, setFilter] = useState<"all" | "species" | "genus" | "feature">("all");
  const graphRef = useRef<any>(null);

  const { data: summaryData, isLoading: summaryLoading } = useQuery({
    queryKey: ["predicate-summary"],
    queryFn: getPredicateSummary,
  });

  const { data: pairsData, isLoading: pairsLoading } = useQuery({
    queryKey: ["predicate-pairs", filter],
    queryFn: () => getPredicatePairs(filter, 50),
  });

  const { data: graphData, isLoading: graphLoading } = useQuery({
    queryKey: ["predicate-graph"],
    queryFn: getPredicateGraph,
    staleTime: 5 * 60 * 1000,
  });

  const { nodes, links, conceptTypes, colorMap } = useMemo(() => {
    if (!graphData) return { nodes: [], links: [], conceptTypes: [], colorMap: new Map<string, string>() };

    const colorMap = new Map<string, string>();
    const conceptTypes = [...new Set(graphData.nodes.map((n) => n.concept_type))];
    conceptTypes.forEach((ct) => colorMap.set(ct, colorFor(ct)));

    const neighborMap = new Map<string, Set<string>>();
    for (const n of graphData.nodes) neighborMap.set(n.id, new Set());
    for (const e of graphData.edges) {
      neighborMap.get(e.source)?.add(e.target);
      neighborMap.get(e.target)?.add(e.source);
    }

    const nodes = graphData.nodes.map((n) => ({
      id: n.id,
      label: n.label,
      concept_type: n.concept_type,
      neighbors: neighborMap.get(n.id) ?? new Set<string>(),
    }));

    const links = graphData.edges.map((e) => ({ source: e.source, target: e.target, type: e.type ?? "part_of" }));

    return { nodes, links, conceptTypes, colorMap };
  }, [graphData]);

  const nodeCanvasObject = useCallback(
    (node: any, ctx: CanvasRenderingContext2D, globalScale: number) => {
      const fontSize = Math.max(10 / globalScale, 2);
      const size = Math.sqrt(Math.max(1, node.neighbors?.size ?? 1)) * 4;
      const color = colorMap.get(node.concept_type) ?? DEFAULT_COLOR;

      ctx.beginPath();
      ctx.arc(node.x, node.y, size, 0, 2 * Math.PI);
      ctx.fillStyle = color;
      ctx.fill();

      if (globalScale > 1.2) {
        ctx.font = `${fontSize}px sans-serif`;
        ctx.textAlign = "center";
        ctx.textBaseline = "top";
        ctx.fillStyle = "#333";
        ctx.fillText(node.label, node.x, node.y + size + 2);
      }
    },
    [colorMap],
  );

  const summary = summaryData?.data ?? [];
  const pairs = pairsData?.data ?? [];

  // Group pairs by concept_type
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
      <div style={{ display: "flex", gap: "2rem", flexWrap: "wrap" }}>
        <div style={{ flex: "1 1 400px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", marginBottom: "1rem" }}>
            <h3 style={{ margin: 0 }}>Pairs</h3>
            {(["all", "species", "genus", "feature"] as const).map((f) => {
              const labels: Record<string, string> = {
                all: "All",
                species: "Species → Genus",
                genus: "Genus → Kingdom",
                feature: "FeatureValue → Feature",
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
                <div style={{
                  display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "0.5rem",
                }}>
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

        {/* Graph visualization */}
        <div style={{ flex: "1 1 400px" }}>
          <h3>Graph</h3>
          {graphLoading ? (
            <LoadingState message="Loading graph..." />
          ) : (
            <>
              <p style={{ color: "#666", fontSize: "0.8rem", marginTop: 0 }}>
                {nodes.length} nodes, {links.length} edges. Nodes colored by concept type.
              </p>
              <div style={{
                border: "1px solid #e0e0e0", borderRadius: "8px",
                overflow: "hidden", background: "#fafafa",
              }}>
                <ForceGraph2D
                  ref={graphRef}
                  graphData={{ nodes, links }}
                  width={500}
                  height={400}
                  nodeLabel={(node: any) => `${node.label} (${node.concept_type})`}
                  nodeRelSize={5}
                  nodeVal={(node: any) => Math.max(1, node.neighbors?.size ?? 1)}
                  linkColor={(link: any) => link.type === "hasFeature" ? "#e9c46a88" : "#d0d0d0"}
                  linkWidth={(link: any) => link.type === "hasFeature" ? 0.5 : 1}
                  linkLineDash={(link: any) => link.type === "hasFeature" ? [2, 2] : []}
                  linkDirectionalArrowLength={4}
                  linkDirectionalArrowRelPos={0.9}
                  nodeCanvasObject={nodeCanvasObject}
                  cooldownTicks={100}
                />
              </div>
              {/* Legend */}
              <div style={{ display: "flex", gap: "1rem", marginTop: "0.75rem", flexWrap: "wrap", fontSize: "0.8rem" }}>
                {conceptTypes.map((ct) => (
                  <div key={ct} style={{ display: "flex", alignItems: "center", gap: "0.3rem" }}>
                    <span style={{
                      width: "10px", height: "10px", borderRadius: "50%",
                      background: colorMap.get(ct) ?? DEFAULT_COLOR, display: "inline-block",
                    }} />
                    <span style={{ color: "#555" }}>{ct}</span>
                  </div>
                ))}
                <div style={{ display: "flex", alignItems: "center", gap: "0.3rem" }}>
                  <span style={{ width: "16px", height: "2px", background: "#d0d0d0", display: "inline-block" }} />
                  <span style={{ color: "#555" }}>part_of</span>
                </div>
                <div style={{ display: "flex", alignItems: "center", gap: "0.3rem" }}>
                  <span style={{ width: "16px", height: "2px", background: "#e9c46a", display: "inline-block", borderTop: "1px dashed #e9c46a" }} />
                  <span style={{ color: "#555" }}>hasFeature</span>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
