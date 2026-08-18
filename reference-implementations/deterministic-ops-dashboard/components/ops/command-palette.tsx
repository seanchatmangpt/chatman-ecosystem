"use client";

import { useEffect, useMemo, useState } from "react";
import { Search } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import type { Entity } from "@/lib/entity-types";
import { cn } from "@/lib/utils";
import { EntityStatusBadge } from "./status-badge";

interface CommandPaletteProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  entities: Entity[];
  onPick: (id: string) => void;
}

/**
 * Cmd+K / Ctrl+K global command palette. The global keydown listener lives
 * in the parent (`EntityDashboard`) since it must be attached whenever the
 * dashboard is mounted, not only while this dialog is open; this component
 * just renders the open dialog and the real substring filter.
 */
export function CommandPalette({ open, onOpenChange, entities, onPick }: CommandPaletteProps) {
  const [query, setQuery] = useState("");
  const [activeIndex, setActiveIndex] = useState(0);

  // Reset search state each time the palette opens.
  useEffect(() => {
    if (open) {
      setQuery("");
      setActiveIndex(0);
    }
  }, [open]);

  const results = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return entities;
    return entities.filter(
      (e) => e.label.toLowerCase().includes(q) || e.id.toLowerCase().includes(q),
    );
  }, [entities, query]);

  useEffect(() => {
    setActiveIndex(0);
  }, [results.length]);

  function handleKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setActiveIndex((i) => Math.min(i + 1, results.length - 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setActiveIndex((i) => Math.max(i - 1, 0));
    } else if (e.key === "Enter") {
      e.preventDefault();
      const pick = results[activeIndex];
      if (pick) onPick(pick.id);
    }
  }

  return (
    <Dialog open={open} onOpenChange={(next) => onOpenChange(next)}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Jump to entity</DialogTitle>
          <DialogDescription>Search by name or id. Enter selects, arrow keys navigate.</DialogDescription>
        </DialogHeader>

        <div className="grid gap-1.5">
          <Label htmlFor="palette-search" className="sr-only">
            Search entities
          </Label>
          <div className="relative">
            <Search className="pointer-events-none absolute left-2.5 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              id="palette-search"
              autoFocus
              className="pl-8"
              placeholder="auth-service, svc-payments…"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={handleKeyDown}
            />
          </div>
        </div>

        <div className="max-h-72 overflow-y-auto rounded-md border border-border">
          {results.length === 0 && (
            <p className="p-3 text-sm text-muted-foreground">No entities match &ldquo;{query}&rdquo;.</p>
          )}
          {results.map((entity, i) => (
            <button
              key={entity.id}
              type="button"
              className={cn(
                "flex w-full items-center justify-between gap-2 px-3 py-2 text-left text-sm transition-colors",
                i === activeIndex ? "bg-muted" : "hover:bg-muted/50",
              )}
              onMouseEnter={() => setActiveIndex(i)}
              onClick={() => onPick(entity.id)}
            >
              <span className="flex flex-col">
                <span className="font-medium">{entity.label}</span>
                <span className="font-mono text-xs text-muted-foreground">{entity.id}</span>
              </span>
              <EntityStatusBadge status={entity.status} />
            </button>
          ))}
        </div>
      </DialogContent>
    </Dialog>
  );
}
