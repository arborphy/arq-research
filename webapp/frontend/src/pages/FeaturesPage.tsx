import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { getFeatures, filterSpeciesByFeatures } from "../api/co_occurrence";
import { LoadingState } from "../components/LoadingState";

type FilterItem = { feature: string; value: string };

const PANEL_HEIGHT = "33vh";

export function FeaturesPage() {
  const [filters, setFilters] = useState<FilterItem[]>([]);

  const { data, isLoading } = useQuery({
    queryKey: ["features"],
    queryFn: getFeatures,
  });

  const { data: speciesData, isLoading: speciesLoading } = useQuery({
    queryKey: ["species-by-filters", filters],
    queryFn: () => filterSpeciesByFeatures(filters),
    enabled: filters.length > 0,
  });

  if (isLoading) return <LoadingState message="Loading features..." />;

  const features = data?.data ?? {};

  function isActive(feature: string, value: string) {
    return filters.some((f) => f.feature === feature && f.value === value);
  }

  function toggleFilter(feature: string, value: string) {
    setFilters((prev) =>
      isActive(feature, value)
        ? prev.filter((f) => !(f.feature === feature && f.value === value))
        : [...prev, { feature, value }]
    );
  }

  function removeFilter(f: FilterItem) {
    setFilters((prev) => prev.filter((x) => !(x.feature === f.feature && x.value === f.value)));
  }

  return (
    <div style={{ paddingBottom: filters.length > 0 ? PANEL_HEIGHT : 0 }}>
      <Link to="/">&larr; Home</Link>
      <h2>Species by Features</h2>

      <div style={{ display: "flex", flexDirection: "column", gap: "0.25rem" }}>
        {Object.entries(features).map(([feature, values]) => (
          <div
            key={feature}
            style={{ display: "flex", alignItems: "baseline", gap: "0.5rem", padding: "0.3rem 0", borderBottom: "1px solid #f0f0f0" }}
          >
            <span style={{ fontSize: "0.78rem", color: "#555", minWidth: "220px", flexShrink: 0 }}>
              {feature}
            </span>
            <div style={{ display: "flex", flexWrap: "wrap", gap: "0.25rem" }}>
              {values.map((v) => {
                const active = isActive(feature, v.value);
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

      {filters.length > 0 && (
        <div style={{
          position: "fixed", bottom: 0, left: 0, right: "25vw",
          height: PANEL_HEIGHT,
          background: "#fff",
          borderTop: "2px solid #2d6a4f",
          boxShadow: "0 -4px 16px rgba(0,0,0,0.08)",
          display: "flex",
          flexDirection: "column",
          zIndex: 100,
        }}>
          {/* Panel header */}
          <div style={{
            display: "flex", alignItems: "center", gap: "0.5rem",
            padding: "0.4rem 1.5rem",
            borderBottom: "1px solid #e0e0e0",
            flexShrink: 0,
          }}>
            <span style={{ fontWeight: 600, fontSize: "0.85rem" }}>
              Matching species
              {speciesData && (
                <span style={{ color: "#666", fontWeight: "normal" }}> ({speciesData.total})</span>
              )}
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
                    onClick={() => removeFilter(f)}
                    style={{ background: "none", border: "none", cursor: "pointer", padding: 0, color: "#2d6a4f", fontWeight: 700, fontSize: "0.85rem", lineHeight: 1 }}
                  >×</button>
                </span>
              ))}
            </div>
            <button
              onClick={() => setFilters([])}
              style={{ fontSize: "0.75rem", color: "#888", background: "none", border: "none", cursor: "pointer", textDecoration: "underline", flexShrink: 0 }}
            >
              clear all
            </button>
          </div>

          {/* Species list */}
          <div style={{ flex: 1, overflowY: "auto", padding: "0.5rem 1.5rem" }}>
            {speciesLoading ? (
              <LoadingState message="Filtering..." />
            ) : speciesData?.total === 0 ? (
              <p style={{ color: "#888", fontSize: "0.85rem", margin: 0 }}>No species match all selected filters.</p>
            ) : (
              <div style={{ columns: "4 180px", gap: "1rem" }}>
                {speciesData?.data.map((s) => (
                  <div key={s.species} style={{ padding: "0.15rem 0", fontSize: "0.82rem", breakInside: "avoid" }}>
                    <Link to={`/species/${encodeURIComponent(s.species)}`}>
                      <em>{s.species}</em>
                    </Link>
                    {s.sources.map((src) => (
                      <span key={src} style={{
                        marginLeft: "0.3rem", fontSize: "0.65rem", color: "#888",
                        background: "#f0f0f0", borderRadius: "8px", padding: "0 0.35rem",
                      }}>{src}</span>
                    ))}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
