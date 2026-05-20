import { useState, useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import ForceGraph2D from "react-force-graph-2d";
import { getFamilies, getFamilyGraph, getFamilySpecies } from "../api/taxonomyPredicates";
import { LoadingState } from "../components/LoadingState";

const FAMILY_COLOR = "#1b4332";
const GENUS_COLOR = "#2d6a4f";
const SPECIES_COLOR = "#95d5b2";
const EDGE_DIRECT = "#52b788";
const EDGE_MISSING = "#e63946";

export function TaxonomyPredicatePage() {
  const [selected, setSelected] = useState("");
  const [showDirect, setShowDirect] = useState(false);

  const { data: familiesData, isLoading: loadingFamilies } = useQuery({
    queryKey: ["taxonomy-families"],
    queryFn: getFamilies,
  });

  const { data: graphData, isLoading: loadingGraph } = useQuery({
    queryKey: ["taxonomy-graph", selected],
    queryFn: () => getFamilyGraph(selected),
    enabled: !!selected,
  });

  const { data: directData, isLoading: loadingDirect } = useQuery({
    queryKey: ["taxonomy-species-part-of", selected],
    queryFn: () => getFamilySpecies(selected, "part_of"),
    enabled: !!selected,
  });

  const families = familiesData?.data ?? [];
  const directCount = directData?.data?.length ?? 0;

  const { nodes, links, stats } = useMemo(() => {
    if (!graphData?.data?.length || !selected) {
      return { nodes: [], links: [], stats: { genera: 0, species: 0 } };
    }

    const rows = graphData.data;
    const genusSeen = new Set<string>();
    const speciesSeen = new Set<string>();

    const nodeList: { id: string; level: "family" | "genus" | "species" }[] = [
      { id: selected, level: "family" },
    ];
    const linkList: { source: string; target: string; direct: boolean }[] = [];

    for (const { genus, species } of rows) {
      if (!genusSeen.has(genus)) {
        genusSeen.add(genus);
        nodeList.push({ id: genus, level: "genus" });
        linkList.push({ source: genus, target: selected, direct: true });
      }
      if (!speciesSeen.has(species)) {
        speciesSeen.add(species);
        nodeList.push({ id: species, level: "species" });
        linkList.push({ source: species, target: genus, direct: true });
      }
    }

    // Overlay the "missing" direct species→family edges
    if (showDirect) {
      for (const s of speciesSeen) {
        linkList.push({ source: s, target: selected, direct: false });
      }
    }

    return {
      nodes: nodeList,
      links: linkList,
      stats: { genera: genusSeen.size, species: speciesSeen.size },
    };
  }, [graphData, selected, showDirect]);

  const nodeColor = (n: { level: string }) =>
    n.level === "family" ? FAMILY_COLOR : n.level === "genus" ? GENUS_COLOR : SPECIES_COLOR;

  const nodeSize = (n: { level: string }) =>
    n.level === "family" ? 8 : n.level === "genus" ? 5 : 2;

  return (
    <div>
      <h2>Taxonomic Predicates Explorer</h2>

      <div style={{
        background: "#f0faf4", borderRadius: "8px", padding: "1rem 1.25rem",
        marginBottom: "1.75rem", fontSize: "0.9rem", color: "#333", lineHeight: 1.6,
      }}>
        <p style={{ margin: "0 0 0.5rem" }}>
          GoBotany loads <code>part_of(Species, Genus)</code> and{" "}
          <code>part_of(Genus, Family)</code> — but <em>never</em>{" "}
          <code>part_of(Species, Family)</code>.
        </p>
        <p style={{ margin: 0 }}>
          <code>within_clade</code> is the transitive closure of <code>part_of</code>:{" "}
          it follows <strong>Species → Genus → Family</strong>.
          Toggle the checkbox to see the missing direct edges — those are what{" "}
          <code>part_of(Species, Family)</code> would need.
        </p>
      </div>

      {loadingFamilies ? (
        <LoadingState message="Loading families…" />
      ) : (
        <div style={{ marginBottom: "1.5rem", display: "flex", alignItems: "center", gap: "1rem", flexWrap: "wrap" }}>
          <div>
            <label htmlFor="family-select" style={{ fontWeight: 600, marginRight: "0.75rem" }}>Family</label>
            <select
              id="family-select"
              value={selected}
              onChange={(e) => { setSelected(e.target.value); setShowDirect(false); }}
              style={{ padding: "0.4rem 0.75rem", borderRadius: "6px", border: "1px solid #ccc", fontSize: "0.95rem" }}
            >
              <option value="">— select a family —</option>
              {families.map((f) => <option key={f} value={f}>{f}</option>)}
            </select>
            <span style={{ marginLeft: "0.75rem", color: "#888", fontSize: "0.85rem" }}>
              {families.length} families
            </span>
          </div>

          {selected && (
            <label style={{ display: "flex", alignItems: "center", gap: "0.5rem", fontSize: "0.85rem", cursor: "pointer", userSelect: "none" }}>
              <input type="checkbox" checked={showDirect} onChange={(e) => setShowDirect(e.target.checked)} />
              Show missing <code style={{ color: EDGE_MISSING }}>part_of(Species, {selected})</code> edges
            </label>
          )}
        </div>
      )}

      {selected && (
        <>
          {/* Stats / direct-count badge */}
          <div style={{ display: "flex", gap: "1.5rem", marginBottom: "0.75rem", fontSize: "0.85rem", alignItems: "center", flexWrap: "wrap" }}>
            <span style={{ display: "flex", alignItems: "center", gap: "0.4rem" }}>
              <span style={{ width: 12, height: 12, borderRadius: "50%", background: FAMILY_COLOR, display: "inline-block" }} />
              <strong>{selected}</strong>
            </span>
            <span style={{ display: "flex", alignItems: "center", gap: "0.4rem" }}>
              <span style={{ width: 10, height: 10, borderRadius: "50%", background: GENUS_COLOR, display: "inline-block" }} />
              {stats.genera} genera
            </span>
            <span style={{ display: "flex", alignItems: "center", gap: "0.4rem" }}>
              <span style={{ width: 8, height: 8, borderRadius: "50%", background: SPECIES_COLOR, display: "inline-block" }} />
              {stats.species} species
            </span>

            <div style={{
              marginLeft: "auto",
              padding: "0.2rem 0.7rem",
              borderRadius: "6px",
              background: directCount === 0 ? "#fff5f5" : "#f0faf4",
              border: `1px solid ${directCount === 0 ? "#fca5a5" : "#86efac"}`,
              color: directCount === 0 ? "#b91c1c" : "#166534",
              fontFamily: "monospace",
              fontSize: "0.82rem",
            }}>
              part_of(Species, {selected}) → {loadingDirect ? "…" : `${directCount} direct`}
            </div>
          </div>

          {/* Graph */}
          {loadingGraph ? (
            <LoadingState message="Building graph…" />
          ) : (
            <div style={{ border: "1px solid #d8f3dc", borderRadius: "8px", overflow: "hidden", background: "#f8fdf9" }}>
              <ForceGraph2D
                graphData={{ nodes, links }}
                width={720}
                height={500}
                nodeLabel={(n: any) => `${n.id} (${n.level})`}
                nodeVal={(n: any) => nodeSize(n) * nodeSize(n)}
                nodeColor={(n: any) => nodeColor(n)}
                linkColor={(l: any) => l.direct ? EDGE_DIRECT : EDGE_MISSING}
                linkWidth={(l: any) => l.direct ? 1.5 : 0.8}
                linkLineDash={(l: any) => l.direct ? null : [4, 3]}
                linkDirectionalArrowLength={4}
                linkDirectionalArrowRelPos={1}
                cooldownTicks={150}
                nodeCanvasObject={(node: any, ctx: CanvasRenderingContext2D, scale: number) => {
                  const r = nodeSize(node);
                  ctx.beginPath();
                  ctx.arc(node.x, node.y, r, 0, 2 * Math.PI);
                  ctx.fillStyle = nodeColor(node);
                  ctx.fill();

                  const showLabel = node.level === "family" || node.level === "genus" || scale > 4;
                  if (showLabel) {
                    const fontSize = Math.max(10 / scale, 2.5);
                    ctx.font = `${node.level === "family" ? "bold " : ""}${fontSize}px sans-serif`;
                    ctx.textAlign = "center";
                    ctx.textBaseline = "top";
                    ctx.fillStyle = "#111";
                    ctx.fillText(node.id, node.x, node.y + r + 2);
                  }
                }}
              />
            </div>
          )}

          {/* Legend */}
          <div style={{ display: "flex", gap: "1.5rem", marginTop: "0.6rem", fontSize: "0.78rem", color: "#666", flexWrap: "wrap" }}>
            <span>
              <span style={{ color: EDGE_DIRECT, fontSize: "1rem" }}>—</span>{" "}
              <code>part_of</code> edges in the data
            </span>
            {showDirect && (
              <span>
                <span style={{ color: EDGE_MISSING, fontSize: "1rem" }}>- -</span>{" "}
                <code>part_of(Species, Family)</code> — absent from data
              </span>
            )}
            <span style={{ marginLeft: "auto" }}>zoom/drag to explore · species labels visible on zoom-in</span>
          </div>
        </>
      )}
    </div>
  );
}
