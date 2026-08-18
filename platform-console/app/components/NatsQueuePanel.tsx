"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
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

export interface QueueStatusView {
  name: string;
  namespace: string;
  provisioned: boolean;
  ready: boolean;
  host: string;
  port: number;
}

interface Props {
  projectName: string;
  canProvision: boolean; // owner
  canReveal: boolean; // member+
  initialStatus: QueueStatusView;
}

/**
 * Managed Queue (NATS/JetStream) panel -- the queue counterpart to
 * RedisCachePanel, same structure: provision/teardown are real mutating
 * actions, every state change shown here follows a real 2xx response
 * from app/api/projects/[name]/queue/route.ts, never a locally-fabricated
 * "done".
 *
 * The connection string's password is never fetched until the user
 * explicitly clicks "Reveal" -- that's the one request that passes
 * `?reveal=1`, gated member+ server-side. Until revealed, only a redacted
 * placeholder is shown.
 */
export default function NatsQueuePanel({ projectName, canProvision, canReveal, initialStatus }: Props) {
  const router = useRouter();
  const [status, setStatus] = useState(initialStatus);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [teardownOpen, setTeardownOpen] = useState(false);
  const [revealedPassword, setRevealedPassword] = useState<string | null>(null);
  const [revealing, setRevealing] = useState(false);

  async function doProvision() {
    setBusy(true);
    setError(null);
    try {
      const res = await fetch(`/api/projects/${encodeURIComponent(projectName)}/queue`, {
        method: "POST",
      });
      const body = await res.json();
      if (!res.ok) throw new Error(body.error ?? `HTTP ${res.status}`);
      setStatus(body.status);
      router.refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }

  async function doTeardown() {
    setBusy(true);
    setError(null);
    try {
      const res = await fetch(`/api/projects/${encodeURIComponent(projectName)}/queue`, {
        method: "DELETE",
      });
      const body = await res.json();
      if (!res.ok) throw new Error(body.error ?? `HTTP ${res.status}`);
      setStatus({ ...status, provisioned: false, ready: false });
      setRevealedPassword(null);
      setTeardownOpen(false);
      router.refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }

  async function doReveal() {
    setRevealing(true);
    setError(null);
    try {
      const res = await fetch(
        `/api/projects/${encodeURIComponent(projectName)}/queue?reveal=1`,
      );
      const body = await res.json();
      if (!res.ok) throw new Error(body.error ?? `HTTP ${res.status}`);
      if (body.connection) setRevealedPassword(body.connection.password);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setRevealing(false);
    }
  }

  const connectionString = status.provisioned
    ? `nats://queue:${revealedPassword ?? "••••••••••••••••"}@${status.host}:${status.port}`
    : null;

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0">
        <CardTitle className="text-base font-medium">Managed Queue (NATS)</CardTitle>
        {status.provisioned ? (
          <Badge variant={status.ready ? "default" : "secondary"}>
            {status.ready ? "Running" : "Provisioning"}
          </Badge>
        ) : (
          <Badge variant="outline">Not provisioned</Badge>
        )}
      </CardHeader>
      <CardContent className="space-y-4">
        {!status.provisioned && (
          <p className="text-sm text-muted-foreground">
            No managed message queue exists for this project yet.
          </p>
        )}

        {status.provisioned && (
          <dl className="divide-y divide-border text-sm">
            <div className="grid grid-cols-3 gap-4 py-2">
              <dt className="text-muted-foreground">Host</dt>
              <dd className="col-span-2 break-all">{status.host}</dd>
            </div>
            <div className="grid grid-cols-3 gap-4 py-2">
              <dt className="text-muted-foreground">Port</dt>
              <dd className="col-span-2">{status.port}</dd>
            </div>
            <div className="grid grid-cols-3 gap-4 py-2">
              <dt className="text-muted-foreground">Connection string</dt>
              <dd className="col-span-2 break-all font-mono text-xs">{connectionString}</dd>
            </div>
          </dl>
        )}

        {status.provisioned && canReveal && !revealedPassword && (
          <Button size="sm" variant="outline" onClick={doReveal} disabled={revealing}>
            {revealing ? "Revealing..." : "Reveal password"}
          </Button>
        )}

        {error && (
          <Alert variant="destructive">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {canProvision && !status.provisioned && (
          <Button onClick={doProvision} disabled={busy}>
            {busy ? "Provisioning..." : "Provision Queue"}
          </Button>
        )}

        {canProvision && status.provisioned && (
          <Dialog open={teardownOpen} onOpenChange={setTeardownOpen}>
            <DialogTrigger asChild>
              <Button variant="destructive" disabled={busy}>
                Tear down
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Tear down managed queue?</DialogTitle>
                <DialogDescription>
                  This permanently deletes the Deployment, Service, NetworkPolicy, and
                  password Secret for <code>{status.name}</code> in{" "}
                  <code>{status.namespace}</code>. Any queued/persisted JetStream data is
                  lost.
                </DialogDescription>
              </DialogHeader>
              <DialogFooter>
                <Button variant="outline" onClick={() => setTeardownOpen(false)} disabled={busy}>
                  Cancel
                </Button>
                <Button variant="destructive" onClick={doTeardown} disabled={busy}>
                  {busy ? "Tearing down..." : "Confirm teardown"}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        )}
      </CardContent>
    </Card>
  );
}
