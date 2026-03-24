import { useEffect, useMemo } from "react";
import { MapContainer, TileLayer, CircleMarker, Polygon, Popup, useMap } from "react-leaflet";
import { latLngBounds, type LatLngBoundsExpression } from "leaflet";
import { cellToBoundary } from "h3-js";
import "leaflet/dist/leaflet.css";
import type { ObservationPoint, CoOccurringObservation, H3CellInfo } from "../types";

const DEFAULT_CENTER: [number, number] = [41.245, -73.59];

interface Props {
  observations?: ObservationPoint[];
  coOccurringObservations?: CoOccurringObservation[];
  h3Cells?: H3CellInfo[];
}

function FitBounds({ bounds }: { bounds: LatLngBoundsExpression | null }) {
  const map = useMap();
  useEffect(() => {
    if (bounds) map.fitBounds(bounds, { padding: [30, 30] });
  }, [map, bounds]);
  return null;
}

export function ObservationMap({ observations = [], coOccurringObservations = [], h3Cells = [] }: Props) {
  const bounds = useMemo(() => {
    const points: [number, number][] = [];
    observations.forEach((obs) => points.push([obs.lat, obs.lon]));
    coOccurringObservations.forEach((obs) => points.push([obs.lat, obs.lon]));
    h3Cells.forEach((cell) => {
      cellToBoundary(cell.h3_index).forEach(([lat, lng]) => points.push([lat, lng]));
    });
    if (points.length === 0) return null;
    return latLngBounds(points);
  }, [observations, coOccurringObservations, h3Cells]);

  return (
    <MapContainer
      center={DEFAULT_CENTER}
      zoom={13}
      style={{ height: "400px", width: "100%", borderRadius: "8px", marginBottom: "1rem" }}
    >
      <FitBounds bounds={bounds} />
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />

      {/* H3 cells — yellow */}
      {h3Cells.map((cell) => {
        const boundary = cellToBoundary(cell.h3_index);
        const positions: [number, number][] = boundary.map(([lat, lng]) => [lat, lng]);
        return (
          <Polygon
            key={cell.h3_index}
            positions={positions}
            pathOptions={{
              color: "#e9c46a",
              fillColor: "#f4e285",
              fillOpacity: 0.3,
              weight: 2,
            }}
          >
            <Popup>
              Co-occurrences: {cell.co_occurrence_count}
            </Popup>
          </Polygon>
        );
      })}

      {/* Co-occurring observations — green */}
      {coOccurringObservations.map((obs) => (
        <CircleMarker
          key={`co-${obs.inat_id}`}
          center={[obs.lat, obs.lon]}
          radius={5}
          pathOptions={{ color: "#2d6a4f", fillColor: "#40916c", fillOpacity: 0.7, weight: 1 }}
        >
          <Popup>
            <em>{obs.species_name}</em><br />
            <strong>{obs.date}</strong><br />
            <a href={`https://www.inaturalist.org/observations/${obs.inat_id}`} target="_blank" rel="noreferrer">
              iNat #{obs.inat_id}
            </a>
          </Popup>
        </CircleMarker>
      ))}

      {/* Species observations — red */}
      {observations.map((obs) => (
        <CircleMarker
          key={`sp-${obs.inat_id}`}
          center={[obs.lat, obs.lon]}
          radius={5}
          pathOptions={{ color: "#d62828", fillColor: "#e76f51", fillOpacity: 0.8, weight: 1 }}
        >
          <Popup>
            <strong>{obs.date}</strong><br />
            <a href={`https://www.inaturalist.org/observations/${obs.inat_id}`} target="_blank" rel="noreferrer">
              iNat #{obs.inat_id}
            </a>
          </Popup>
        </CircleMarker>
      ))}
    </MapContainer>
  );
}
