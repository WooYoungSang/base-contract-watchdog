import { SeverityBadge } from "@/components/SeverityBadge";
import { api } from "@/lib/api";
import Link from "next/link";
import { notFound } from "next/navigation";

export default async function EventDetailPage({ params }: { params: { id: string } }) {
  let event;
  try {
    event = await api.event(Number(params.id));
  } catch {
    notFound();
  }

  return (
    <div className="mx-auto max-w-3xl px-4 py-10">
      <div className="mb-6">
        <Link href="/events" className="text-sm text-gray-500 hover:text-gray-300">
          ← Back to events
        </Link>
      </div>

      <div className="rounded-xl border border-gray-800 bg-gray-900 overflow-hidden">
        {/* Header */}
        <div className="border-b border-gray-800 px-6 py-5 flex items-center gap-4">
          <SeverityBadge severity={event.severity} />
          <h1 className="text-lg font-semibold text-white">{event.event_type}</h1>
          <span className="ml-auto text-xs text-gray-500">Event #{event.id}</span>
        </div>

        {/* Fields */}
        <dl className="divide-y divide-gray-800">
          <Row label="Contract">
            <Link
              href={`/contracts/${event.contract_address}`}
              className="font-mono text-blue-400 hover:text-blue-300 break-all"
            >
              {event.contract_address}
            </Link>
          </Row>
          <Row label="Block">{event.block_number.toLocaleString()}</Row>
          <Row label="Transaction">
            <span className="font-mono text-gray-300 break-all">{event.tx_hash}</span>
          </Row>
          <Row label="Detected At">
            {new Date(event.classified_at).toLocaleString()}
          </Row>
          <Row label="Details">
            <pre className="text-xs text-gray-300 whitespace-pre-wrap break-all bg-gray-950 rounded p-3 mt-1">
              {JSON.stringify(event.details, null, 2)}
            </pre>
          </Row>
        </dl>
      </div>
    </div>
  );
}

function Row({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="px-6 py-4 sm:grid sm:grid-cols-3 sm:gap-4">
      <dt className="text-sm font-medium text-gray-400">{label}</dt>
      <dd className="mt-1 text-sm text-gray-200 sm:col-span-2 sm:mt-0">{children}</dd>
    </div>
  );
}
