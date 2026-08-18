import type { StatusResult } from "@/lib/status";

function formatValue(value: unknown): string {
  if (value === null || value === undefined) return "-";
  if (Array.isArray(value)) return value.length ? value.join(", ") : "(none)";
  if (typeof value === "object") return JSON.stringify(value);
  return String(value);
}

export default function StatusPanel<T extends object>({
  title,
  result,
}: {
  title: string;
  result: StatusResult<T>;
}) {
  if (!result.ok) {
    return (
      <div className="card p-6">
        <h2 className="mb-2 text-base font-medium text-white">{title}</h2>
        <div className="flex items-center gap-2 rounded-md border border-red-900 bg-red-950/40 px-3 py-2">
          <span className="h-2 w-2 rounded-full bg-red-500" />
          <span className="text-sm text-red-300">unreachable</span>
        </div>
        <p className="mt-2 break-all text-xs text-gray-500">{result.error}</p>
      </div>
    );
  }

  const entries = Object.entries(result.data as Record<string, unknown>);

  return (
    <div className="card p-6">
      <div className="mb-4 flex items-center gap-2">
        <h2 className="text-base font-medium text-white">{title}</h2>
        <span className="flex items-center gap-1 rounded-full border border-emerald-900 bg-emerald-950/40 px-2 py-0.5 text-xs text-emerald-300">
          <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
          reachable
        </span>
      </div>
      <dl className="divide-y divide-border">
        {entries.map(([key, value]) => (
          <div key={key} className="grid grid-cols-3 gap-4 py-2 text-sm">
            <dt className="text-gray-400">{key}</dt>
            <dd className="col-span-2 break-all text-gray-100">{formatValue(value)}</dd>
          </div>
        ))}
      </dl>
    </div>
  );
}
