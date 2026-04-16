"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { EventTable } from "./EventTable";

export function LiveFeed() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["live-feed"],
    queryFn: () => api.events({ page: 1, page_size: 10 }),
    refetchInterval: 15_000,
  });

  if (isLoading) {
    return (
      <div className="space-y-2">
        {Array.from({ length: 5 }).map((_, i) => (
          <div key={i} className="h-10 rounded bg-gray-800 animate-pulse" />
        ))}
      </div>
    );
  }

  if (isError) {
    return (
      <div className="rounded-lg border border-red-800 bg-red-950 px-4 py-3 text-red-400 text-sm">
        Failed to load events — is the API running?
      </div>
    );
  }

  return <EventTable events={data?.items ?? []} />;
}
