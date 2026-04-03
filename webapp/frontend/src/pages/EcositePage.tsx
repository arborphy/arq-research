import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { MapContainer, TileLayer, Polygon, useMap } from "react-leaflet";
import { latLngBounds, type LatLngBoundsExpression } from "leaflet";
import { cellToBoundary } from "h3-js";
import { useEffect, useMemo } from "react";
import { fetchEcosites, fetchEcositeCells, fetchEcositeCompactedCells } from "../api/ecosites";
import { LoadingState } from "../components/LoadingState";
import "leaflet/dist/leaflet.css";

function FitBounds({ bounds }: { bounds: LatLngBoundsExpression | null }) {
  const map = useMap();
  useEffect(() => {
    if (bounds) map.fitBounds(bounds, { padding: [30, 30] });
  }, [map, bounds]);
  return null;
}

function EcositeMap({ cells }: { cells: string[] }) {
  const bounds = useMemo(() => {
    if (cells.length === 0) return null;
    const points: [number, number][] = [];
    const sample = cells.length > 200 ? cells.filter((_, i) => i % Math.ceil(cells.length / 200) === 0) : cells;
    sample.forEach((h3) => {
      try {
        cellToBoundary(h3).forEach(([lat, lng]) => points.push([lat, lng]));
      } catch {}
    });
    return points.length > 0 ? latLngBounds(points) : null;
  }, [cells]);

  return (
    <MapContainer
      center={[43.0, -72.5]}
      zoom={10}
      style={{ height: "520px", width: "100%", borderRadius: "8px" }}
    >
      <FitBounds bounds={bounds} />
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      {cells.map((h3) => {
        try {
          const positions: [number, number][] = cellToBoundary(h3).map(([lat, lng]) => [lat, lng]);
          return (
            <Polygon
              key={h3}
              positions={positions}
              pathOptions={{ color: "#2d6a4f", fillColor: "#52b788", fillOpacity: 0.4, weight: 1 }}
            />
          );
        } catch {
          return null;
        }
      })}
    </MapContainer>
  );
}

export function EcositePage() {
  const [selected, setSelected] = useState<string>("");
  const [compacted, setCompacted] = useState(false);

  const { data: ecositesData, isLoading: loadingList } = useQuery({
    queryKey: ["ecosites"],
    queryFn: fetchEcosites,
  });

  const { data: cellsData, isLoading: loadingCells, isFetching } = useQuery({
    queryKey: ["ecosite-cells", selected, compacted],
    queryFn: () => compacted ? fetchEcositeCompactedCells(selected) : fetchEcositeCells(selected),
    enabled: !!selected,
  });

  const ecosites = ecositesData?.data ?? [];
  const cells = cellsData?.data ?? [];

  return (
    <div>
      <h2>Ecosite Explorer</h2>
      <p style={{ color: "#555", marginBottom: "1.5rem" }}>
        Select an ecosite to see its H3 cell coverage.
      </p>

      {loadingList ? (
        <LoadingState message="Loading ecosites…" />
      ) : (
        <div style={{ display: "flex", alignItems: "center", gap: "1.5rem", marginBottom: "1.5rem", flexWrap: "wrap" }}>
          <div>
            <label htmlFor="ecosite-select" style={{ fontWeight: 600, marginRight: "0.75rem" }}>
              Ecosite
            </label>
            <select
              id="ecosite-select"
              value={selected}
              onChange={(e) => setSelected(e.target.value)}
              style={{ padding: "0.4rem 0.75rem", borderRadius: "6px", border: "1px solid #ccc", fontSize: "0.95rem" }}
            >
              <option value="">— select an ecosite —</option>
              {ecosites.map((id) => (
                <option key={id} value={id}>{id}</option>
              ))}
            </select>
          </div>

          {selected && (
            <div style={{ display: "flex", gap: "0.5rem" }}>
              <button
                onClick={() => setCompacted(false)}
                style={{
                  padding: "0.4rem 0.9rem",
                  borderRadius: "6px",
                  border: "1px solid #2d6a4f",
                  background: !compacted ? "#2d6a4f" : "transparent",
                  color: !compacted ? "#fff" : "#2d6a4f",
                  cursor: "pointer",
                  fontSize: "0.9rem",
                  fontWeight: 600,
                }}
              >
                Full (res 13)
              </button>
              <button
                onClick={() => setCompacted(true)}
                style={{
                  padding: "0.4rem 0.9rem",
                  borderRadius: "6px",
                  border: "1px solid #2d6a4f",
                  background: compacted ? "#2d6a4f" : "transparent",
                  color: compacted ? "#fff" : "#2d6a4f",
                  cursor: "pointer",
                  fontSize: "0.9rem",
                  fontWeight: 600,
                }}
              >
                Compacted
              </button>
            </div>
          )}
        </div>
      )}

      {selected && (
        <>
          {loadingCells || isFetching ? (
            <LoadingState message={`Loading ${compacted ? "compacted " : ""}cells for ${selected}…`} />
          ) : cells.length > 0 ? (
            <>
              <p style={{ color: "#555", marginBottom: "0.75rem" }}>
                <strong>{cells.length.toLocaleString()}</strong> H3 cells
                {compacted ? " (compacted, mixed resolution)" : " (res 13)"}
              </p>
              <EcositeMap cells={cells} />
            </>
          ) : (
            <p style={{ color: "#888" }}>No cells found for {selected}.</p>
          )}
        </>
      )}
    </div>
  );
}
