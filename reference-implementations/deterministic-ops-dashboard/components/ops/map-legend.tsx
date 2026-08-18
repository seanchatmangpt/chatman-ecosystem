import { STATUS_HEX } from "@/lib/palette";

const ENTRIES: { key: keyof typeof STATUS_HEX; label: string }[] = [
  { key: "good", label: "Healthy node" },
  { key: "warning", label: "Degraded node" },
  { key: "critical", label: "Critical node" },
];

export function MapLegend() {
  return (
    <div className="flex flex-wrap items-center gap-4 text-sm text-muted-foreground">
      {ENTRIES.map((e) => (
        <span key={e.key} className="inline-flex items-center gap-1.5">
          <span
            className="inline-block size-2.5 rounded-full"
            style={{ backgroundColor: STATUS_HEX[e.key] }}
            aria-hidden="true"
          />
          {e.label}
        </span>
      ))}
      <span className="inline-flex items-center gap-1.5">
        <span className="inline-block h-0.5 w-4 rounded-full bg-[#3987e5]" aria-hidden="true" />
        Job flow (width = throughput)
      </span>
    </div>
  );
}
