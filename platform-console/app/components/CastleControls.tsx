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
  const [sunsetOpen, setSunsetOpen] = useState(false);

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
