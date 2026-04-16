import { api } from "@/lib/api";
import { StatsChart } from "@/components/StatsChart";
import Link from "next/link";

export const revalidate = 30;

export default async function StatsPage() {
  let stats;
  try {
    stats = await api.stats();
  } catch {
    stats = { total_events: 0, by_severity: [], most_active_contracts: [] };
  }

  return (
    <div className="mx-auto max-w-5xl px-4 py-10">
      <h1 className="text-2xl font-bold text-white mb-8">Security Dashboard</h1>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-10">
        <StatCard label="Total Events" value={stats.total_events} />
        {(["CRITICAL", "HIGH", "MEDIUM", "LOW"] as const).map((s) => {
          const found = stats.by_severity.find((x) => x.severity === s);
          return <StatCard key={s} label={s} value={found?.count ?? 0} severity={s} />;
        })}
      </div>

      {/* Severity Chart */}
      <div className="rounded-xl border border-gray-800 bg-gray-900 p-6 mb-8">
        <h2 className="text-base font-semibold text-white mb-4">Events by Severity</h2>
        <StatsChart data={stats.by_severity} />
      </div>

      {/* Most Active Contracts */}
      <div className="rounded-xl border border-gray-800 bg-gray-900 p-6">
        <h2 className="text-base font-semibold text-white mb-4">Most Active Contracts</h2>
        {stats.most_active_contracts.length === 0 ? (
          <p className="text-sm text-gray-500">No data yet.</p>
        ) : (
          <ol className="space-y-2">
            {stats.most_active_contracts.map((c, i) => (
              <li key={c.contract_address} className="flex items-center gap-3">
                <span className="text-xs text-gray-600 w-5">{i + 1}</span>
                <Link
                  href={`/contracts/${c.contract_address}`}
                  className="font-mono text-sm text-blue-400 hover:text-blue-300 flex-1 truncate"
                >
                  {c.contract_address}
                </Link>
                <span className="text-sm text-gray-400">{c.event_count} events</span>
              </li>
            ))}
          </ol>
        )}
      </div>
    </div>
  );
}

const SEVERITY_COLORS: Record<string, string> = {
  CRITICAL: "text-red-500",
  HIGH: "text-orange-400",
  MEDIUM: "text-yellow-400",
  LOW: "text-green-500",
};

function StatCard({ label, value, severity }: { label: string; value: number; severity?: string }) {
  return (
    <div className="rounded-xl border border-gray-800 bg-gray-900 p-4">
      <p className={`text-xs font-medium uppercase tracking-wide mb-1 ${severity ? SEVERITY_COLORS[severity] : "text-gray-400"}`}>
        {label}
      </p>
      <p className="text-3xl font-bold text-white">{value}</p>
    </div>
  );
}
