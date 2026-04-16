import Link from "next/link";
import { LiveFeed } from "@/components/LiveFeed";

export default function HomePage() {
  return (
    <div className="mx-auto max-w-7xl px-4 py-12">
      {/* Hero */}
      <div className="mb-12 text-center">
        <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-red-800 bg-red-950/40 px-4 py-1.5 text-xs text-red-400">
          <span className="h-1.5 w-1.5 rounded-full bg-red-500 animate-pulse" />
          Live monitoring Base
        </div>
        <h1 className="text-4xl font-bold tracking-tight text-white mb-4">
          Contract Watchdog
        </h1>
        <p className="text-lg text-gray-400 max-w-2xl mx-auto">
          Real-time detection of proxy upgrades, admin changes, and permission events
          on Base. Get alerted before exploits happen.
        </p>
        <div className="mt-6 flex gap-4 justify-center">
          <Link
            href="/events"
            className="rounded-lg bg-red-600 px-5 py-2.5 text-sm font-semibold text-white hover:bg-red-500 transition-colors"
          >
            View All Events
          </Link>
          <Link
            href="/stats"
            className="rounded-lg border border-gray-700 px-5 py-2.5 text-sm font-semibold text-gray-300 hover:border-gray-500 hover:text-white transition-colors"
          >
            Dashboard
          </Link>
        </div>
      </div>

      {/* Live Feed */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-white">Recent Security Events</h2>
          <span className="text-xs text-gray-500">Auto-refreshes every 15s</span>
        </div>
        <LiveFeed />
      </div>
    </div>
  );
}
