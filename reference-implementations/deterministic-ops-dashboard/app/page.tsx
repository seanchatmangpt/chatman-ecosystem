import { Activity, AlertOctagon, CheckCircle2, Gauge, Server } from "lucide-react";
import { Separator } from "@/components/ui/separator";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { StatTile } from "@/components/ops/stat-tile";
import { MapLegend } from "@/components/ops/map-legend";
import { OpsMapLoader } from "@/components/ops/ops-map-loader";
import { JobsPanel } from "@/components/ops/jobs-panel";
import { NodesPanel } from "@/components/ops/nodes-panel";
import { IncidentsPanel } from "@/components/ops/incidents-panel";
import { EntityDashboard } from "@/components/ops/entity-dashboard";
import { INCIDENTS, STATS } from "@/lib/ops-data";

export default function Home() {
  return (
    <div className="mx-auto flex w-full max-w-7xl flex-1 flex-col gap-6 px-6 py-8">
      <header className="flex flex-col gap-1">
        <h1 className="text-2xl font-semibold tracking-tight">Deterministic Ops Dashboard</h1>
        <p className="text-sm text-muted-foreground">
          Reference implementation — fixed data, fixed layout, zero runtime network calls.
          Rendered output is identical on every build.
        </p>
      </header>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatTile label="Nodes online" value={STATS.totalNodes} icon={Server} />
        <StatTile label="Jobs running" value={STATS.jobsRunning} icon={Activity} tone="default" />
        <StatTile
          label="Success rate"
          value={STATS.successRatePct}
          suffix="%"
          icon={CheckCircle2}
          tone="good"
        />
        <StatTile
          label="Mean latency"
          value={STATS.meanLatencyMs.toLocaleString()}
          suffix="ms"
          icon={Gauge}
          tone="default"
        />
      </div>

      <Separator />

      <Tabs defaultValue="entities" className="flex-1">
        <TabsList>
          <TabsTrigger value="entities">Entity graph</TabsTrigger>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="nodes">Nodes</TabsTrigger>
          <TabsTrigger value="incidents" className="gap-1.5">
            Incidents
            {INCIDENTS.length > 0 && (
              <span className="inline-flex size-4 items-center justify-center rounded-full bg-[#d03b3b]/20 text-[10px] font-semibold text-[#f27272]">
                {INCIDENTS.length}
              </span>
            )}
          </TabsTrigger>
        </TabsList>

        <TabsContent value="entities" className="pt-4">
          <EntityDashboard />
        </TabsContent>

        <TabsContent value="overview" className="flex flex-col gap-4">
          <div className="flex flex-col gap-2">
            <div className="h-[420px] w-full">
              <OpsMapLoader />
            </div>
            <MapLegend />
          </div>
          <JobsPanel />
        </TabsContent>

        <TabsContent value="nodes">
          <NodesPanel />
        </TabsContent>

        <TabsContent value="incidents">
          <IncidentsPanel />
        </TabsContent>
      </Tabs>

      <footer className="flex items-center gap-2 pt-4 text-xs text-muted-foreground">
        <AlertOctagon className="size-3.5" aria-hidden="true" />
        Reference artifact only — not wired to any live cluster or deploy pipeline.
      </footer>
    </div>
  );
}
