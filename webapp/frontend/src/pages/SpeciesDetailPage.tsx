import { useState } from "react";
import { useParams, Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { createColumnHelper } from "@tanstack/react-table";
import { getForSpecies, getSpeciesObservations, getSpeciesCoOccurrenceCells, getCoOccurringObservations, getSharedFeatures, getNewcombKey } from "../api/co_occurrence";
import { DataTable } from "../components/DataTable";
import { LoadingState } from "../components/LoadingState";
import { ObservationMap } from "../components/ObservationMap";
import type { SpeciesCoOccurrence, SharedFeature } from "../types";

const col = createColumnHelper<SpeciesCoOccurrence>();
const fcol = createColumnHelper<SharedFeature>();

const columns = [
  col.accessor("co_occurring_species", {
    header: "Co-Occurring Species",
    cell: (info) => (
      <Link to={`/species/${encodeURIComponent(info.getValue())}`}>
        <em>{info.getValue()}</em>
      </Link>
    ),
  }),
];

const featureColumns = [
  fcol.accessor("feature", { header: "Feature" }),
  fcol.accessor("value", { header: "Value" }),
  fcol.accessor("species_count", { header: "Species with Trait" }),
];

const GRANULARITIES = [
  { value: "day", label: "Same Day" },
  { value: "week", label: "Same Week" },
  { value: "month", label: "Same Month" },
  { value: "quarter", label: "Same Quarter" },
];

export function SpeciesDetailPage() {
  const { name } = useParams<{ name: string }>();
  const decodedName = decodeURIComponent(name ?? "");
  const [granularity, setGranularity] = useState("day");

  const { data, isLoading, error } = useQuery({
    queryKey: ["species", decodedName, granularity],
    queryFn: () => getForSpecies(decodedName, granularity),
    enabled: !!decodedName,
  });

  const { data: obsData } = useQuery({
    queryKey: ["species-obs", decodedName],
    queryFn: () => getSpeciesObservations(decodedName),
    enabled: !!decodedName,
  });

  const { data: cellData } = useQuery({
    queryKey: ["species-cells", decodedName],
    queryFn: () => getSpeciesCoOccurrenceCells(decodedName),
    enabled: !!decodedName,
  });

  const { data: coObsData } = useQuery({
    queryKey: ["species-co-obs", decodedName],
    queryFn: () => getCoOccurringObservations(decodedName),
    enabled: !!decodedName,
  });

  const { data: featData } = useQuery({
    queryKey: ["species-shared-features", decodedName],
    queryFn: () => getSharedFeatures(decodedName),
    enabled: !!decodedName,
  });

  const { data: keyData } = useQuery({
    queryKey: ["newcomb-key", decodedName],
    queryFn: () => getNewcombKey(decodedName),
    enabled: !!decodedName,
  });

  const newcombKey = keyData?.data;
  const photos = (obsData?.data ?? []).filter((o) => o.image_url);

  if (isLoading) return <LoadingState message={`Loading co-occurrences for ${decodedName}...`} />;
  if (error) return (
    <div>
      <Link to="/">&larr; Back</Link>
      <p style={{ color: "red", marginTop: "1rem" }}>
        No co-occurrences found for <em>{decodedName}</em>
      </p>
    </div>
  );

  return (
    <div>
      <Link to="/">&larr; Back</Link>
      <h2><em>{decodedName}</em></h2>

      {newcombKey && (
        <div style={{
          display: "flex", gap: "1.5rem", padding: "0.75rem 1rem",
          background: "#f0faf4", borderRadius: "6px", marginBottom: "1rem",
          fontSize: "0.85rem", alignItems: "center",
        }}>
          <span><strong>Newcomb Group {newcombKey.group_number}</strong></span>
          <span>{newcombKey.flower_type}</span>
          <span>{newcombKey.plant_type}</span>
          <span>{newcombKey.leaf_type}</span>
        </div>
      )}

      <div style={{ display: "flex", gap: "1.5rem" }}>
        {/* Main content */}
        <div style={{ flex: 1, minWidth: 0 }}>
          <ObservationMap
            observations={obsData?.data}
            coOccurringObservations={coObsData?.data}
            h3Cells={cellData?.data}
          />

          <div style={{ display: "flex", gap: "1rem", fontSize: "0.85rem", marginBottom: "1rem" }}>
            <span><span style={{ color: "#d62828" }}>{"\u25CF"}</span> Observations ({obsData?.total ?? 0})</span>
            <span><span style={{ color: "#40916c" }}>{"\u25CF"}</span> Co-occurring ({coObsData?.total ?? 0})</span>
            <span><span style={{ color: "#e9c46a" }}>{"\u25A0"}</span> H3 cells ({cellData?.total ?? 0})</span>
          </div>

          {(featData?.data?.length ?? 0) > 0 && (
            <>
              <h3>Shared Traits Among Co-Occurring Species</h3>
              <DataTable data={featData?.data ?? []} columns={featureColumns} />
            </>
          )}

          <div style={{ display: "flex", alignItems: "center", gap: "1rem", marginTop: "2rem" }}>
            <h3 style={{ margin: 0 }}>{data?.total ?? 0} co-occurring species</h3>
            <div style={{ display: "flex", gap: "0.25rem" }}>
              {GRANULARITIES.map((g) => (
                <button
                  key={g.value}
                  onClick={() => setGranularity(g.value)}
                  style={{
                    padding: "0.3rem 0.6rem", borderRadius: "4px", cursor: "pointer",
                    border: granularity === g.value ? "2px solid #2d6a4f" : "1px solid #ccc",
                    background: granularity === g.value ? "#d8f3dc" : "#fff",
                    fontSize: "0.8rem", color: "#333",
                  }}
                >
                  {g.label}
                </button>
              ))}
            </div>
          </div>
          <DataTable data={data?.data ?? []} columns={columns} />
        </div>

        {/* Photo gallery */}
        {photos.length > 0 && (
          <div style={{ width: "220px", flexShrink: 0 }}>
            <h3 style={{ fontSize: "0.9rem", marginTop: 0 }}>Photos ({photos.length})</h3>
            <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem", maxHeight: "80vh", overflow: "auto" }}>
              {photos.map((obs) => (
                <a
                  key={obs.inat_id}
                  href={`https://www.inaturalist.org/observations/${obs.inat_id}`}
                  target="_blank"
                  rel="noreferrer"
                >
                  <img
                    src={obs.image_url}
                    alt={`Observation ${obs.inat_id}`}
                    style={{ width: "100%", borderRadius: "4px", display: "block" }}
                    loading="lazy"
                  />
                  <span style={{ fontSize: "0.7rem", color: "#666" }}>{obs.date}</span>
                </a>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
