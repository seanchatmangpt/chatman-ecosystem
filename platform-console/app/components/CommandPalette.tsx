"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { cn } from "@/lib/utils";
import type { SearchResult, SearchResultType } from "@/lib/global-search";

// AWS resource search / GCP Cloud Console search bar equivalent: real
// cross-resource lookup across every module, from one place. Opens on
// Cmd+K (Mac) / Ctrl+K (Windows/Linux) from anywhere in the console
// (wired into app/layout.tsx, not one page), debounces keystrokes, and
// fetches real results from GET /api/search -- never a client-side
// static index built ahead of time.

const TYPE_LABEL: Record<SearchResultType, string> = {
  service: "Service",
  project: "Project",
  secret: "Secret",
  cronjob: "Scheduled Job",
  backup: "Backup",
  webhook: "Webhook",
  "openclaw-tool": "OpenClaw Domain/Solver",
};

const DEBOUNCE_MS = 200;

export default function CommandPalette() {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeIndex, setActiveIndex] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const requestSeq = useRef(0);

  // Global Cmd+K / Ctrl+K shortcut, active on every page (this component
  // is mounted once in app/layout.tsx).
  useEffect(() => {
    function onKeyDown(e: KeyboardEvent) {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setOpen((v) => !v);
      }
      if (e.key === "Escape") {
        setOpen(false);
      }
    }
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, []);

  useEffect(() => {
    if (open) {
      setQuery("");
      setResults([]);
      setError(null);
      setActiveIndex(0);
      // Wait one tick for the Dialog's own open animation to mount the input.
      setTimeout(() => inputRef.current?.focus(), 0);
    }
  }, [open]);

  const runSearch = useCallback((q: string) => {
    const seq = ++requestSeq.current;
    if (q.trim().length < 2) {
      setResults([]);
      setLoading(false);
      setError(null);
      return;
    }
    setLoading(true);
    setError(null);
    fetch(`/api/search?q=${encodeURIComponent(q)}`)
      .then(async (res) => {
        const body = await res.json();
        if (seq !== requestSeq.current) return; // a newer keystroke already superseded this request
        if (!res.ok) {
          setError(body.error ?? `HTTP ${res.status}`);
          setResults([]);
          return;
        }
        setResults(body.results as SearchResult[]);
        setActiveIndex(0);
      })
      .catch((err) => {
        if (seq !== requestSeq.current) return;
        setError(err instanceof Error ? err.message : String(err));
        setResults([]);
      })
      .finally(() => {
        if (seq === requestSeq.current) setLoading(false);
      });
  }, []);

  function onQueryChange(value: string) {
    setQuery(value);
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => runSearch(value), DEBOUNCE_MS);
  }

  function navigateTo(result: SearchResult) {
    setOpen(false);
    router.push(result.path);
  }

  function onInputKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setActiveIndex((i) => Math.min(i + 1, results.length - 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setActiveIndex((i) => Math.max(i - 1, 0));
    } else if (e.key === "Enter") {
      e.preventDefault();
      const target = results[activeIndex];
      if (target) navigateTo(target);
    }
  }

  return (
    <>
      <button
        type="button"
        onClick={() => setOpen(true)}
        className="fixed bottom-4 right-4 z-40 flex items-center gap-2 rounded-full border border-border bg-panel px-4 py-2 text-xs text-muted-foreground shadow-lg hover:text-foreground"
        aria-label="Open global search"
      >
        Search
        <kbd className="rounded border border-border bg-background px-1.5 py-0.5 text-[10px]">
          ⌘K
        </kbd>
      </button>

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent
          hideClose
          className="max-w-xl gap-0 overflow-hidden p-0"
          onOpenAutoFocus={(e) => {
            e.preventDefault();
            inputRef.current?.focus();
          }}
        >
          <DialogHeader className="sr-only">
            <DialogTitle>Global search</DialogTitle>
            <DialogDescription>
              Search every real resource across this console&apos;s modules by name.
            </DialogDescription>
          </DialogHeader>

          <div className="border-b border-border px-4 py-3">
            <input
              ref={inputRef}
              value={query}
              onChange={(e) => onQueryChange(e.target.value)}
              onKeyDown={onInputKeyDown}
              type="text"
              placeholder="Search services, projects, secrets, jobs, backups, webhooks..."
              className="w-full border-none bg-transparent text-sm text-foreground outline-none placeholder:text-muted-foreground"
              autoComplete="off"
              spellCheck={false}
            />
          </div>

          <div className="max-h-96 overflow-y-auto p-2">
            {loading && <p className="px-3 py-6 text-center text-sm text-muted-foreground">Searching...</p>}

            {!loading && error && (
              <p className="px-3 py-6 text-center text-sm text-destructive">{error}</p>
            )}

            {!loading && !error && query.trim().length >= 2 && results.length === 0 && (
              <p className="px-3 py-6 text-center text-sm text-muted-foreground">
                No matches for &quot;{query}&quot;.
              </p>
            )}

            {!loading && !error && query.trim().length < 2 && (
              <p className="px-3 py-6 text-center text-sm text-muted-foreground">
                Type at least 2 characters to search every module at once.
              </p>
            )}

            {!loading &&
              !error &&
              results.map((result, i) => (
                <button
                  key={`${result.type}-${result.path}-${result.name}-${i}`}
                  type="button"
                  onClick={() => navigateTo(result)}
                  onMouseEnter={() => setActiveIndex(i)}
                  className={cn(
                    "flex w-full items-center justify-between gap-3 rounded-md px-3 py-2 text-left text-sm",
                    i === activeIndex ? "bg-accent text-accent-foreground" : "text-foreground",
                  )}
                >
                  <span className="min-w-0">
                    <span className="block truncate font-medium">{result.name}</span>
                    <span className="block truncate text-xs text-muted-foreground">{result.detail}</span>
                  </span>
                  <span className="shrink-0 rounded border border-border px-1.5 py-0.5 text-[10px] uppercase tracking-wide text-muted-foreground">
                    {TYPE_LABEL[result.type]}
                  </span>
                </button>
              ))}
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
}
