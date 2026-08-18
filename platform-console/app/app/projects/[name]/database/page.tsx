import { cookies } from "next/headers";
import Nav from "@/components/Nav";
import ProjectSubNav from "@/components/ProjectSubNav";
import RedisCachePanel from "@/components/RedisCachePanel";
import NatsQueuePanel from "@/components/NatsQueuePanel";
import { getProject, listNamespaceServices, type K8sService } from "@/lib/k8s";
import { getRedisStatus } from "@/lib/redis";
import { getQueueStatus } from "@/lib/queue";
import { SESSION_COOKIE_NAME, verifySessionToken } from "@/lib/session";
import { getRoleFor, type Role } from "@/lib/authz";

export const dynamic = "force-dynamic";

const ROLE_RANK: Record<Role, number> = { viewer: 0, member: 1, owner: 2 };

function ServiceCard({ title, service }: { title: string; service: K8sService | undefined }) {
  if (!service) {
    return (
      <div className="card p-6">
        <h2 className="mb-2 text-base font-medium text-white">{title}</h2>
        <p className="text-sm text-gray-500">
          not found: no Service in this namespace matched.
        </p>
      </div>
    );
  }
  return (
    <div className="card p-6">
      <h2 className="mb-4 text-base font-medium text-white">{title}</h2>
      <dl className="divide-y divide-border text-sm">
        <div className="grid grid-cols-3 gap-4 py-2">
          <dt className="text-gray-400">Service DNS</dt>
          <dd className="col-span-2 break-all text-gray-100">{service.dns}</dd>
        </div>
        <div className="grid grid-cols-3 gap-4 py-2">
          <dt className="text-gray-400">Cluster IP</dt>
          <dd className="col-span-2 text-gray-100">{service.clusterIP ?? "-"}</dd>
        </div>
        <div className="grid grid-cols-3 gap-4 py-2">
          <dt className="text-gray-400">Ports</dt>
          <dd className="col-span-2 text-gray-100">
            {service.ports
              .map((p) => `${p.name ? `${p.name}:` : ""}${p.port}/${p.protocol}`)
              .join(", ") || "-"}
          </dd>
        </div>
      </dl>
    </div>
  );
}

export default async function ProjectDatabasePage({
  params,
}: {
  params: Promise<{ name: string }>;
}) {
  const { name } = await params;
  const projectResult = await getProject(name);

  if (!projectResult.ok) {
    return (
      <>
        <Nav />
        <main className="mx-auto max-w-3xl px-6 py-10">
          <h1 className="mb-4 text-2xl font-semibold text-white">{name}</h1>
          <div className="rounded-md border border-red-900 bg-red-950/40 px-4 py-3 text-sm text-red-300">
            {projectResult.error}
          </div>
        </main>
      </>
    );
  }

  const project = projectResult.data;
  if (!project) {
    return (
      <>
        <Nav />
        <main className="mx-auto max-w-3xl px-6 py-10">
          <h1 className="mb-4 text-2xl font-semibold text-white">{name}</h1>
          <p className="text-sm text-gray-400">
            No Project custom resource named <code>{name}</code> was found on
            the cluster.
          </p>
        </main>
      </>
    );
  }

  const servicesResult = await listNamespaceServices(project.namespace);
  const services = servicesResult.ok ? servicesResult.data : [];

  const dbService = services.find(
    (s) =>
      s.labels["app.kubernetes.io/component"] === "database" &&
      (project.databaseRefName ? s.labels["app.kubernetes.io/instance"] === project.databaseRefName : true),
  );
  const restService = services.find(
    (s) =>
      s.labels["app.kubernetes.io/component"] === "rest" &&
      s.labels["app.kubernetes.io/instance"] === project.name,
  );

  const cookieStore = await cookies();
  const token = cookieStore.get(SESSION_COOKIE_NAME)?.value;
  const session = token ? await verifySessionToken(token) : null;
  const role: Role = session ? await getRoleFor(session) : "viewer";
  const canProvisionCache = ROLE_RANK[role] >= ROLE_RANK.owner;
  const canRevealCache = ROLE_RANK[role] >= ROLE_RANK.member;

  const redisStatusResult = await getRedisStatus(project);
  const redisStatus = redisStatusResult.ok
    ? redisStatusResult.data
    : { name: `${project.name}-redis`, namespace: project.namespace, provisioned: false, ready: false, host: "", port: 6379 };

  const queueStatusResult = await getQueueStatus(project);
  const queueStatus = queueStatusResult.ok
    ? queueStatusResult.data
    : { name: `${project.name}-queue`, namespace: project.namespace, provisioned: false, ready: false, host: "", port: 4222 };

  return (
    <>
      <Nav />
      <main className="mx-auto max-w-3xl px-6 py-10">
        <h1 className="mb-1 text-2xl font-semibold text-white">{project.name}</h1>
        <p className="mb-6 text-sm text-gray-500">namespace <code>{project.namespace}</code></p>
        <ProjectSubNav name={project.name} active="database" />

        {!servicesResult.ok && (
          <div className="mb-6 rounded-md border border-red-900 bg-red-950/40 px-4 py-3 text-sm text-red-300">
            {servicesResult.error}
          </div>
        )}

        <div className="space-y-4">
          <ServiceCard title="Postgres" service={dbService} />
          <ServiceCard title="PostgREST" service={restService} />
          <RedisCachePanel
            projectName={project.name}
            canProvision={canProvisionCache}
            canReveal={canRevealCache}
            initialStatus={redisStatus}
          />
          <NatsQueuePanel
            projectName={project.name}
            canProvision={canProvisionCache}
            canReveal={canRevealCache}
            initialStatus={queueStatus}
          />
        </div>
      </main>
    </>
  );
}
