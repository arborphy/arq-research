import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { getDebugQueries } from "../api/co_occurrence";

export function DebugPanel() {
  const [visible, setVisible] = useState(true);

  const { data } = useQuery({
    queryKey: ["debug-queries"],
    queryFn: () => getDebugQueries(30),
    refetchInterval: 3000,
  });

  return (
    <div style={{
      position: "fixed", top: 0, right: 0, height: "100vh",
      width: visible ? "25vw" : "auto",
      background: "#fafafa", color: "#333",
      borderLeft: "1px solid #e0e0e0",
      display: "flex", flexDirection: "column",
      zIndex: 100,
      transition: "width 0.2s",
    }}>
      <button
        onClick={() => setVisible(!visible)}
        style={{
          background: "#2d6a4f", color: "#fff", border: "none",
          padding: "0.4rem 0.8rem", cursor: "pointer",
          fontSize: "0.8rem", alignSelf: "flex-start", margin: "0.5rem",
          borderRadius: "4px",
        }}
      >
        {visible ? "Hide" : "RAI"}
      </button>

      {visible && (
        <div style={{ flex: 1, overflow: "auto", padding: "0 0.75rem 0.75rem" }}>
          <h4 style={{ margin: "0 0 0.5rem", color: "#2d6a4f" }}>RAI Queries</h4>
          {(data?.data ?? []).slice().reverse().map((q, i) => (
            <div key={q.id ?? i} style={{
              marginBottom: "0.75rem", padding: "0.5rem",
              background: "#fff", borderRadius: "4px",
              border: "1px solid #e0e0e0",
              fontSize: "0.75rem",
            }}>
              <div style={{ color: "#999", marginBottom: "0.25rem" }}>
                {q.file}:{q.line} &middot; {q.timestamp ? new Date(q.timestamp).toLocaleTimeString() : ""}
              </div>
              <pre style={{
                margin: 0, whiteSpace: "pre-wrap", wordBreak: "break-word",
                color: "#555", fontFamily: "monospace", fontSize: "0.7rem",
              }}>
                {q.source}
              </pre>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
