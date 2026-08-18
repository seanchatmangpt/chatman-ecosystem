"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { AlertCircle, Command, Inbox, RefreshCw } from "lucide-react";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { OpsDashboardCanvasLoader } from "@/components/OpsDashboardCanvasLoader";
import { fetchEntities } from "@/lib/fetch-entities";
import type { Entity } from "@/lib/entity-types";
import { EntityLegend } from "./entity-legend";
import { EntityDetailPanel } from "./entity-detail-panel";
import { EntityTable } from "./entity-table";
import { CommandPalette } from "./command-palette";

/** Live re-fetch cadence for the entity graph (requirement: document N). */
export const POLL_INTERVAL_MS = 5000;

type LoadState =
  | { status: "loading" }
  | { status: "error"; message: string }
  | { status: "ready"; entities: Entity[] };

/**
 * Full entity-graph dashboard: real async polling data source
 * (`fetchEntities`, `lib/fetch-entities.ts`), a deck.gl spatial view and a
 * plain table view of the same data, a docked detail panel and legend, and
 * a Cmd+K/Ctrl+K command palette — all sharing one `selectedId` state.
 */
export function EntityDashboard() {
  const [state, setState] = useState<LoadState>({ status: "loading" });
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [paletteOpen, setPaletteOpen] = useState(false);

  const load = useCallback(async () => {
    try {
      const entities = await fetchEntities();
      setState({ status: "ready", entities });
    } catch (err) {
      setState({ status: "error", message: err instanceof Error ? err.message : String(err) });
    }
  }, []);

  // Initial fetch + live re-fetch every POLL_INTERVAL_MS.
  useEffect(() => {
    load();
    const id = setInterval(load, POLL_INTERVAL_MS);
    return () => clearInterval(id);
  }, [load]);

  // Global Cmd+K / Ctrl+K listener, attached for the whole dashboard's
  // lifetime (not just while the palette is open).
  useEffect(() => {
    function onKeyDown(e: KeyboardEvent) {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setPaletteOpen((open) => !open);
      }
    }
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, []);

  const entities = useMemo(() => (state.status === "ready" ? state.entities : []), [state]);
  const selected = useMemo(
    () => entities.find((e) => e.id === selectedId) ?? null,
    [entities, selectedId],
  );

  function handlePick(id: string) {
    setSelectedId(id);
    setPaletteOpen(false);
  }

  if (state.status === "loading") {
    return <DashboardSkeleton />;
  }

  if (state.status === "error") {
    return (
      <Alert variant="destructive">
        <AlertCircle />
        <AlertTitle>Failed to load entities</AlertTitle>
        <AlertDescription>{state.message}</AlertDescription>
        <Button variant="outline" size="sm" className="mt-2" onClick={load}>
          <RefreshCw className="size-3.5" />
          Retry
        </Button>
      </Alert>
    );
  }

  if (entities.length === 0) {
    return (
      <Alert>
        <Inbox />
        <AlertTitle>No entities</AlertTitle>
        <AlertDescription>
          fetchEntities() returned zero entities — nothing to display yet.
        </AlertDescription>
      </Alert>
    );
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between gap-2">
        <p className="text-sm text-muted-foreground">
          {entities.length} entities · live re-fetch every {POLL_INTERVAL_MS / 1000}s
        </p>
        <Button variant="outline" size="sm" onClick={() => setPaletteOpen(true)}>
          <Command className="size-3.5" />
          Jump to entity
          <kbd className="ml-1 rounded border border-border bg-muted px-1 font-mono text-[10px]">⌘K</kbd>
        </Button>
      </div>

      <Tabs defaultValue="map">
        <TabsList>
          <TabsTrigger value="map">Spatial</TabsTrigger>
          <TabsTrigger value="table">Table</TabsTrigger>
        </TabsList>

        <TabsContent value="map" className="flex flex-col gap-3 pt-3 lg:flex-row">
          <div className="h-[440px] flex-1">
            <OpsDashboardCanvasLoader entities={entities} selectedId={selectedId} onSelect={setSelectedId} />
          </div>
          <div className="flex w-full flex-col gap-3 lg:w-80 lg:shrink-0">
            <EntityLegend entities={entities} />
            <EntityDetailPanel entity={selected} />
          </div>
        </TabsContent>

        <TabsContent value="table" className="flex flex-col gap-3 pt-3 lg:flex-row">
          <div className="flex-1">
            <EntityTable entities={entities} selectedId={selectedId} onSelect={setSelectedId} />
          </div>
          <div className="flex w-full flex-col gap-3 lg:w-80 lg:shrink-0">
            <EntityLegend entities={entities} />
            <EntityDetailPanel entity={selected} />
          </div>
        </TabsContent>
      </Tabs>

      <CommandPalette
        open={paletteOpen}
        onOpenChange={setPaletteOpen}
        entities={entities}
        onPick={handlePick}
      />
    </div>
  );
}

/** Loading state: skeleton blocks shaped like the eventual content, never a bare spinner. */
function DashboardSkeleton() {
  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between gap-2">
        <Skeleton className="h-4 w-56" />
        <Skeleton className="h-7 w-32 rounded-lg" />
      </div>
      <div className="flex gap-2">
        <Skeleton className="h-8 w-20 rounded-md" />
        <Skeleton className="h-8 w-20 rounded-md" />
      </div>
      <div className="flex flex-col gap-3 lg:flex-row">
        <Skeleton className="h-[440px] flex-1 rounded-lg" />
        <div className="flex w-full flex-col gap-3 lg:w-80 lg:shrink-0">
          <Skeleton className="h-36 rounded-lg" />
          <Skeleton className="h-52 rounded-lg" />
        </div>
      </div>
    </div>
  );
}
