import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { MapContainer, TileLayer, CircleMarker, Polygon, Popup, useMap } from "react-leaflet";
import { latLngBounds, type LatLngBoundsExpression } from "leaflet";
import { cellToBoundary } from "h3-js";
import { useEffect, useMemo } from "react";
import {
  fetchTrails,
  fetchAllTrailCells, fetchAllTrailObservations, fetchAllTrailEcosites, fetchAllTrailEcositeCells,
  fetchTrailCells, fetchTrailObservations, fetchTrailEcosites, fetchTrailEcositeCells,
  type TrailObservation, type EcositeCell,
} from "../api/trails";
import { LoadingState } from "../components/LoadingState";
import "leaflet/dist/leaflet.css";

const ALL = "__all__";

// Distinct colors for up to ~20 ecosites; cycles if more
const ECOSITE_PALETTE = [
  "#e76f51", "#f4a261", "#e9c46a", "#2a9d8f", "#457b9d",
  "#a8dadc", "#6a4c93", "#c77dff", "#52b788", "#d62828",
  "#4cc9f0", "#f72585", "#7209b7", "#3a86ff", "#fb5607",
  "#8338ec", "#06d6a0", "#ef233c", "#ffd60a", "#b5838d",
];

function buildColorMap(ecositeIds: string[]): Record<string, string> {
  const sorted = [...new Set(ecositeIds)].sort();
  const map: Record<string, string> = {};
  sorted.forEach((id, i) => {
    map[id] = ECOSITE_PALETTE[i % ECOSITE_PALETTE.length];
  });
  return map;
}

function FitBounds({ bounds }: { bounds: LatLngBoundsExpression | null }) {
  const map = useMap();
  useEffect(() => {
    if (bounds) map.fitBounds(bounds, { padding: [40, 40] });
  }, [map, bounds]);
  return null;
}

function TrailMap({ cells, ecositeCells, observations }: {
  cells: string[];
  ecositeCells: EcositeCell[];
  observations: TrailObservation[];
}) {
  const { cellColorMap, colorMap } = useMemo(() => {
    const colorMap = buildColorMap(ecositeCells.map((e) => e.ecosite_id));
    const cellColorMap: Record<string, string> = {};
    ecositeCells.forEach(({ ecosite_id, h3_index }) => {
      cellColorMap[h3_index] = colorMap[ecosite_id];
    });
    return { cellColorMap, colorMap };
  }, [ecositeCells]);

  const bounds = useMemo(() => {
    const points: [number, number][] = [];
    const sample = cells.length > 500 ? cells.filter((_, i) => i % Math.ceil(cells.length / 500) === 0) : cells;
    sample.forEach((h3) => {
      try {
        cellToBoundary(h3).forEach(([lat, lng]) => points.push([lat, lng]));
      } catch {}
    });
    observations.forEach((o) => points.push([o.latitude, o.longitude]));
    return points.length > 0 ? latLngBounds(points) : null;
  }, [cells, observations]);

  return (
    <MapContainer
      center={[41.2, -73.6]}
      zoom={13}
      style={{ height: "500px", width: "100%", borderRadius: "8px" }}
    >
      <FitBounds bounds={bounds} />
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />

      {cells.map((h3) => {
        try {
          const positions: [number, number][] = cellToBoundary(h3).map(([lat, lng]) => [lat, lng]);
          const ecositeColor = cellColorMap[h3];
          return (
            <Polygon
              key={h3}
              positions={positions}
              pathOptions={ecositeColor
                ? { color: ecositeColor, fillColor: ecositeColor, fillOpacity: 0.55, weight: 1 }
                : { color: "#2d6a4f", fillColor: "#52b788", fillOpacity: 0.4, weight: 1 }
              }
            />
          );
        } catch {
          return null;
        }
      })}

      {observations.map((obs) => (
        <CircleMarker
          key={obs.inat_id}
          center={[obs.latitude, obs.longitude]}
          radius={5}
          pathOptions={{ color: "#d62828", fillColor: "#e76f51", fillOpacity: 0.8, weight: 1 }}
        >
          <Popup>
            <em>{obs.species}</em>
            <br />
            <strong>{obs.date}</strong>
            {obs.image_url && (
              <>
                <br />
                <img src={obs.image_url} alt={obs.species} style={{ width: "120px", marginTop: "4px", borderRadius: "4px" }} />
              </>
            )}
          </Popup>
        </CircleMarker>
      ))}
    </MapContainer>
  );
}

