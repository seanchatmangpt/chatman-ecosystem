import { cookies } from "next/headers";
import Nav from "@/components/Nav";
import ProjectSubNav from "@/components/ProjectSubNav";
import BudgetPanel from "@/components/BudgetPanel";
import { getProject } from "@/lib/k8s";
import { getProjectBudgetStatus } from "@/lib/quota-enforcement";
import { SESSION_COOKIE_NAME, verifySessionToken } from "@/lib/session";
import { getRoleFor, type Role } from "@/lib/authz";

export const dynamic = "force-dynamic";

const ROLE_RANK: Record<Role, number> = { viewer: 0, member: 1, owner: 2 };

export default async function ProjectSettingsPage({
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

  const cookieStore = await cookies();
  const token = cookieStore.get(SESSION_COOKIE_NAME)?.value;
  const session = token ? await verifySessionToken(token) : null;
  const role: Role = session ? await getRoleFor(session) : "viewer";
  const canEditBudget = ROLE_RANK[role] >= ROLE_RANK.owner;

  const budgetResult = await getProjectBudgetStatus(project.namespace);

  return (
    <>
      <Nav />
      <main className="mx-auto max-w-3xl px-6 py-10">
        <h1 className="mb-2 text-2xl font-semibold text-white">{name}</h1>
        <ProjectSubNav name={name} active="settings" />

        {budgetResult.ok ? (
          <BudgetPanel projectName={name} canEdit={canEditBudget} initialStatus={budgetResult.data} />
        ) : (
          <div className="rounded-md border border-red-900 bg-red-950/40 px-4 py-3 text-sm text-red-300">
            {budgetResult.error}
          </div>
        )}
      </main>
    </>
  );
}
