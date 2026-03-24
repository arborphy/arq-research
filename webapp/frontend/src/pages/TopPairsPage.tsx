import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { createColumnHelper } from "@tanstack/react-table";
import { getTopSpecies } from "../api/co_occurrence";
import { DataTable } from "../components/DataTable";
import { LoadingState } from "../components/LoadingState";
import type { SpeciesCoOccurrenceCount } from "../types";

const col = createColumnHelper<SpeciesCoOccurrenceCount>();

const columns = [
  col.accessor("co_occurring_count", { header: "Co-Occurring Species" }),
  col.accessor("species", {
    header: "Species",
    cell: (info) => (
      <Link to={`/species/${encodeURIComponent(info.getValue())}`}>
        <em>{info.getValue()}</em>
      </Link>
    ),
  }),
];

export function TopPairsPage() {
  const { data, isLoading, error } = useQuery({
    queryKey: ["top-species"],
    queryFn: () => getTopSpecies(100),
  });

  if (isLoading) return <LoadingState message="Loading co-occurrence data..." />;
  if (error) return <p style={{ color: "red" }}>Error: {(error as Error).message}</p>;

  return (
    <div>
      <h2>Species by Co-Occurrence Count</h2>
      <p style={{ color: "#666" }}>Showing species ranked by how many other species they co-occur with</p>
      <DataTable data={data?.data ?? []} columns={columns} />
    </div>
  );
}
