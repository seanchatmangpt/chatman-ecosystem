import { cookies } from "next/headers";
import Nav from "@/components/Nav";
import { SESSION_COOKIE_NAME, verifySessionToken } from "@/lib/session";
import { requireRole, roleIdentifierFor } from "@/lib/authz";
import { hasClusterCredentials } from "@/lib/k8s";
import {
  listActivePolicies,
  type ActiveValidatingAdmissionPolicy,
  type ActiveValidatingAdmissionPolicyBinding,
} from "@/lib/policy";

export const dynamic = "force-dynamic";

// Owner-gated, read-only, same pattern as app/org/page.tsx: middleware.ts
// already guarantees a valid session reaches this page; the requireRole
// check below is this page's OWN gate. There is nothing to mutate here --
// this page only ever reads real cluster state -- but it is still
// owner-gated because a ValidatingAdmissionPolicy's real CEL rule text is
// operational/security-posture detail, the same sensitivity class as the
// RBAC/NetworkPolicy inventory on /iam and the role assignments on /org.
export default async function PolicyPage() {
  const cookieStore = await cookies();
  const token = cookieStore.get(SESSION_COOKIE_NAME)?.value;
  const session = token ? await verifySessionToken(token) : null;

  const clusterConfigured = hasClusterCredentials();

  if (!session) {
    return (
      <>
        <Nav />
        <main className="mx-auto max-w-4xl px-6 py-10">
          <p className="rounded-md border border-red-900 bg-red-950/40 px-4 py-3 text-sm text-red-300">
            unauthenticated
          </p>
        </main>
      </>
    );
  }

  const access = await requireRole(session, "owner");
  const currentIdentifier = roleIdentifierFor(session);

  return (
    <>
      <Nav />
      <main className="mx-auto max-w-4xl px-6 py-10">
        <h1 className="mb-2 text-2xl font-semibold text-white">Policy as Code</h1>
        <p className="mb-8 max-w-2xl text-sm text-gray-400">
          Real Organization Policy enforcement (AWS Config Rules / GCP Org Policy equivalent)
          using Kubernetes&apos; own native, built-in{" "}
          <code>admissionregistration.k8s.io/v1</code> <code>ValidatingAdmissionPolicy</code>{" "}
          (CEL-based, GA since 1.30) -- not a third-party admission webhook framework, none of
          which is installed on this cluster. The enforcement itself runs entirely inside
          kube-apiserver, on every matching request; this page only reads back what a cluster
          operator already applied via{" "}
          <code>kubectl apply -f k8s/admission-policy.yaml</code>, it does not implement the
          enforcement.
        </p>

        {!clusterConfigured && (
          <div className="mb-6 rounded-md border border-amber-900 bg-amber-950/40 px-4 py-3 text-sm text-amber-300">
            not configured: no in-cluster ServiceAccount credentials found. This page only
            returns real data when running as the platform-console pod.
          </div>
        )}

        {clusterConfigured && !access.ok && (
          <div className="mb-6 rounded-md border border-red-900 bg-red-950/40 px-4 py-3 text-sm text-red-300">
            <p className="font-medium">403 -- forbidden</p>
            <p className="mt-1 text-red-300/80">
              Your role (<code>{access.role}</code>) does not meet the required minimum role (
              <code>owner</code>) for this page. Ask an existing owner to promote your account (
              <code>{currentIdentifier}</code>) via <code>/org</code>.
            </p>
          </div>
        )}

        {clusterConfigured && access.ok && <PolicyServerBoundary />}

        <DenialsDisclosure />
      </main>
    </>
  );
}

async function PolicyServerBoundary() {
  const result = await listActivePolicies();

  if (!result.ok) {
    return (
      <p className="rounded-md border border-red-900 bg-red-950/40 px-4 py-2 text-sm text-red-300">
        {result.error}
      </p>
    );
  }

  const { policies, bindings } = result.data;

  if (policies.length === 0) {
    return (
      <p className="text-sm text-gray-400">
        No <code>ValidatingAdmissionPolicy</code> objects found on this cluster.
      </p>
    );
  }

  return (
    <div className="space-y-8">
      {policies.map((policy) => (
        <PolicyCard
          key={policy.name}
          policy={policy}
          bindings={bindings.filter((b) => b.policyName === policy.name)}
        />
      ))}
    </div>
  );
}

