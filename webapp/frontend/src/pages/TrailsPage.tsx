import { useState } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { MapContainer, TileLayer, CircleMarker, Polygon, Popup, useMap } from "react-leaflet";
import { latLngBounds, type LatLngBoundsExpression } from "leaflet";
import { cellToBoundary } from "h3-js";
import { useEffect, useMemo } from "react";
import {
  fetchTrails,
  fetchAllTrailCells, fetchAllTrailObservations, fetchAllTrailEcosites, fetchAllTrailEcositeCells,
  fetchTrailCells, fetchTrailObservations, fetchTrailEcosites, fetchTrailEcositeCells,
  fetchTrailSpecies, fetchTrailFeatures, filterTrailSpecies,
  type TrailObservation, type EcositeCell, type FilterItem,
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
  const [filters, setFilters] = useState<FilterItem[]>([]);
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

  const { data: speciesData, isLoading: loadingSpecies, isFetching: fetchingSpecies } = useQuery({
    queryKey: ["trail-species", selectedOsmId],
    queryFn: () => fetchTrailSpecies(selectedOsmId),
    enabled: !!selectedOsmId && !isAll,
  });

  const { data: featuresData, isLoading: loadingFeatures } = useQuery({
    queryKey: ["trail-features", selectedOsmId],
    queryFn: () => fetchTrailFeatures(selectedOsmId),
    enabled: !!selectedOsmId && !isAll,
  });

  const { data: filteredData, isLoading: loadingFiltered } = useQuery({
    queryKey: ["trail-species-filtered", selectedOsmId, filters],
    queryFn: () => filterTrailSpecies(selectedOsmId, filters),
    enabled: !!selectedOsmId && !isAll && filters.length > 0,
  });

  const trails = trailsData?.data ?? [];
  const cells = isAll ? (allCellsData?.data ?? []) : (cellsData?.data ?? []);
  const allObservations = isAll ? (allObsData?.data ?? []) : (obsData?.data ?? []);
  const ecosites = isAll ? (allEcositeData?.data ?? []) : (ecositeData?.data ?? []);
  const ecositeCells = isAll ? (allEcositeCellsData?.data ?? []) : (ecositeCellsData?.data ?? []);
  const allSpecies = speciesData?.data ?? [];
  const features = featuresData?.data ?? {};

  const activeSpeciesSet = filters.length > 0 ? new Set(filteredData?.data ?? []) : null;
  const species = activeSpeciesSet ? allSpecies.filter((n) => activeSpeciesSet.has(n)) : allSpecies;
  const observations = activeSpeciesSet
    ? allObservations.filter((o) => activeSpeciesSet.has(o.species))
    : allObservations;

  // Build color map once for legend
  const colorMap = useMemo(() => buildColorMap(ecosites), [ecosites]);

  const selectedTrail = trails.find((t) => t.osm_id === selectedOsmId);
  const isLoading =
    loadingAllCells || fetchingAllCells || loadingAllObs || fetchingAllObs ||
    loadingAllEcosites || fetchingAllEcosites || loadingAllEcositeCells || fetchingAllEcositeCells ||
    loadingCells || loadingObs || loadingEcosites || loadingEcositeCells ||
    fetchingCells || fetchingObs || fetchingEcosites || fetchingEcositeCells ||
    loadingSpecies || fetchingSpecies;

  function isFilterActive(feature: string, value: string) {
    return filters.some((f) => f.feature === feature && f.value === value);
  }

  function toggleFilter(feature: string, value: string) {
    setFilters((prev) =>
      isFilterActive(feature, value)
        ? prev.filter((f) => !(f.feature === feature && f.value === value))
        : [...prev, { feature, value }]
    );
  }

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
            onChange={(e) => { setSelectedOsmId(e.target.value); setFilters([]); }}
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

              {Object.keys(features).length > 0 && (
                <div style={{ marginTop: "1.5rem", paddingBottom: filters.length > 0 ? "33vh" : 0 }}>
                  <h3 style={{ marginBottom: "0.5rem", fontSize: "1rem" }}>Filter by features</h3>
                  {loadingFeatures ? (
                    <LoadingState message="Loading features…" />
                  ) : (
                    <div style={{ display: "flex", flexDirection: "column", gap: "0.2rem" }}>
                      {Object.entries(features).map(([feature, values]) => (
                        <div key={feature} style={{ display: "flex", alignItems: "baseline", gap: "0.5rem", padding: "0.25rem 0", borderBottom: "1px solid #f0f0f0" }}>
                          <span style={{ fontSize: "0.78rem", color: "#555", minWidth: "200px", flexShrink: 0 }}>{feature}</span>
                          <div style={{ display: "flex", flexWrap: "wrap", gap: "0.25rem" }}>
                            {values.map((v) => {
                              const active = isFilterActive(feature, v.value);
                              return (
                                <span
                                  key={v.value}
                                  onClick={() => toggleFilter(feature, v.value)}
                                  style={{
                                    cursor: "pointer", fontSize: "0.78rem", padding: "0.1rem 0.5rem",
                                    borderRadius: "10px", border: "1px solid",
                                    borderColor: active ? "#2d6a4f" : "#ddd",
                                    background: active ? "#d8f3dc" : "#fafafa",
                                    color: active ? "#1b4332" : "#333",
                                    whiteSpace: "nowrap",
                                  }}
                                >
                                  {v.value} <span style={{ color: "#999", fontSize: "0.7rem" }}>{v.species_count}</span>
                                </span>
                              );
                            })}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {species.length > 0 && filters.length === 0 && (
                <div style={{ marginTop: "1.5rem" }}>
                  <h3 style={{ marginBottom: "0.75rem", fontSize: "1rem" }}>
                    Species observed on this trail ({species.length})
                  </h3>
                  <ul style={{ columns: 2, columnGap: "2rem", padding: 0, margin: 0, listStyle: "none", fontSize: "0.85rem" }}>
                    {species.map((name) => (
                      <li key={name} style={{ padding: "0.2rem 0", breakInside: "avoid" }}>
                        <Link to={`/species/${encodeURIComponent(name)}`} style={{ fontStyle: "italic", color: "#2d6a4f" }}>
                          {name}
                        </Link>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {filters.length > 0 && (
                <div style={{
                  position: "fixed", bottom: 0, left: 0, right: "25vw",
                  height: "33vh",
                  background: "#fff",
                  borderTop: "2px solid #2d6a4f",
                  boxShadow: "0 -4px 16px rgba(0,0,0,0.08)",
                  display: "flex", flexDirection: "column",
                  zIndex: 1000,
                }}>
                  <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", padding: "0.4rem 1.5rem", borderBottom: "1px solid #e0e0e0", flexShrink: 0 }}>
                    <span style={{ fontWeight: 600, fontSize: "0.85rem" }}>
                      Matching species
                      {filteredData && <span style={{ color: "#666", fontWeight: "normal" }}> ({filteredData.total})</span>}
                    </span>
                    <span style={{ color: "#bbb", margin: "0 0.25rem" }}>·</span>
                    <div style={{ display: "flex", flexWrap: "wrap", gap: "0.3rem", flex: 1 }}>
                      {filters.map((f) => (
                        <span
                          key={`${f.feature}:${f.value}`}
                          style={{
                            display: "inline-flex", alignItems: "center", gap: "0.25rem",
                            background: "#d8f3dc", border: "1px solid #2d6a4f",
                            borderRadius: "10px", padding: "0.1rem 0.5rem",
                            fontSize: "0.75rem", color: "#1b4332",
                          }}
                        >
                          <span style={{ color: "#555", fontSize: "0.68rem" }}>{f.feature}:</span>{f.value}
                          <button
                            onClick={() => setFilters((prev) => prev.filter((x) => !(x.feature === f.feature && x.value === f.value)))}
                            style={{ background: "none", border: "none", cursor: "pointer", padding: 0, color: "#2d6a4f", fontWeight: 700, fontSize: "0.85rem", lineHeight: 1 }}
                          >×</button>
                        </span>
                      ))}
                    </div>
                    <button
                      onClick={() => setFilters([])}
                      style={{ fontSize: "0.75rem", color: "#888", background: "none", border: "none", cursor: "pointer", textDecoration: "underline", flexShrink: 0 }}
                    >clear all</button>
                  </div>
                  <div style={{ flex: 1, overflowY: "auto", padding: "0.5rem 1.5rem" }}>
                    {loadingFiltered ? (
                      <LoadingState message="Filtering…" />
                    ) : species.length === 0 ? (
                      <p style={{ color: "#888", fontSize: "0.85rem", margin: 0 }}>No species match all selected filters.</p>
                    ) : (
                      <div style={{ columns: "4 180px", gap: "1rem" }}>
                        {species.map((name) => (
                          <div key={name} style={{ padding: "0.15rem 0", fontSize: "0.82rem", breakInside: "avoid" }}>
                            <Link to={`/species/${encodeURIComponent(name)}`} style={{ fontStyle: "italic", color: "#2d6a4f" }}>
                              {name}
                            </Link>
                          </div>
                        ))}
                      </div>
                    )}
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
