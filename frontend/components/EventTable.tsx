"use client";

import Link from "next/link";
import type { Event } from "@/lib/api";
import { SeverityBadge } from "./SeverityBadge";

function shortAddr(addr: string) {
  return `${addr.slice(0, 6)}…${addr.slice(-4)}`;
}

function shortHash(hash: string) {
  return `${hash.slice(0, 8)}…`;
}

export function EventTable({ events }: { events: Event[] }) {
  if (events.length === 0) {
    return (
      <div className="rounded-lg border border-gray-800 bg-gray-900 py-16 text-center text-gray-500">
        No events found.
      </div>
    );
  }

  return (
    <div className="overflow-x-auto rounded-lg border border-gray-800">
      <table className="w-full text-sm text-left">
        <thead className="bg-gray-900 text-gray-400 text-xs uppercase tracking-wider">
          <tr>
            <th className="px-4 py-3">Severity</th>
            <th className="px-4 py-3">Event Type</th>
            <th className="px-4 py-3">Contract</th>
            <th className="px-4 py-3">Block</th>
            <th className="px-4 py-3">Tx</th>
            <th className="px-4 py-3">Time</th>
            <th className="px-4 py-3"></th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-800">
          {events.map((ev) => (
            <tr key={ev.id} className="bg-gray-950 hover:bg-gray-900 transition-colors">
              <td className="px-4 py-3">
                <SeverityBadge severity={ev.severity} />
              </td>
              <td className="px-4 py-3 font-mono text-gray-300">{ev.event_type}</td>
              <td className="px-4 py-3">
                <Link
                  href={`/contracts/${ev.contract_address}`}
                  className="font-mono text-blue-400 hover:text-blue-300"
                >
                  {shortAddr(ev.contract_address)}
                </Link>
              </td>
              <td className="px-4 py-3 text-gray-400">{ev.block_number.toLocaleString()}</td>
              <td className="px-4 py-3 font-mono text-gray-500">{shortHash(ev.tx_hash)}</td>
              <td className="px-4 py-3 text-gray-500 whitespace-nowrap">
                {new Date(ev.classified_at).toLocaleString()}
              </td>
              <td className="px-4 py-3">
                <Link
                  href={`/events/${ev.id}`}
                  className="text-xs text-gray-400 hover:text-white transition-colors"
                >
                  Detail →
                </Link>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