function PolicyCard({
  policy,
  bindings,
}: {
  policy: ActiveValidatingAdmissionPolicy;
  bindings: ActiveValidatingAdmissionPolicyBinding[];
}) {
  return (
    <div className="rounded-md border border-border bg-panel p-5">
      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-lg font-medium text-white">{policy.name}</h2>
        <span className="rounded border border-border px-1.5 py-0.5 text-[10px] text-gray-400">
          failurePolicy: {policy.failurePolicy ?? "(unset)"}
        </span>
      </div>

      <div className="mb-4">
        <p className="mb-1 text-xs uppercase tracking-wide text-gray-500">
          Matches (matchConstraints.resourceRules)
        </p>
        <ul className="space-y-1 text-sm text-gray-300">
          {policy.matchConstraints.map((m, i) => (
            <li key={i}>
              <code>
                {m.apiGroups.join(",") || "core"}/{m.apiVersions.join(",")}{" "}
                {m.resources.join(",")} on {m.operations.join(", ")}
              </code>
            </li>
          ))}
        </ul>
      </div>

      <div className="mb-4">
        <p className="mb-1 text-xs uppercase tracking-wide text-gray-500">
          Real CEL rule (validations[].expression, verbatim)
        </p>
        {policy.validations.map((v, i) => (
          <div key={i} className="mb-2 rounded border border-border bg-black/40 p-3">
            <pre className="whitespace-pre-wrap break-words text-xs text-emerald-300">
              {v.expression}
            </pre>
            {v.message && <p className="mt-2 text-xs text-gray-400">message: {v.message}</p>}
          </div>
        ))}
      </div>

      <div>
        <p className="mb-1 text-xs uppercase tracking-wide text-gray-500">
          Bindings ({bindings.length}) -- real scope this policy is actually enforced against
        </p>
        {bindings.length === 0 && (
          <p className="text-sm text-amber-300">
            no bindings -- this policy is defined but enforces nothing anywhere.
          </p>
        )}
        <ul className="space-y-2">
          {bindings.map((b) => (
            <li key={b.name} className="rounded border border-border p-3 text-sm text-gray-300">
              <p>
                <code>{b.name}</code> -- validationActions:{" "}
                <code>{b.validationActions.join(", ") || "(none)"}</code>
              </p>
              {b.namespaceSelectorRules.length > 0 ? (
                <ul className="mt-1 list-inside list-disc text-xs text-gray-400">
                  {b.namespaceSelectorRules.map((r, i) => (
                    <li key={i}>
                      <code>{r.key}</code> {r.operator} [
                      <code>{r.values.join(", ")}</code>]
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="mt-1 text-xs text-amber-300">
                  no namespaceSelector -- this binding matches ALL namespaces, cluster-wide.
                </p>
              )}
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}

function DenialsDisclosure() {
  return (
    <div className="mt-10 rounded-md border border-amber-900 bg-amber-950/40 px-4 py-3 text-sm text-amber-300">
      <p className="font-medium">Recent denials -- documentation-only, not live-queryable</p>
      <p className="mt-1 text-amber-300/80">
        Kubernetes has no built-in &quot;denial log&quot; API. A ValidatingAdmissionPolicy&apos;s{" "}
        <code>auditAnnotations</code> are written into kube-apiserver&apos;s own audit log stream
        (when audit logging is enabled and configured to capture them) -- not into any object
        this app, or any Kubernetes API, can <code>GET</code>. This cluster does not currently
        ingest kube-apiserver&apos;s audit log anywhere queryable from this console, so a real,
        live &quot;recent denials&quot; list cannot honestly be built here today. Building one
        would require standing up audit-log ingestion (e.g. a webhook backend or a log-file
        sink piped into this console&apos;s own storage) as a separate, disclosed follow-on --
        out of scope for this pass. The real rejection text a denied request actually gets back
        from the API server is reproduced verbatim in{" "}
        <code>README.md</code>&apos;s{" "}
        <code>admission-policy-rejects-noncompliant-deployment</code> control entry, captured
        live at the time this policy was applied.
      </p>
    </div>
  );
}
