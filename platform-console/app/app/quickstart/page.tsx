import { cookies, headers } from "next/headers";
import Nav from "@/components/Nav";
import ManifestActions from "@/components/ManifestActions";
import { SESSION_COOKIE_NAME, verifySessionToken } from "@/lib/session";
import { getRoleFor, roleIdentifierFor } from "@/lib/authz";
import { hasClusterCredentials } from "@/lib/k8s";
import { buildQuickstartScript, quickstartProjectName } from "@/lib/quickstart";

export const dynamic = "force-dynamic";

// The AWS CLI getting-started / `gcloud init` / Vercel CLI quickstart
// equivalent for this console: a real, personalized, ready-to-run
// quickstart.sh generated for whoever is viewing this page, tying
// together five modules that already exist (API Keys, Projects, Database
// Backups) into one script instead of leaving a first-time user to find
// each module's page on their own. Session-gated, any role -- the script
// itself is what enforces role requirements (API key / project creation
// are owner-only, the exact same requireRole(session, "owner") gate
// those routes already have), the same honest "the real API decides, not
// this page" pattern /audit's header comment documents for its own
// owner-only data.
export default async function QuickstartPage() {
  const cookieStore = await cookies();
  const token = cookieStore.get(SESSION_COOKIE_NAME)?.value;
  const session = token ? await verifySessionToken(token) : null;

  if (!session || !token) {
    return (
      <>
        <Nav />
        <main className="mx-auto max-w-3xl px-6 py-10">
          <p className="rounded-md border border-red-900 bg-red-950/40 px-4 py-3 text-sm text-red-300">
            unauthenticated
          </p>
        </main>
      </>
    );
  }

  const clusterConfigured = hasClusterCredentials();

  const shell = (body: React.ReactNode) => (
    <>
      <Nav />
      <main className="mx-auto max-w-4xl px-6 py-10">
        <h1 className="mb-2 text-2xl font-semibold text-white">Quickstart</h1>
        <p className="mb-8 max-w-2xl text-sm text-gray-400">
          Get started in five minutes, the same way <code>aws configure</code>,{" "}
          <code>gcloud init</code>, or the Vercel CLI would: a personalized{" "}
          <code>quickstart.sh</code> that creates a real API key, provisions a real project,
          waits for it to reach real <code>Ready</code> status, backs it up, and cleans up --
          five real curl calls against this deployment&apos;s own real HTTP API, nothing
          simulated.
        </p>
        {body}
      </main>
    </>
  );

  if (!clusterConfigured) {
    return shell(
      <div className="rounded-md border border-amber-900 bg-amber-950/40 px-4 py-3 text-sm text-amber-300">
        not configured: no in-cluster ServiceAccount credentials found. This page only
        generates a real, working script when running as the platform-console pod.
      </div>,
    );
  }

  const role = await getRoleFor(session);
  const identifier = roleIdentifierFor(session);

  const headerList = await headers();
  const host = headerList.get("x-forwarded-host") ?? headerList.get("host") ?? "platform.local";
  // This deployment terminates plain HTTP at the Istio Gateway (README's
  // "How to reach it" -- http://platform.local, no TLS gateway for the
  // console itself); x-forwarded-proto is honored if a proxy in front of
  // that ever sets one, so this keeps working if that changes.
  const protocol = headerList.get("x-forwarded-proto") ?? "http";
  const baseUrl = `${protocol}://${host}`;

  const generatedAt = new Date().toISOString();
  const script = buildQuickstartScript({
    baseUrl,
    sessionCookie: token,
    identifier,
    role,
    generatedAt,
  });
  const projectName = quickstartProjectName({ identifier, generatedAt });

  return shell(
    <>
      <div className="mb-6 card p-6">
        <dl className="grid grid-cols-2 gap-4 text-sm sm:grid-cols-4">
          <div>
            <dt className="text-gray-500">Generated for</dt>
            <dd className="text-white">
              <code>{identifier}</code>
            </dd>
          </div>
          <div>
            <dt className="text-gray-500">Role</dt>
            <dd className="text-white">
              <code>{role}</code>
            </dd>
          </div>
          <div>
            <dt className="text-gray-500">Base URL</dt>
            <dd className="text-white">
              <code>{baseUrl}</code>
            </dd>
          </div>
          <div>
            <dt className="text-gray-500">Demo project name</dt>
            <dd className="text-white">
              <code>{projectName}</code>
            </dd>
          </div>
        </dl>
        {role !== "owner" && (
          <p className="mt-4 rounded-md border border-amber-900 bg-amber-950/40 px-3 py-2 text-xs text-amber-300">
            Your role is <code>{role}</code>. Creating an API key and creating a project are
            owner-only actions (the same real RBAC every other module in this console
            enforces) -- running this script will get a real 403 at step 1 unless you run it
            from an owner account. The script is still real and still yours to inspect.
          </p>
        )}
      </div>

      <div className="mb-6 card p-6">
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-base font-medium text-white">quickstart.sh</h2>
          <ManifestActions
            yamlText={script}
            fileName="quickstart.sh"
            copyLabel="Copy script"
            mimeType="text/x-sh"
          />
        </div>
        <p className="mb-3 text-xs text-gray-500">
          Regenerated fresh on every page load (a new project name, a fresh copy of your
          current session). Run it with <code>bash quickstart.sh</code> -- requires only{" "}
          <code>bash</code>, <code>curl</code>, and <code>jq</code>.
        </p>
        <div className="overflow-x-auto rounded-md border border-border bg-black/40">
          <pre className="max-h-[36rem] overflow-y-auto p-4 text-xs text-gray-300">
            <code>{script}</code>
          </pre>
        </div>
      </div>

      <div className="card p-6 text-sm text-gray-400">
        <h2 className="mb-2 text-base font-medium text-white">What each step calls</h2>
        <ol className="list-decimal space-y-1 pl-5">
          <li>
            <code>POST /api/api-keys</code> -- API Keys module (<code>/api-keys</code>)
          </li>
          <li>
            <code>POST /api/projects</code> -- self-service Projects module (
            <code>/projects</code>)
          </li>
          <li>
            <code>GET /api/projects</code> (polled) -- real{" "}
            <code>status.conditions[Ready]</code>
          </li>
          <li>
            <code>POST /api/projects/&#123;name&#125;/backups</code> -- Database Backups
            module
          </li>
          <li>
            <code>DELETE /api/projects/&#123;name&#125;</code> -- real cleanup
          </li>
        </ol>
      </div>
    </>,
  );
}
