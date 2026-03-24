import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { getFeatures, getSpeciesByFeature } from "../api/co_occurrence";
import { LoadingState } from "../components/LoadingState";

export function FeaturesPage() {
  const [selected, setSelected] = useState<{ feature: string; value: string } | null>(null);

  const { data, isLoading } = useQuery({
    queryKey: ["features"],
    queryFn: getFeatures,
  });

  const { data: speciesData, isLoading: speciesLoading } = useQuery({
    queryKey: ["species-by-feature", selected?.feature, selected?.value],
    queryFn: () => getSpeciesByFeature(selected!.feature, selected!.value),
    enabled: !!selected,
  });

  if (isLoading) return <LoadingState message="Loading features..." />;

  const features = data?.data ?? {};

  return (
    <div>
      <Link to="/">&larr; Home</Link>
      <h2>Species by Features</h2>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "1.5rem" }}>
        {Object.entries(features).map(([feature, values]) => (
          <div key={feature}>
            <h3 style={{ textTransform: "capitalize" }}>{feature.replace("_", " ")}</h3>
            <ul style={{ listStyle: "none", padding: 0 }}>
              {values.map((v) => (
                <li
                  key={v.value}
                  onClick={() => setSelected({ feature, value: v.value })}
                  style={{
                    padding: "0.4rem 0.6rem", cursor: "pointer", borderRadius: "4px",
                    background: selected?.feature === feature && selected?.value === v.value ? "#d8f3dc" : "transparent",
                  }}
                  onMouseEnter={e => e.currentTarget.style.background = e.currentTarget.style.background || "#f0f0f0"}
                  onMouseLeave={e => {
                    if (!(selected?.feature === feature && selected?.value === v.value))
                      e.currentTarget.style.background = "transparent";
                  }}
                >
                  {v.value} <span style={{ color: "#999" }}>({v.species_count})</span>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>

      {selected && (
        <div style={{ marginTop: "2rem" }}>
          <h3>
            Species with <em>{selected.value}</em>
            {speciesData && <span style={{ color: "#666", fontWeight: "normal" }}> ({speciesData.total})</span>}
          </h3>
          {speciesLoading ? (
            <LoadingState message="Loading species..." />
          ) : (
            <ul style={{ columns: 3, listStyle: "none", padding: 0 }}>
              {speciesData?.data.map((s) => (
                <li key={s.species} style={{ padding: "0.2rem 0" }}>
                  <Link to={`/species/${encodeURIComponent(s.species)}`}>
                    <em>{s.species}</em>
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}
