import { useState, useRef, useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { getSpeciesList } from "../api/co_occurrence";

export function SpeciesSearch() {
  const [query, setQuery] = useState("");
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();

  const { data } = useQuery({
    queryKey: ["species-list"],
    queryFn: getSpeciesList,
    staleTime: 5 * 60 * 1000,
  });

  const filtered = data?.data
    .filter((s) => s.toLowerCase().includes(query.toLowerCase()))
    .slice(0, 10) ?? [];

  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  return (
    <div ref={ref} style={{ position: "relative" }}>
      <input
        type="text"
        placeholder="Search species..."
        value={query}
        onChange={(e) => { setQuery(e.target.value); setOpen(true); }}
        onFocus={() => setOpen(true)}
        style={{ padding: "0.4rem 0.8rem", width: "250px", borderRadius: "4px", border: "1px solid #ccc" }}
      />
      {open && query.length > 1 && filtered.length > 0 && (
        <ul style={{
          position: "absolute", top: "100%", left: 0, right: 0,
          background: "#fff", border: "1px solid #ccc", borderRadius: "4px",
          listStyle: "none", margin: 0, padding: 0, zIndex: 10, maxHeight: "300px", overflow: "auto",
        }}>
          {filtered.map((s) => (
            <li
              key={s}
              onClick={() => { navigate(`/species/${encodeURIComponent(s)}`); setOpen(false); setQuery(""); }}
              style={{ padding: "0.4rem 0.8rem", cursor: "pointer" }}
              onMouseEnter={(e) => (e.currentTarget.style.background = "#f0f0f0")}
              onMouseLeave={(e) => (e.currentTarget.style.background = "#fff")}
            >
              <em>{s}</em>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
