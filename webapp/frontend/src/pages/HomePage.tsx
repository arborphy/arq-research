import { Link } from "react-router-dom";

export function HomePage() {
  return (
    <div>
      <h2>Arborphy Explorer</h2>
      <p style={{ color: "#666" }}>Explore plant species co-occurrence and traits</p>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1.5rem", marginTop: "2rem" }}>
        <Link to="/co-occurrence" style={{ textDecoration: "none" }}>
          <div style={{
            border: "2px solid #2d6a4f", borderRadius: "8px", padding: "1.5rem",
            transition: "background 0.2s",
          }}
            onMouseEnter={e => e.currentTarget.style.background = "#f0faf4"}
            onMouseLeave={e => e.currentTarget.style.background = "transparent"}
          >
            <h3 style={{ margin: "0 0 0.5rem", color: "#2d6a4f" }}>Species Co-Occurrence</h3>
            <p style={{ color: "#666", margin: 0 }}>
              Discover which species are observed together in the same area and time.
              View observations on a map with H3 spatial cells.
            </p>
          </div>
        </Link>
        <Link to="/features" style={{ textDecoration: "none" }}>
          <div style={{
            border: "2px solid #2d6a4f", borderRadius: "8px", padding: "1.5rem",
            transition: "background 0.2s",
          }}
            onMouseEnter={e => e.currentTarget.style.background = "#f0faf4"}
            onMouseLeave={e => e.currentTarget.style.background = "transparent"}
          >
            <h3 style={{ margin: "0 0 0.5rem", color: "#2d6a4f" }}>Species by Features</h3>
            <p style={{ color: "#666", margin: 0 }}>
              Browse species by botanical traits: flower type, plant type, and leaf type
              from the Newcomb wildflower guide.
            </p>
          </div>
        </Link>
        <Link to="/field-guide" style={{ textDecoration: "none" }}>
          <div style={{
            border: "2px solid #2d6a4f", borderRadius: "8px", padding: "1.5rem",
            transition: "background 0.2s",
          }}
            onMouseEnter={e => e.currentTarget.style.background = "#f0faf4"}
            onMouseLeave={e => e.currentTarget.style.background = "transparent"}
          >
            <h3 style={{ margin: "0 0 0.5rem", color: "#2d6a4f" }}>Field Guide</h3>
            <p style={{ color: "#666", margin: 0 }}>
              Pick a date and click a location on the map to see what species
              have been observed there on that day of year.
            </p>
          </div>
        </Link>
        <Link to="/community" style={{ textDecoration: "none" }}>
          <div style={{
            border: "2px solid #2d6a4f", borderRadius: "8px", padding: "1.5rem",
            transition: "background 0.2s",
          }}
            onMouseEnter={e => e.currentTarget.style.background = "#f0faf4"}
            onMouseLeave={e => e.currentTarget.style.background = "transparent"}
          >
            <h3 style={{ margin: "0 0 0.5rem", color: "#2d6a4f" }}>Community Graph</h3>
            <p style={{ color: "#666", margin: 0 }}>
              Visualize species co-occurrence as a network graph.
              Nodes are species, edges connect co-occurring pairs.
            </p>
          </div>
        </Link>
        <Link to="/predicates" style={{ textDecoration: "none" }}>
          <div style={{
            border: "2px solid #2d6a4f", borderRadius: "8px", padding: "1.5rem",
            transition: "background 0.2s",
          }}
            onMouseEnter={e => e.currentTarget.style.background = "#f0faf4"}
            onMouseLeave={e => e.currentTarget.style.background = "transparent"}
          >
            <h3 style={{ margin: "0 0 0.5rem", color: "#2d6a4f" }}>Global Predicates</h3>
            <p style={{ color: "#666", margin: 0 }}>
              See how a single predicate like <code>part_of</code> works across
              H3 cells, features, and taxonomy — one query, many concepts.
            </p>
          </div>
        </Link>
        <Link to="/ecosites" style={{ textDecoration: "none" }}>
          <div style={{
            border: "2px solid #2d6a4f", borderRadius: "8px", padding: "1.5rem",
            transition: "background 0.2s",
          }}
            onMouseEnter={e => e.currentTarget.style.background = "#f0faf4"}
            onMouseLeave={e => e.currentTarget.style.background = "transparent"}
          >
            <h3 style={{ margin: "0 0 0.5rem", color: "#2d6a4f" }}>Ecosite Explorer</h3>
            <p style={{ color: "#666", margin: 0 }}>
              Select an ecosite and see its H3 res-12 cell coverage on a map.
            </p>
          </div>
        </Link>
        <Link to="/trails" style={{ textDecoration: "none" }}>
          <div style={{
            border: "2px solid #2d6a4f", borderRadius: "8px", padding: "1.5rem",
            transition: "background 0.2s",
          }}
            onMouseEnter={e => e.currentTarget.style.background = "#f0faf4"}
            onMouseLeave={e => e.currentTarget.style.background = "transparent"}
          >
            <h3 style={{ margin: "0 0 0.5rem", color: "#2d6a4f" }}>Trail Explorer</h3>
            <p style={{ color: "#666", margin: 0 }}>
              Select a trail to see species observations recorded along it, matched by res-13 H3 cells.
            </p>
          </div>
        </Link>
      </div>
    </div>
  );
}
