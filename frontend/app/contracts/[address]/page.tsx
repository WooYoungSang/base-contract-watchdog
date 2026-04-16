import { api } from "@/lib/api";
import { EventTimeline } from "@/components/EventTimeline";
import Link from "next/link";

export default async function ContractPage({ params }: { params: { address: string } }) {
  let data;
  try {
    data = await api.contractEvents(params.address);
  } catch {
    data = { items: [], pagination: { total: 0, page: 1, page_size: 20, pages: 0 } };
  }

  return (
    <div className="mx-auto max-w-3xl px-4 py-10">
      <div className="mb-6">
        <Link href="/events" className="text-sm text-gray-500 hover:text-gray-300">
          ← Back to events
        </Link>
      </div>

      <h1 className="text-xl font-bold text-white mb-1">Contract Events</h1>
      <p className="font-mono text-sm text-gray-400 break-all mb-8">{params.address}</p>

      <div className="flex items-center justify-between mb-6">
        <span className="text-sm text-gray-500">{data.pagination.total} total events</span>
      </div>

      <EventTimeline events={data.items} />
    </div>
  );
}
