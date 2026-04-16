import Link from "next/link";
import type { Event } from "@/lib/api";
import { SeverityBadge } from "./SeverityBadge";

export function EventTimeline({ events }: { events: Event[] }) {
  if (events.length === 0) {
    return (
      <div className="py-12 text-center text-gray-500">No events for this contract.</div>
    );
  }

  return (
    <ol className="relative border-l border-gray-800 space-y-6 ml-4">
      {events.map((ev) => (
        <li key={ev.id} className="ml-6">
          <span className="absolute -left-2 flex h-4 w-4 items-center justify-center rounded-full bg-gray-800 ring-2 ring-gray-700" />
          <div className="rounded-lg border border-gray-800 bg-gray-900 p-4">
            <div className="flex items-center gap-3 mb-2">
              <SeverityBadge severity={ev.severity} />
              <span className="font-mono text-sm text-gray-300">{ev.event_type}</span>
              <span className="ml-auto text-xs text-gray-500">
                Block {ev.block_number.toLocaleString()}
              </span>
            </div>
            <p className="text-xs text-gray-500 font-mono mb-2">{ev.tx_hash}</p>
            <Link href={`/events/${ev.id}`} className="text-xs text-blue-400 hover:text-blue-300">
              View detail →
            </Link>
          </div>
        </li>
      ))}
    </ol>
  );
}
