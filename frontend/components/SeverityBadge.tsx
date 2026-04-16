import type { Severity } from "@/lib/api";

const STYLES: Record<Severity, string> = {
  CRITICAL: "bg-red-600 text-white",
  HIGH: "bg-orange-500 text-white",
  MEDIUM: "bg-yellow-400 text-gray-900",
  LOW: "bg-green-600 text-white",
};

export function SeverityBadge({ severity }: { severity: Severity }) {
  return (
    <span
      className={`inline-flex items-center rounded px-2 py-0.5 text-xs font-semibold uppercase tracking-wide ${STYLES[severity]}`}
    >
      {severity}
    </span>
  );
}
