import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  getPlaceHierarchy, getWithinPairs,
  LOCATION_LEVELS, CONTAINER_LEVELS, type PlaceLevel, type ContainerLevel, type SubjectLevel,
} from "../api/spatial";
import { LoadingState } from "../components/LoadingState";

const SUBJECT_LEVELS: SubjectLevel[] = ["Observation", ...LOCATION_LEVELS];

function PlaceHierarchyPanel({ places, isLoading }: { places: PlaceLevel[]; isLoading: boolean }) {
  return (
    <div style={{ marginBottom: "2rem" }}>
      <h3 style={{ margin: "0 0 0.5rem" }}>Named Places Hierarchy</h3>
      <p style={{ color: "#555", fontSize: "0.85rem", marginBottom: "1rem" }}>
        Each observation is <code>located_in</code> the park directly (via <code>Observation.area</code>).
        The park is <code>located_in</code> the county, which is <code>located_in</code> the state, etc.
        The <code>direct</code> count is only non-zero at the Park level — higher levels require multi-hop joins.
      </p>
      {isLoading ? (
        <LoadingState message="Loading place hierarchy…" />
      ) : places.length === 0 ? (
        <p style={{ color: "#999", fontStyle: "italic" }}>No place data loaded yet.</p>
      ) : (
        <div style={{ display: "flex", flexDirection: "column" }}>
          {places.map((p, i) => (
            <div key={p.level}>
              <div style={{
                display: "flex", alignItems: "center", gap: "1rem",
                background: i === 0 ? "#f0faf4" : "#fafafa",
                border: "1px solid #d8f3dc", borderRadius: "8px",
                padding: "0.75rem 1rem",
              }}>
                <div style={{ flex: 1 }}>
                  <div style={{ fontWeight: 600, fontSize: "0.95rem" }}>{p.name}</div>
                  <div style={{ fontSize: "0.78rem", color: "#888" }}>{p.level}</div>
                </div>
                <div style={{ textAlign: "right" }}>
                  <div style={{ fontSize: "0.8rem", color: "#888" }}>within (chain)</div>
                  <div style={{ fontWeight: 700, color: "#2d6a4f", fontSize: "1.1rem" }}>
                    {p.within.toLocaleString()} obs
                  </div>
                </div>
                <div style={{ textAlign: "right", minWidth: "90px" }}>
                  <div style={{ fontSize: "0.8rem", color: "#888" }}>located_in (direct)</div>
                  <div style={{ fontWeight: 700, color: p.direct > 0 ? "#2d6a4f" : "#ccc", fontSize: "1.1rem" }}>
                    {p.direct > 0 ? p.direct.toLocaleString() : "0"} obs
                  </div>
                </div>
              </div>
              {i < places.length - 1 && (
                <div style={{ padding: "0.15rem 0 0.15rem 1.4rem", color: "#52b788", fontSize: "0.8rem" }}>
                  ↓ <code style={{ fontSize: "0.75rem" }}>located_in</code>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

const SELECT_STYLE: React.CSSProperties = {
  padding: "0.4rem 0.75rem", borderRadius: "6px",
  border: "1px solid #ccc", fontSize: "0.95rem",
};

function WithinExplorerPanel() {
  const [subject, setSubject] = useState<SubjectLevel>("Park");
  const [container, setContainer] = useState<ContainerLevel>("Country");

  const { data, isLoading, isFetching } = useQuery({
    queryKey: ["spatial-within", subject, container],
    queryFn: () => getWithinPairs(subject, container),
  });

  const pairs = data?.data ?? [];
  const hasResult = !isLoading && !isFetching;

  return (
    <div>
      <h3 style={{ margin: "0 0 0.5rem" }}>within( ) Explorer</h3>
      <p style={{ color: "#555", fontSize: "0.85rem", marginBottom: "1rem" }}>
        Select two concept types and see every pair where{" "}
        <code>within(subject, container)</code> holds.
      </p>

      <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", marginBottom: "1.25rem", flexWrap: "wrap" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
          <label style={{ fontWeight: 600, fontSize: "0.9rem" }}>subject</label>
          <select style={SELECT_STYLE} value={subject} onChange={(e) => setSubject(e.target.value as SubjectLevel)}>
            {SUBJECT_LEVELS.map((l) => <option key={l} value={l}>{l}</option>)}
          </select>
        </div>
        <span style={{ fontFamily: "monospace", color: "#2d6a4f", fontWeight: 700 }}>within</span>
        <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
          <label style={{ fontWeight: 600, fontSize: "0.9rem" }}>container</label>
          <select style={SELECT_STYLE} value={container} onChange={(e) => setContainer(e.target.value as ContainerLevel)}>
            {CONTAINER_LEVELS.map((l) => <option key={l} value={l}>{l}</option>)}
          </select>
        </div>
      </div>

      {isLoading || isFetching ? (
        <LoadingState message="Querying…" />
      ) : (
        <div style={{
          background: pairs.length > 0 ? "#f0faf4" : "#fafafa",
          border: `1px solid ${pairs.length > 0 ? "#52b788" : "#e0e0e0"}`,
          borderRadius: "8px", padding: "0.9rem 1.1rem",
        }}>
          {pairs.length === 0 ? (
            <p style={{ margin: 0, color: "#999", fontStyle: "italic", fontSize: "0.9rem" }}>
              No results — <code>within({subject}, {container})</code> holds for 0 pairs.
            </p>
          ) : (
            <>
              <div style={{ fontSize: "0.8rem", color: "#555", marginBottom: "0.6rem" }}>
                <code>within({subject}, {container})</code> → {pairs.length} result{pairs.length !== 1 ? "s" : ""}
              </div>
              {subject === "Observation" ? (
                <table style={{ borderCollapse: "collapse", width: "100%", fontSize: "0.9rem" }}>
                  <thead>
                    <tr>
                      <th style={{ textAlign: "left", padding: "0.3rem 0.75rem 0.3rem 0", color: "#555", fontWeight: 600 }}>
                        {container}
                      </th>
                      <th style={{ textAlign: "right", padding: "0.3rem 0 0.3rem 0.75rem", color: "#555", fontWeight: 600 }}>
                        Observations
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {pairs.map((p, i) => (
                      <tr key={i} style={{ borderTop: "1px solid #e8f5e9" }}>
                        <td style={{ padding: "0.35rem 0.75rem 0.35rem 0", fontWeight: 500 }}>{p.container}</td>
                        <td style={{ padding: "0.35rem 0 0.35rem 0.75rem", textAlign: "right", fontWeight: 700, color: "#2d6a4f" }}>
                          {p.count?.toLocaleString()}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : (
                <table style={{ borderCollapse: "collapse", width: "100%", fontSize: "0.9rem" }}>
                  <thead>
                    <tr>
                      <th style={{ textAlign: "left", padding: "0.3rem 0.75rem 0.3rem 0", color: "#555", fontWeight: 600 }}>
                        {subject}
                      </th>
                      <th style={{ textAlign: "left", padding: "0.3rem 0.75rem", color: "#555", fontWeight: 600, width: "2rem" }} />
                      <th style={{ textAlign: "left", padding: "0.3rem 0 0.3rem 0.75rem", color: "#555", fontWeight: 600 }}>
                        {container}
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {pairs.map((p, i) => (
                      <tr key={i} style={{ borderTop: "1px solid #e8f5e9" }}>
                        <td style={{ padding: "0.35rem 0.75rem 0.35rem 0", fontWeight: 500 }}>{p.subject}</td>
                        <td style={{ padding: "0.35rem 0.75rem", color: "#52b788", fontFamily: "monospace", fontSize: "0.8rem" }}>within</td>
                        <td style={{ padding: "0.35rem 0 0.35rem 0.75rem" }}>{p.container}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </>
          )}
        </div>
      )}
      {hasResult && (
        <p style={{ marginTop: "0.5rem", fontSize: "0.78rem", color: "#888" }}>
          {pairs.length > 0
            ? `✓ within(${subject}, ${container}) is satisfied`
            : `✗ within(${subject}, ${container}) is not satisfied — try swapping subject and container`}
        </p>
      )}
    </div>
  );
}

export function SpatialPredicatePage() {
  const { data: placesData, isLoading: loadingPlaces } = useQuery({
    queryKey: ["spatial-places"],
    queryFn: getPlaceHierarchy,
  });

  return (
    <div>
      <h2>Spatial Predicates Explorer</h2>

      <div style={{
        background: "#f0faf4", borderRadius: "8px", padding: "1rem 1.25rem",
        marginBottom: "1.75rem", fontSize: "0.9rem", color: "#333", lineHeight: 1.6,
      }}>
        <p style={{ margin: "0 0 0.5rem" }}>
          <code>located_in</code> records a direct spatial placement.{" "}
          <code>within</code> closes over it transitively.
        </p>
        <p style={{ margin: 0 }}>
          Observations are placed directly in the park via <code>Observation.area</code>.
          The park, county, state, and country are linked by <code>located_in</code> facts.
          Only <code>within</code> reaches the full chain — <code>located_in</code> returns 0
          at every level above the park.
        </p>
      </div>

      <PlaceHierarchyPanel places={placesData?.data ?? []} isLoading={loadingPlaces} />

      <hr style={{ border: "none", borderTop: "1px solid #e8f5e9", margin: "0 0 2rem" }} />

      <WithinExplorerPanel />
    </div>
  );
}
