"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Alert, AlertDescription } from "@/components/ui/alert";

export interface CastleVerbOption {
  id: string;
  label: string;
  description: string;
}

interface Props {
  canDeploy: boolean;
  canRunOrSunset: boolean;
  isDeployed: boolean;
  verbs: CastleVerbOption[];
  defaultImage: string;
}

/** Local-time `datetime-local` input value 5 minutes from now -- a
 * sensible default lower bound for "schedule this for later" that is
 * always strictly in the future by the time the form actually submits. */
function defaultScheduleValue(): string {
  const d = new Date(Date.now() + 5 * 60 * 1000);
  d.setSeconds(0, 0);
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

/**
 * DEPLOY / RUN / SUNSET action bar. Every action is a real fetch against
 * this module's own API routes (app/api/castle/*) -- no local
 * fabrication of success. `router.refresh()` after each real response
 * re-renders the server component page with the real, freshly-read k8s
 * state, so the list of Jobs and the deployment badge are never stale
 * client-only state.
 */
export default function CastleControls({
  canDeploy,
  canRunOrSunset,
  isDeployed,
  verbs,
  defaultImage,
}: Props) {
  const router = useRouter();
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [sunsetOpen, setSunsetOpen] = useState(false);
  const [scheduleOpen, setScheduleOpen] = useState(false);
  const [scheduleVerbId, setScheduleVerbId] = useState(verbs[0]?.id ?? "");
  const [scheduleFor, setScheduleFor] = useState(defaultScheduleValue);

  async function doDeploy() {
    setBusy("deploy");
    setError(null);
    try {
      const res = await fetch("/api/castle/deploy", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ image: defaultImage }),
      });
      const body = await res.json();
      if (!res.ok) throw new Error(body.error ?? `HTTP ${res.status}`);
      router.refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(null);
    }
  }

  async function doRun(verbId: string) {
    setBusy(`run:${verbId}`);
    setError(null);
    try {
      const res = await fetch("/api/castle/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ verbId }),
      });
      const body = await res.json();
      if (!res.ok) throw new Error(body.error ?? `HTTP ${res.status}`);
      router.refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(null);
    }
  }

  async function doSchedule() {
    setBusy("schedule");
    setError(null);
    setNotice(null);
    try {
      // `datetime-local` has no timezone -- `new Date(value)` parses it
      // as LOCAL time in the browser's own timezone, then `.toISOString()`
      // converts to the real UTC instant the server-side validation
      // (lib/scheduled-verbs.ts's scheduleCastleVerb) compares against
      // `Date.now()` -- never a raw string round-tripped as if it were
      // already UTC.
      const requestedFor = new Date(scheduleFor).toISOString();
      const res = await fetch("/api/castle/schedule", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ verbId: scheduleVerbId, requestedFor }),
      });
      const body = await res.json();
      if (!res.ok && res.status !== 202) throw new Error(body.error ?? `HTTP ${res.status}`);
      setNotice(body.message ?? "Scheduled -- awaiting a second approver.");
      setScheduleOpen(false);
      router.refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(null);
    }
  }

  async function doSunset() {
    setBusy("sunset");
    setError(null);
    try {
      const res = await fetch("/api/castle/sunset", { method: "POST" });
      const body = await res.json();
      if (!res.ok) throw new Error(body.error ?? `HTTP ${res.status}`);
      setSunsetOpen(false);
      router.refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(null);
    }
  }

  return (
    <div className="space-y-4">
      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {notice && (
        <Alert>
          <AlertDescription>{notice}</AlertDescription>
        </Alert>
      )}

      <div className="flex flex-wrap items-center gap-3">
        <Badge variant={isDeployed ? "default" : "secondary"}>
          {isDeployed ? "deployed" : "not deployed"}
        </Badge>

        <Button size="sm" disabled={!canDeploy || busy !== null} onClick={doDeploy}>
          {busy === "deploy" ? "Deploying..." : isDeployed ? "Re-deploy" : "Deploy"}
        </Button>

        {verbs.map((verb) => (
          <Button
            key={verb.id}
            size="sm"
            variant="secondary"
            title={verb.description}
            disabled={!canRunOrSunset || !isDeployed || busy !== null}
            onClick={() => doRun(verb.id)}
          >
            {busy === `run:${verb.id}` ? "Running..." : `Run: ${verb.label}`}
          </Button>
        ))}

        <Dialog open={scheduleOpen} onOpenChange={setScheduleOpen}>
          <DialogTrigger asChild>
            <Button size="sm" variant="outline" disabled={!canRunOrSunset || !isDeployed || verbs.length === 0}>
              Schedule for maintenance window...
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Schedule a castle verb</DialogTitle>
              <DialogDescription>
                Queues a real castle verb to run unattended at the exact
                time you pick below. Requires a second, distinct{" "}
                <code>owner</code>-role approver to sign off (POST{" "}
                <code>/api/approvals/[id]</code>) before it becomes
                eligible to run -- it will not fire on the maker&apos;s
                approval alone, and it never fires early.
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-3 py-2">
              <label className="block space-y-1 text-sm">
                <span className="text-muted-foreground">Verb</span>
                <select
                  className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                  value={scheduleVerbId}
                  onChange={(e) => setScheduleVerbId(e.target.value)}
                >
                  {verbs.map((v) => (
                    <option key={v.id} value={v.id}>
                      {v.label}
                    </option>
                  ))}
                </select>
              </label>
              <label className="block space-y-1 text-sm">
                <span className="text-muted-foreground">Run at (your local time)</span>
                <input
                  type="datetime-local"
                  className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                  value={scheduleFor}
                  onChange={(e) => setScheduleFor(e.target.value)}
                />
              </label>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setScheduleOpen(false)} disabled={busy !== null}>
                Cancel
              </Button>
              <Button onClick={doSchedule} disabled={busy !== null || !scheduleVerbId}>
                {busy === "schedule" ? "Scheduling..." : "Schedule"}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        <Dialog open={sunsetOpen} onOpenChange={setSunsetOpen}>
          <DialogTrigger asChild>
            <Button size="sm" variant="destructive" disabled={!canRunOrSunset || busy !== null}>
              Sunset
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Sunset Castle</DialogTitle>
              <DialogDescription>
                Deletes every real Run Job this module created in the{" "}
                <code>castle</code> namespace plus the deployment record. This
                cannot be undone -- Run again after a new Deploy.
              </DialogDescription>
            </DialogHeader>
            <DialogFooter>
              <Button variant="outline" onClick={() => setSunsetOpen(false)} disabled={busy !== null}>
                Cancel
              </Button>
              <Button variant="destructive" onClick={doSunset} disabled={busy !== null}>
                {busy === "sunset" ? "Sunsetting..." : "Confirm sunset"}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </div>
  );
}
