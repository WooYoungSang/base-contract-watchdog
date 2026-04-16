"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api, type Severity } from "@/lib/api";
import { EventTable } from "@/components/EventTable";

const SEVERITIES: Severity[] = ["CRITICAL", "HIGH", "MEDIUM", "LOW"];
const EVENT_TYPES = ["ProxyUpgraded", "OwnershipTransferred", "AdminChanged", "RoleGranted", "RoleRevoked", "TimelockOperation"];

export default function EventsPage() {
  const [severity, setSeverity] = useState<Severity | "">("");
  const [eventType, setEventType] = useState("");
  const [contract, setContract] = useState("");
  const [page, setPage] = useState(1);

  const { data, isLoading, isError } = useQuery({
    queryKey: ["events", severity, eventType, contract, page],
    queryFn: () => api.events({ severity: severity || undefined, event_type: eventType || undefined, contract: contract || undefined, page, page_size: 20 }),
  });

  function resetFilters() {
    setSeverity("");
    setEventType("");
    setContract("");
    setPage(1);
  }

  return (
    <div className="mx-auto max-w-7xl px-4 py-10">
      <h1 className="text-2xl font-bold text-white mb-6">Security Events</h1>

      {/* Filters */}
      <div className="mb-6 flex flex-wrap gap-3">
        <select
          value={severity}
          onChange={(e) => { setSeverity(e.target.value as Severity | ""); setPage(1); }}
          className="rounded-lg border border-gray-700 bg-gray-900 px-3 py-2 text-sm text-gray-300 focus:outline-none focus:ring-1 focus:ring-red-500"
        >
          <option value="">All severities</option>
          {SEVERITIES.map((s) => <option key={s} value={s}>{s}</option>)}
        </select>

        <select
          value={eventType}
          onChange={(e) => { setEventType(e.target.value); setPage(1); }}
          className="rounded-lg border border-gray-700 bg-gray-900 px-3 py-2 text-sm text-gray-300 focus:outline-none focus:ring-1 focus:ring-red-500"
        >
          <option value="">All event types</option>
          {EVENT_TYPES.map((t) => <option key={t} value={t}>{t}</option>)}
        </select>

        <input
          type="text"
          placeholder="Filter by contract address…"
          value={contract}
          onChange={(e) => { setContract(e.target.value); setPage(1); }}
          className="flex-1 min-w-48 rounded-lg border border-gray-700 bg-gray-900 px-3 py-2 text-sm text-gray-300 placeholder-gray-600 focus:outline-none focus:ring-1 focus:ring-red-500"
        />

        <button
          onClick={resetFilters}
          className="rounded-lg border border-gray-700 px-3 py-2 text-sm text-gray-400 hover:text-white hover:border-gray-500 transition-colors"
        >
          Reset
        </button>
      </div>

      {/* Table */}
      {isLoading ? (
        <div className="space-y-2">
          {Array.from({ length: 8 }).map((_, i) => (
            <div key={i} className="h-10 rounded bg-gray-800 animate-pulse" />
          ))}
        </div>
      ) : isError ? (
        <div className="rounded-lg border border-red-800 bg-red-950 px-4 py-3 text-red-400 text-sm">
          Failed to load events.
        </div>
      ) : (
        <>
          <EventTable events={data?.items ?? []} />

          {/* Pagination */}
          {data && data.pagination.pages > 1 && (
            <div className="mt-4 flex items-center justify-between text-sm text-gray-500">
              <span>
                {data.pagination.total} events · page {data.pagination.page} of {data.pagination.pages}
              </span>
              <div className="flex gap-2">
                <button
                  disabled={page <= 1}
                  onClick={() => setPage((p) => p - 1)}
                  className="rounded border border-gray-700 px-3 py-1 disabled:opacity-40 hover:border-gray-500 transition-colors"
                >
                  ← Prev
                </button>
                <button
                  disabled={page >= data.pagination.pages}
                  onClick={() => setPage((p) => p + 1)}
                  className="rounded border border-gray-700 px-3 py-1 disabled:opacity-40 hover:border-gray-500 transition-colors"
                >
                  Next →
                </button>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
