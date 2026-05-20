import { useState, useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import ForceGraph2D from "react-force-graph-2d";
import { fetchEcositesWithObservations, fetchEcositeSpecies } from "../api/ecosites";
import { LoadingState } from "../components/LoadingState";

const ECOSITE_COLOR = "#1b4332";
const SPECIES_COLOR = "#95d5b2";
const EDGE_COLOR = "#52b788";

export function EcositeSpeciesPage() {
  const [selected, setSelected] = useState("");

  const { data: ecositesData, isLoading: loadingList } = useQuery({
    queryKey: ["ecosites-with-obs"],
    queryFn: fetchEcositesWithObservations,
  });

  const { data: speciesData, isLoading: loadingSpecies } = useQuery({
    queryKey: ["ecosite-species", selected],
    queryFn: () => fetchEcositeSpecies(selected),
    enabled: !!selected,
  });

  const ecosites = ecositesData?.data ?? [];
  const speciesList = speciesData?.data ?? [];

  const { nodes, links } = useMemo(() => {
    if (!selected || !speciesList.length) return { nodes: [], links: [] };

    const nodes = [
      { id: selected, type: "ecosite" as const },
      ...speciesList.map((s) => ({ id: s, type: "species" as const })),
    ];
    const links = speciesList.map((s) => ({ source: s, target: selected }));
    return { nodes, links };
  }, [selected, speciesList]);

  return (
    <div>
      <h2>Species Co-Existence by Ecosite</h2>

      <div style={{
        background: "#f0faf4", borderRadius: "8px", padding: "1rem 1.25rem",
        marginBottom: "1.75rem", fontSize: "0.9rem", color: "#333", lineHeight: 1.6,
      }}>
        <p style={{ margin: "0 0 0.5rem" }}>
          Tracing the path{" "}
          <strong>Species → Observation → H3Cell(res-13) → H3Cell(res-12) → EcoSite</strong>{" "}
          using explicit multi-hop joins over <code>located_in</code>.
        </p>
        <p style={{ margin: 0 }}>
          All species shown share the same ecosite — they co-exist within that geographic area,
          connected through their iNaturalist observations and H3 spatial cells.
        </p>
      </div>

      {loadingList ? (
        <LoadingState message="Loading ecosites with observations…" />
      ) : (
        <div style={{ marginBottom: "1.5rem", display: "flex", alignItems: "center", gap: "1rem", flexWrap: "wrap" }}>
          <div>
            <label htmlFor="ecosite-select" style={{ fontWeight: 600, marginRight: "0.75rem" }}>Ecosite</label>
            <select
              id="ecosite-select"
              value={selected}
              onChange={(e) => setSelected(e.target.value)}
              style={{ padding: "0.4rem 0.75rem", borderRadius: "6px", border: "1px solid #ccc", fontSize: "0.95rem" }}
            >
              <option value="">— select an ecosite —</option>
              {ecosites.map((id) => <option key={id} value={id}>{id}</option>)}
            </select>
            <span style={{ marginLeft: "0.75rem", color: "#888", fontSize: "0.85rem" }}>
              {ecosites.length} ecosites with observations
            </span>
          </div>
        </div>
      )}

      {selected && (
        <>
          <div style={{ display: "flex", gap: "1.5rem", marginBottom: "0.75rem", fontSize: "0.85rem", alignItems: "center" }}>
            <span style={{ display: "flex", alignItems: "center", gap: "0.4rem" }}>
              <span style={{ width: 14, height: 14, borderRadius: "50%", background: ECOSITE_COLOR, display: "inline-block" }} />
              <strong>{selected}</strong>
            </span>
            <span style={{ display: "flex", alignItems: "center", gap: "0.4rem" }}>
              <span style={{ width: 10, height: 10, borderRadius: "50%", background: SPECIES_COLOR, display: "inline-block" }} />
              {loadingSpecies ? "…" : `${speciesList.length} species`}
            </span>
          </div>

          {loadingSpecies ? (
            <LoadingState message={`Finding species in ${selected}…`} />
          ) : speciesList.length === 0 ? (
            <p style={{ color: "#888" }}>No species observations found for this ecosite.</p>
          ) : (
            <div style={{ border: "1px solid #d8f3dc", borderRadius: "8px", overflow: "hidden", background: "#f8fdf9" }}>
              <ForceGraph2D
                graphData={{ nodes, links }}
                width={720}
                height={500}
                nodeLabel={(n: any) => n.type === "ecosite" ? `Ecosite: ${n.id}` : n.id}
                nodeVal={(n: any) => n.type === "ecosite" ? 64 : 4}
                nodeColor={(n: any) => n.type === "ecosite" ? ECOSITE_COLOR : SPECIES_COLOR}
                linkColor={() => EDGE_COLOR}
                linkWidth={0.8}
                linkDirectionalArrowLength={3}
                linkDirectionalArrowRelPos={1}
                cooldownTicks={120}
                nodeCanvasObject={(node: any, ctx: CanvasRenderingContext2D, scale: number) => {
                  const isEcosite = node.type === "ecosite";
                  const r = isEcosite ? 10 : 3;
                  ctx.beginPath();
                  ctx.arc(node.x, node.y, r, 0, 2 * Math.PI);
                  ctx.fillStyle = isEcosite ? ECOSITE_COLOR : SPECIES_COLOR;
                  ctx.fill();

                  const showLabel = isEcosite || scale > 3;
                  if (showLabel) {
                    const fontSize = isEcosite ? Math.max(12 / scale, 3) : Math.max(9 / scale, 2);
                    ctx.font = `${isEcosite ? "bold " : ""}${fontSize}px sans-serif`;
                    ctx.textAlign = "center";
                    ctx.textBaseline = "top";
                    ctx.fillStyle = "#111";
                    ctx.fillText(node.id, node.x, node.y + r + 2);
                  }
                }}
              />
            </div>
          )}

          <div style={{ marginTop: "0.6rem", fontSize: "0.78rem", color: "#666" }}>
            <span>
              <span style={{ color: EDGE_COLOR, fontSize: "1rem" }}>—</span>{" "}
              observed within (Species → Obs → H3Cell → EcoSite)
            </span>
            <span style={{ marginLeft: "1.5rem" }}>zoom/drag to explore · species labels visible on zoom-in</span>
          </div>
        </>
      )}
    </div>
  );
}
