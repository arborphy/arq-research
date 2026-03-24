import { useState, useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { MapContainer, TileLayer, Polygon } from "react-leaflet";
import { cellToBoundary } from "h3-js";
import "leaflet/dist/leaflet.css";
import { getCells, getVisibleSpecies } from "../api/co_occurrence";
import { LoadingState } from "../components/LoadingState";

const CENTER: [number, number] = [41.245, -73.59];

function getDayOfYear(dateStr: string): number {
  const d = new Date(dateStr + "T00:00:00");
  const start = new Date(d.getFullYear(), 0, 0);
  return Math.floor((d.getTime() - start.getTime()) / 86400000);
}

export function FieldGuidePage() {
  const today = new Date().toISOString().slice(0, 10);
  const [date, setDate] = useState(today);
  const [selectedCell, setSelectedCell] = useState<string | null>(null);

  const dayOfYear = useMemo(() => getDayOfYear(date), [date]);

  const { data: cellsData, isLoading: cellsLoading } = useQuery({
    queryKey: ["cells-on-day", dayOfYear],
    queryFn: () => getCells(dayOfYear),
  });

  const { data: visibleData, isLoading: visibleLoading } = useQuery({
    queryKey: ["visible", selectedCell, dayOfYear],
    queryFn: () => getVisibleSpecies(selectedCell!, dayOfYear),
    enabled: !!selectedCell,
  });

  const cells = cellsData?.data ?? [];

  return (
    <div>
      <Link to="/">&larr; Home</Link>
      <h2>Field Guide</h2>

      <div style={{ display: "flex", alignItems: "center", gap: "1rem", marginBottom: "1rem" }}>
        <label>
          Date:{" "}
          <input
            type="date"
            value={date}
            onChange={(e) => { setDate(e.target.value); setSelectedCell(null); }}
            style={{ padding: "0.3rem 0.5rem", borderRadius: "4px", border: "1px solid #ccc" }}
          />
        </label>
        <span style={{ color: "#888", fontSize: "0.85rem" }}>
          Day {dayOfYear} &middot; {cells.length} cells with observations
        </span>
      </div>

      {cellsLoading ? (
        <LoadingState message="Finding cells with observations..." />
      ) : (
        <MapContainer center={CENTER} zoom={13} style={{ height: "450px", width: "100%", borderRadius: "8px", marginBottom: "1rem" }}>
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          {cells.map((cell) => {
            const boundary = cellToBoundary(cell.h3_index);
            const positions: [number, number][] = boundary.map(([lat, lng]) => [lat, lng]);
            const isSelected = cell.h3_index === selectedCell;
            return (
              <Polygon
                key={cell.h3_index}
                positions={positions}
                pathOptions={{
                  color: isSelected ? "#d62828" : "#2d6a4f",
                  fillColor: isSelected ? "#e76f51" : "#40916c",
                  fillOpacity: isSelected ? 0.5 : 0.25,
                  weight: isSelected ? 3 : 1,
                }}
                eventHandlers={{ click: () => setSelectedCell(cell.h3_index) }}
              />
            );
          })}
        </MapContainer>
      )}

      {selectedCell && (
        <div>
          <h3>
            Species visible on day {dayOfYear}
            {visibleData && <span style={{ color: "#666", fontWeight: "normal" }}> ({visibleData.total} observations)</span>}
          </h3>

          {visibleLoading ? (
            <LoadingState message="Querying knowledge graph..." />
          ) : visibleData?.data.length === 0 ? (
            <p style={{ color: "#888" }}>No species found.</p>
          ) : (
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(180px, 1fr))", gap: "1rem" }}>
              {visibleData?.data.map((s, i) => (
                <Link
                  key={`${s.inat_id}-${i}`}
                  to={`/species/${encodeURIComponent(s.species)}`}
                  style={{ textDecoration: "none", color: "inherit" }}
                >
                  <div style={{
                    border: "1px solid #e0e0e0", borderRadius: "8px", overflow: "hidden",
                    transition: "box-shadow 0.2s",
                  }}
                    onMouseEnter={(e) => e.currentTarget.style.boxShadow = "0 2px 8px rgba(0,0,0,0.12)"}
                    onMouseLeave={(e) => e.currentTarget.style.boxShadow = "none"}
                  >
                    {s.image_url && (
                      <img
                        src={s.image_url}
                        alt={s.species}
                        style={{ width: "100%", height: "140px", objectFit: "cover" }}
                        loading="lazy"
                      />
                    )}
                    <div style={{ padding: "0.5rem" }}>
                      <div style={{ fontSize: "0.85rem", fontStyle: "italic", color: "#2d6a4f" }}>{s.species}</div>
                      <div style={{ fontSize: "0.75rem", color: "#888" }}>{s.date}</div>
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
