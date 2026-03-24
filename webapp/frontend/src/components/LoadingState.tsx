export function LoadingState({ message = "Loading..." }: { message?: string }) {
  return (
    <div style={{ display: "flex", justifyContent: "center", alignItems: "center", padding: "4rem" }}>
      <div style={{ textAlign: "center" }}>
        <div className="spinner" />
        <p style={{ marginTop: "1rem", color: "#666" }}>{message}</p>
      </div>
    </div>
  );
}
