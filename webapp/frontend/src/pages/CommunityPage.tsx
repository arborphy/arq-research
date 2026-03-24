import { useMemo, useCallback, useRef } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link, useNavigate } from "react-router-dom";
import ForceGraph2D from "react-force-graph-2d";
import { getCoOccurrenceGraph } from "../api/co_occurrence";
import { LoadingState } from "../components/LoadingState";

const COMMUNITY_COLORS = [
  "#2d6a4f", "#d62828", "#457b9d", "#e9c46a", "#f4a261",
  "#264653", "#e76f51", "#606c38", "#283618", "#bc6c25",
  "#6d597a", "#b56576", "#355070", "#eaac8b", "#8ecae6",
];

interface GraphNode {
  id: string;
  name: string;
  community: string;
  neighbors: Set<string>;
}

interface GraphLink {
  source: string;
  target: string;
}

export function CommunityPage() {
  const navigate = useNavigate();
  const graphRef = useRef<any>(null);

  const { data, isLoading } = useQuery({
    queryKey: ["co-occurrence-graph"],
    queryFn: getCoOccurrenceGraph,
    staleTime: 5 * 60 * 1000,
  });

  const { graphData, communityList, colorMap } = useMemo(() => {
    if (!data) return { graphData: { nodes: [], links: [] }, communityList: [], colorMap: new Map() };

    const communities = data.communities ?? {};
    const uniqueCommunities = [...new Set(Object.values(communities))];
    const colorMap = new Map<string, string>();
    uniqueCommunities.forEach((c, i) => colorMap.set(c, COMMUNITY_COLORS[i % COMMUNITY_COLORS.length]));

    const neighborMap = new Map<string, Set<string>>();
    for (const name of data.nodes) {
      neighborMap.set(name, new Set());
    }
    for (const edge of data.edges) {
      neighborMap.get(edge.source)?.add(edge.target);
      neighborMap.get(edge.target)?.add(edge.source);
    }

    const nodes: GraphNode[] = data.nodes.map((name) => ({
      id: name,
      name,
      community: communities[name] ?? "unknown",
      neighbors: neighborMap.get(name) ?? new Set(),
    }));

    const links: GraphLink[] = data.edges.map((e) => ({
      source: e.source,
      target: e.target,
    }));

    const commCounts = new Map<string, number>();
    for (const n of nodes) {
      commCounts.set(n.community, (commCounts.get(n.community) ?? 0) + 1);
    }
    const communityList = [...commCounts.entries()]
      .sort((a, b) => b[1] - a[1])
      .map(([name, count]) => ({ name, count, color: colorMap.get(name) ?? "#888" }));

    return { graphData: { nodes, links }, communityList, colorMap };
  }, [data]);

  const handleNodeClick = useCallback((node: GraphNode) => {
    navigate(`/species/${encodeURIComponent(node.id)}`);
  }, [navigate]);

  if (isLoading) return <LoadingState message="Loading co-occurrence graph..." />;

  return (
    <div>
      <Link to="/">&larr; Home</Link>
      <h2>Species Community Graph</h2>
      <p style={{ color: "#666", fontSize: "0.85rem" }}>
        {graphData.nodes.length} species, {graphData.links.length} co-occurrence links, {communityList.length} communities (WCC).
        Click a node to view species details.
      </p>

      <div style={{ display: "flex", gap: "1rem" }}>
        <div style={{
          flex: 1, border: "1px solid #e0e0e0", borderRadius: "8px",
          overflow: "hidden", background: "#fafafa",
        }}>
          <ForceGraph2D
            ref={graphRef}
            graphData={graphData}
            width={600}
            height={500}
            nodeLabel={(node: GraphNode) => `${node.name} (community: ${node.community})`}
            nodeRelSize={5}
            nodeVal={(node: GraphNode) => Math.max(1, node.neighbors.size)}
            linkColor={() => "#d0d0d0"}
            linkWidth={1}
            onNodeClick={handleNodeClick}
            nodeCanvasObject={(node: any, ctx: CanvasRenderingContext2D, globalScale: number) => {
              const fontSize = Math.max(10 / globalScale, 2);
              const nodeSize = Math.sqrt(Math.max(1, node.neighbors?.size ?? 1)) * 3;
              const color = colorMap.get(node.community) ?? "#888";

              ctx.beginPath();
              ctx.arc(node.x, node.y, nodeSize, 0, 2 * Math.PI);
              ctx.fillStyle = color;
              ctx.fill();

              if (globalScale > 1.5) {
                ctx.font = `${fontSize}px sans-serif`;
                ctx.textAlign = "center";
                ctx.textBaseline = "top";
                ctx.fillStyle = "#333";
                ctx.fillText(node.name, node.x, node.y + nodeSize + 2);
              }
            }}
            cooldownTicks={100}
          />
        </div>

        <div style={{ width: "200px", flexShrink: 0 }}>
          <h3 style={{ fontSize: "0.9rem", marginTop: 0 }}>Communities</h3>
          <div style={{ fontSize: "0.8rem" }}>
            {communityList.map((c) => (
              <div key={c.name} style={{ display: "flex", alignItems: "center", gap: "0.4rem", marginBottom: "0.3rem" }}>
                <span style={{
                  width: "10px", height: "10px", borderRadius: "50%",
                  background: c.color, display: "inline-block", flexShrink: 0,
                }} />
                <span style={{ color: "#444" }}>{c.count} species</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
