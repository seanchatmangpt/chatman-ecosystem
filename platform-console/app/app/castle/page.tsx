import { cookies } from "next/headers";
import Nav from "@/components/Nav";
import CastleControls from "@/components/CastleControls";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { hasClusterCredentials } from "@/lib/k8s";
import { SESSION_COOKIE_NAME, verifySessionToken } from "@/lib/session";
import { getRoleFor, type Role } from "@/lib/authz";
import {
  ALLOWED_CASTLE_VERBS,
  CASTLE_DEFAULT_IMAGE,
  CASTLE_NAMESPACE,
  getCastleDeployment,
  listCastleJobs,
} from "@/lib/castle";

export const dynamic = "force-dynamic";

const ROLE_RANK: Record<Role, number> = { viewer: 0, member: 1, owner: 2 };

function statusBadgeVariant(status: string): "default" | "secondary" | "destructive" | "outline" {
  if (status === "Complete") return "default";
  if (status === "Failed") return "destructive";
  if (status === "Running") return "secondary";
  return "outline";
}

export default async function CastlePage() {
  const clusterConfigured = hasClusterCredentials();
  const cookieStore = await cookies();
  const token = cookieStore.get(SESSION_COOKIE_NAME)?.value;
  const session = token ? await verifySessionToken(token) : null;
  const role: Role = session ? await getRoleFor(session) : "viewer";
  const canDeploy = ROLE_RANK[role] >= ROLE_RANK.owner;
  const canRunOrSunset = ROLE_RANK[role] >= ROLE_RANK.member;

  const [deployment, jobs] = clusterConfigured
    ? await Promise.all([getCastleDeployment(), listCastleJobs()])
    : [null, null];

  return (
    <>
      <Nav />
      <main className="mx-auto max-w-5xl px-6 py-10">
        <h1 className="mb-2 text-2xl font-semibold text-foreground">Castle</h1>
        <p className="mb-6 max-w-3xl text-sm text-muted-foreground">
          DEPLOY / RUN / SUNSET lifecycle for the real{" "}
          <code>~/castle</code> security-testing crate (Rust CLI, binary{" "}
          <code>castle</code>) as a workload in its own dedicated{" "}
          <code>{CASTLE_NAMESPACE}</code> namespace. Every Run invokes one
          of castle&apos;s real, already-shipped, read-only CLI verbs (
          <code>fortune5</code>, <code>inventory</code>) as a one-shot{" "}
          <code>batch/v1</code> Job -- castle has no{" "}
          <code>construct</code>/<code>gymact</code> actuation verb yet
          (its own <code>VISION.md</code> gap #3), and this module never
          invents one: <code>CONSTRUCT != DO</code> is preserved exactly by
          only ever calling the CLI castle&apos;s own binary already
          exposes.
        </p>

        {!clusterConfigured && (
          <Alert className="mb-6 border-amber-900 bg-amber-950/40 text-amber-300">
            <AlertDescription className="text-amber-300">
              not configured: no in-cluster ServiceAccount credentials
              found. This page only returns real data when running as the
              platform-console pod.
            </AlertDescription>
          </Alert>
        )}

        {clusterConfigured && (
          <>
            <Card className="mb-6">
              <CardHeader>
                <CardTitle>Lifecycle controls</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {deployment && !deployment.ok && (
                  <Alert variant="destructive">
                    <AlertDescription>{deployment.error}</AlertDescription>
                  </Alert>
                )}

                {deployment?.ok && deployment.data && (
                  <p className="text-sm text-muted-foreground">
                    Deployed image <code>{deployment.data.image}</code> by{" "}
                    <code>{deployment.data.deployedBy}</code> at{" "}
                    {new Date(deployment.data.deployedAt).toLocaleString()}.
                  </p>
                )}

                <CastleControls
                  canDeploy={canDeploy}
                  canRunOrSunset={canRunOrSunset}
                  isDeployed={Boolean(deployment?.ok && deployment.data)}
                  defaultImage={CASTLE_DEFAULT_IMAGE}
                  verbs={Object.values(ALLOWED_CASTLE_VERBS).map((v) => ({
                    id: v.id,
                    label: v.label,
                    description: v.description,
                  }))}
                />

                {!canDeploy && (
                  <p className="text-xs text-muted-foreground">
                    Deploy/Sunset require the <code>owner</code> role; Run
                    requires <code>member</code>+. Your role: <code>{role}</code>.
                  </p>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Run history</CardTitle>
              </CardHeader>
              <CardContent>
                {jobs && !jobs.ok && (
                  <Alert variant="destructive">
                    <AlertDescription>{jobs.error}</AlertDescription>
                  </Alert>
                )}

                {jobs?.ok && jobs.data.length === 0 && (
                  <p className="text-sm text-muted-foreground">
                    No Castle Jobs yet -- Deploy, then Run a verb above.
                  </p>
                )}

                {jobs?.ok && jobs.data.length > 0 && (
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Job</TableHead>
                        <TableHead>Verb</TableHead>
                        <TableHead>Status</TableHead>
                        <TableHead>Created</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {jobs.data
                        .slice()
                        .sort((a, b) => (a.createdAt < b.createdAt ? 1 : -1))
                        .map((job) => (
                          <TableRow key={job.name}>
                            <TableCell className="font-mono text-xs">{job.name}</TableCell>
                            <TableCell>{job.verbId ?? "-"}</TableCell>
                            <TableCell>
                              <Badge variant={statusBadgeVariant(job.status)}>{job.status}</Badge>
                            </TableCell>
                            <TableCell className="text-xs text-muted-foreground">
                              {new Date(job.createdAt).toLocaleString()}
                            </TableCell>
                          </TableRow>
                        ))}
                    </TableBody>
                  </Table>
                )}
              </CardContent>
            </Card>
          </>
        )}
      </main>
    </>
  );
}
