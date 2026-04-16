const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export type Severity = "CRITICAL" | "HIGH" | "MEDIUM" | "LOW";

export interface Event {
  id: number;
  block_number: number;
  tx_hash: string;
  contract_address: string;
  event_type: string;
  severity: Severity;
  details: Record<string, unknown>;
  classified_at: string;
}

export interface PaginationMeta {
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface EventListResponse {
  items: Event[];
  pagination: PaginationMeta;
}

export interface SeverityStats {
  severity: Severity;
  count: number;
}

export interface ContractActivity {
  contract_address: string;
  event_count: number;
}

export interface StatsResponse {
  total_events: number;
  by_severity: SeverityStats[];
  most_active_contracts: ContractActivity[];
}

export interface HealthResponse {
  status: string;
  version: string;
  watcher_running: boolean;
}

async function fetchJson<T>(path: string): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`API error ${res.status}: ${path}`);
  return res.json() as Promise<T>;
}

export interface EventsParams {
  severity?: Severity | "";
  event_type?: string;
  contract?: string;
  page?: number;
  page_size?: number;
}

export function buildEventsUrl(params: EventsParams = {}): string {
  const q = new URLSearchParams();
  if (params.severity) q.set("severity", params.severity);
  if (params.event_type) q.set("event_type", params.event_type);
  if (params.contract) q.set("contract", params.contract);
  if (params.page) q.set("page", String(params.page));
  if (params.page_size) q.set("page_size", String(params.page_size));
  const qs = q.toString();
  return `/events${qs ? `?${qs}` : ""}`;
}

export const api = {
  events: (params: EventsParams = {}) =>
    fetchJson<EventListResponse>(buildEventsUrl(params)),
  event: (id: number) => fetchJson<Event>(`/events/${id}`),
  contractEvents: (address: string, page = 1) =>
    fetchJson<EventListResponse>(`/contracts/${address}/events?page=${page}&page_size=20`),
  stats: () => fetchJson<StatsResponse>("/stats"),
  health: () => fetchJson<HealthResponse>("/health"),
};