export function TrailsPage() {
  const [selectedOsmId, setSelectedOsmId] = useState<string>("");
  const isAll = selectedOsmId === ALL;

  const { data: trailsData, isLoading: loadingTrails } = useQuery({
    queryKey: ["trails"],
    queryFn: fetchTrails,
  });

  const { data: allCellsData, isLoading: loadingAllCells, isFetching: fetchingAllCells } = useQuery({
    queryKey: ["trail-cells-all"],
    queryFn: fetchAllTrailCells,
    enabled: isAll,
  });
  const { data: allObsData, isLoading: loadingAllObs, isFetching: fetchingAllObs } = useQuery({
    queryKey: ["trail-observations-all"],
    queryFn: fetchAllTrailObservations,
    enabled: isAll,
  });
  const { data: allEcositeData, isLoading: loadingAllEcosites, isFetching: fetchingAllEcosites } = useQuery({
    queryKey: ["trail-ecosites-all"],
    queryFn: fetchAllTrailEcosites,
    enabled: isAll,
  });
  const { data: allEcositeCellsData, isLoading: loadingAllEcositeCells, isFetching: fetchingAllEcositeCells } = useQuery({
    queryKey: ["trail-ecosite-cells-all"],
    queryFn: fetchAllTrailEcositeCells,
    enabled: isAll,
  });

  const { data: cellsData, isLoading: loadingCells, isFetching: fetchingCells } = useQuery({
    queryKey: ["trail-cells", selectedOsmId],
    queryFn: () => fetchTrailCells(selectedOsmId),
    enabled: !!selectedOsmId && !isAll,
  });
  const { data: obsData, isLoading: loadingObs, isFetching: fetchingObs } = useQuery({
    queryKey: ["trail-observations", selectedOsmId],
    queryFn: () => fetchTrailObservations(selectedOsmId),
    enabled: !!selectedOsmId && !isAll,
  });
  const { data: ecositeData, isLoading: loadingEcosites, isFetching: fetchingEcosites } = useQuery({
    queryKey: ["trail-ecosites", selectedOsmId],
    queryFn: () => fetchTrailEcosites(selectedOsmId),
    enabled: !!selectedOsmId && !isAll,
  });
  const { data: ecositeCellsData, isLoading: loadingEcositeCells, isFetching: fetchingEcositeCells } = useQuery({
    queryKey: ["trail-ecosite-cells", selectedOsmId],
    queryFn: () => fetchTrailEcositeCells(selectedOsmId),
    enabled: !!selectedOsmId && !isAll,
  });

  const trails = trailsData?.data ?? [];
  const cells = isAll ? (allCellsData?.data ?? []) : (cellsData?.data ?? []);
  const observations = isAll ? (allObsData?.data ?? []) : (obsData?.data ?? []);
  const ecosites = isAll ? (allEcositeData?.data ?? []) : (ecositeData?.data ?? []);
  const ecositeCells = isAll ? (allEcositeCellsData?.data ?? []) : (ecositeCellsData?.data ?? []);

  // Build color map once for legend
  const colorMap = useMemo(() => buildColorMap(ecosites), [ecosites]);

  const selectedTrail = trails.find((t) => t.osm_id === selectedOsmId);
  const isLoading =
    loadingAllCells || fetchingAllCells || loadingAllObs || fetchingAllObs ||
    loadingAllEcosites || fetchingAllEcosites || loadingAllEcositeCells || fetchingAllEcositeCells ||
    loadingCells || loadingObs || loadingEcosites || loadingEcositeCells ||
    fetchingCells || fetchingObs || fetchingEcosites || fetchingEcositeCells;

  return (
    <div>
      <h2>Trail Explorer</h2>
      <p style={{ color: "#555", marginBottom: "1.5rem" }}>
        Select a trail to see its H3 cell coverage, observations, and ecosites (res-13 spatial join).
      </p>

      {loadingTrails ? (
        <LoadingState message="Loading trails…" />
      ) : (
        <div style={{ marginBottom: "1.5rem" }}>
          <label htmlFor="trail-select" style={{ fontWeight: 600, marginRight: "0.75rem" }}>
            Trail
          </label>
          <select
            id="trail-select"
            value={selectedOsmId}
            onChange={(e) => setSelectedOsmId(e.target.value)}
            style={{ padding: "0.4rem 0.75rem", borderRadius: "6px", border: "1px solid #ccc", fontSize: "0.95rem" }}
          >
            <option value="">— select a trail —</option>
            <option value={ALL}>All trails</option>
            {trails.map((t) => (
              <option key={t.osm_id} value={t.osm_id}>
                {t.name || `[${t.highway}]`} #{t.osm_id}
              </option>
            ))}
          </select>
        </div>
      )}

      {selectedTrail && (
        <div style={{ marginBottom: "1rem", color: "#555", fontSize: "0.9rem" }}>
          {selectedTrail.highway && <span style={{ marginRight: "1rem" }}>Type: <strong>{selectedTrail.highway}</strong></span>}
          {selectedTrail.surface && <span>Surface: <strong>{selectedTrail.surface}</strong></span>}
        </div>
      )}

      {selectedOsmId && (
        <>
          {isLoading ? (
            <LoadingState message="Loading trail data…" />
          ) : (
            <>
              <div style={{ display: "flex", gap: "1.5rem", fontSize: "0.85rem", marginBottom: "0.75rem", flexWrap: "wrap" }}>
                <span><span style={{ color: "#2d6a4f" }}>■</span> Trail cells ({cells.length.toLocaleString()})</span>
                <span><span style={{ color: "#888" }}>■</span> Ecosite overlap ({ecositeCells.length.toLocaleString()})</span>
                <span><span style={{ color: "#d62828" }}>●</span> Observations ({observations.length.toLocaleString()})</span>
              </div>
              <TrailMap cells={cells} ecositeCells={ecositeCells} observations={observations} />

              {ecosites.length > 0 && (
                <div style={{ marginTop: "1.5rem" }}>
                  <h3 style={{ marginBottom: "0.75rem", fontSize: "1rem" }}>Ecosites along this trail</h3>
                  <div style={{ display: "flex", flexWrap: "wrap", gap: "0.5rem" }}>
                    {ecosites.map((id) => (
                      <span
                        key={id}
                        style={{
                          padding: "0.25rem 0.6rem",
                          background: colorMap[id] + "22",
                          border: `1px solid ${colorMap[id]}`,
                          borderRadius: "4px",
                          fontSize: "0.85rem",
                          color: colorMap[id],
                          fontWeight: 600,
                        }}
                      >
                        {id}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </>
          )}
        </>
      )}
    </div>
  );
}
