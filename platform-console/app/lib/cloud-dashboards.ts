import type { DashboardModel, DashboardResource, DashboardStanding } from "@/components/CloudLayerDashboard";
import {
  getBackupsPvc,
  listDeployments,
  listHelmReleases,
  listJobs,
  listKustomizations,
  listNamespaceServices,
  listNamespaces,
  listNetworkPolicies,
  listPods,
  listProjects,
  listRoleBindings,
  listRoles,
  listSecrets,
} from "@/lib/k8s";

const PAAS_NAMESPACE = "supabase-demo";
const BACKUPS_PVC = "platform-backups-pvc";
const SYSTEM_NAMESPACES = new Set(["kube-system", "kube-public", "kube-node-lease"]);

type ResultLike<T> = { ok: true; data: T } | { ok: false; error: string };

function observe<T>(label: string, result: ResultLike<T>, errors: string[]): result is { ok: true; data: T } {
  if (!result.ok) errors.push(`${label}: ${result.error}`);
  return result.ok;
}

function deriveStanding(successes: number, errors: string[]): DashboardStanding {
  if (successes === 0) return errors.length > 0 ? "BLOCKED" : "UNKNOWN";
  return errors.length === 0 ? "ALIVE" : "PARTIAL_ALIVE";
}

function ratio(ready: number, total: number): string {
  return total === 0 ? "0" : `${ready}/${total}`;
}

export async function getIaasDashboard(): Promise<DashboardModel> {
  const errors: string[] = [];
  let successes = 0;
  const [namespacesResult, policiesResult, rolesResult, bindingsResult, kustomizationsResult, helmResult] =
    await Promise.all([
      listNamespaces(),
      listNetworkPolicies(),
      listRoles(),
      listRoleBindings(),
      listKustomizations(),
      listHelmReleases(),
    ]);

  const namespaces = observe("namespaces", namespacesResult, errors) ? namespacesResult.data : [];
  if (namespacesResult.ok) successes++;
  const policies = observe("network policies", policiesResult, errors) ? policiesResult.data : [];
  if (policiesResult.ok) successes++;
  const roles = observe("roles", rolesResult, errors) ? rolesResult.data : [];
  if (rolesResult.ok) successes++;
  const bindings = observe("role bindings", bindingsResult, errors) ? bindingsResult.data : [];
  if (bindingsResult.ok) successes++;
  const kustomizations = observe("Flux Kustomizations", kustomizationsResult, errors)
    ? kustomizationsResult.data
    : [];
  if (kustomizationsResult.ok) successes++;
  const helm = observe("Flux HelmReleases", helmResult, errors) ? helmResult.data : [];
  if (helmResult.ok) successes++;

  const workloadNamespaces = namespaces.filter((namespace) => !SYSTEM_NAMESPACES.has(namespace));
  const namespaceObservations = await Promise.all(
    workloadNamespaces.map(async (namespace) => {
      const [deployments, services, pods] = await Promise.all([
        listDeployments(namespace),
        listNamespaceServices(namespace),
        listPods(namespace),
      ]);
      return { namespace, deployments, services, pods };
    }),
  );

  const resources: DashboardResource[] = [];
  let deploymentCount = 0;
  let desiredReplicas = 0;
  let readyReplicas = 0;
  let serviceCount = 0;
  let podCount = 0;
  let readyPods = 0;

  for (const observation of namespaceObservations) {
    const { namespace } = observation;
    if (observe(`deployments/${namespace}`, observation.deployments, errors)) {
      successes++;
      for (const deployment of observation.deployments.data) {
        deploymentCount++;
        desiredReplicas += deployment.replicasDesired;
        readyReplicas += deployment.replicasReady;
        resources.push({
          kind: "Deployment",
          name: deployment.name,
          namespace,
          state:
            deployment.replicasDesired > 0 && deployment.replicasReady === deployment.replicasDesired
              ? "READY"
              : "DEGRADED",
          detail: `${deployment.replicasReady}/${deployment.replicasDesired} replicas ready; ${deployment.containers
            .map((container) => `${container.name}=${container.image}`)
            .join(", ") || "no containers reported"}`,
        });
      }
    }
    if (observe(`services/${namespace}`, observation.services, errors)) {
      successes++;
      serviceCount += observation.services.data.length;
      for (const service of observation.services.data) {
        resources.push({
          kind: "Service",
          name: service.name,
          namespace,
          state: service.clusterIP ? "LIVE" : "UNKNOWN",
          detail: `${service.dns}; ${service.ports.map((port) => `${port.port}/${port.protocol}`).join(", ") || "no ports"}`,
        });
      }
    }
    if (observe(`pods/${namespace}`, observation.pods, errors)) {
      successes++;
      podCount += observation.pods.data.length;
      readyPods += observation.pods.data.filter((pod) => pod.ready).length;
      for (const pod of observation.pods.data) {
        resources.push({
          kind: "Pod",
          name: pod.name,
          namespace,
          state: pod.ready ? "READY" : pod.phase,
          detail: `${pod.phase}; containers=${pod.containers.join(", ") || "none"}`,
        });
      }
    }
  }

  for (const policy of policies) {
    resources.push({
      kind: "NetworkPolicy",
      name: policy.name,
      namespace: policy.namespace,
      state: "LIVE",
      detail: `policyTypes=${policy.policyTypes.join(", ") || "unspecified"}`,
    });
  }

  const fluxReady = [...kustomizations, ...helm].filter((resource) => resource.ready === true).length;
  const fluxTotal = kustomizations.length + helm.length;

  return {
    layer: "IaaS",
    title: "Infrastructure Control Plane",
    subtitle:
      "A live substrate view over namespaces, workloads, services, network policy, identity boundaries and GitOps reconciliation. The dashboard treats infrastructure as an observable projection: unavailable API evidence stays unavailable instead of being replaced by synthetic cloud telemetry.",
    scope: "Kubernetes API + Flux CRDs + namespaced workload state",
    standing: deriveStanding(successes, errors),
    capturedAt: new Date().toISOString(),
    metrics: [
      {
        label: "Workload namespaces",
        value: String(workloadNamespaces.length),
        detail: `${namespaces.length} total namespaces observed; Kubernetes system namespaces excluded from workload count.`,
        tone: workloadNamespaces.length > 0 ? "good" : "neutral",
      },
      {
        label: "Replica readiness",
        value: ratio(readyReplicas, desiredReplicas),
        detail: `${deploymentCount} deployments across the observed workload namespaces.`,
        tone: desiredReplicas > 0 && readyReplicas === desiredReplicas ? "good" : "warn",
      },
      {
        label: "Pod readiness",
        value: ratio(readyPods, podCount),
        detail: `${serviceCount} Services and ${policies.length} NetworkPolicies observed.`,
        tone: podCount > 0 && readyPods === podCount ? "good" : "warn",
      },
      {
        label: "GitOps reconciliation",
        value: ratio(fluxReady, fluxTotal),
        detail: `${kustomizations.length} Kustomizations + ${helm.length} HelmReleases; IAM=${roles.length} Roles/${bindings.length} bindings.`,
        tone: fluxTotal > 0 && fluxReady === fluxTotal ? "good" : "warn",
      },
    ],
    resources,
    capabilities: [
      {
        name: "GitOps",
        href: "/gitops",
        state: kustomizationsResult.ok && helmResult.ok ? "LIVE" : "UNKNOWN",
        description: "Flux reconciliation state for declared infrastructure and platform packages.",
        evidence: "kustomize.toolkit.fluxcd.io + helm.toolkit.fluxcd.io",
      },
      {
        name: "IAM",
        href: "/iam",
        state: rolesResult.ok && bindingsResult.ok ? "LIVE" : "UNKNOWN",
        description: "Namespaced RBAC and network-policy authority surfaces.",
        evidence: "rbac.authorization.k8s.io + networking.k8s.io",
      },
      {
        name: "Observability",
        href: "/observability",
        state: "LIVE",
        description: "Prometheus/Grafana substrate telemetry exposed through the existing monitoring module.",
        evidence: "existing /observability live Prometheus query path",
      },
      {
        name: "Container Registry",
        href: "/registry",
        state: "LIVE",
        description: "Runtime-resolved image inventory and pull evidence from Kubernetes container status.",
        evidence: "Deployment specs + Pod containerStatuses.imageID",
      },
      {
        name: "Logs",
        href: "/logs",
        state: "LIVE",
        description: "Direct pod stdout/stderr observation through the Kubernetes log subresource.",
        evidence: "GET pods/{pod}/log",
      },
      {
        name: "Compliance",
        href: "/compliance",
        state: "LIVE",
        description: "Control evidence and policy posture over the active infrastructure surface.",
        evidence: "platform-console evidence/control-evidence-bundle.json",
      },
    ],
    flow: ["Observe substrate", "Admit desired graph", "Construct manifests", "BRCE actuation", "Receipt state", "Replay/reconstitute"],
    errors,
  };
}

export async function getPaasDashboard(): Promise<DashboardModel> {
  const errors: string[] = [];
  let successes = 0;
  const [projectsResult, deploymentsResult, servicesResult, podsResult, secretsResult, backupsResult, pvcResult, kustomizationsResult, helmResult] =
    await Promise.all([
      listProjects(),
      listDeployments(PAAS_NAMESPACE),
      listNamespaceServices(PAAS_NAMESPACE),
      listPods(PAAS_NAMESPACE),
      listSecrets(PAAS_NAMESPACE),
      listJobs(PAAS_NAMESPACE, "app=platform-backups"),
      getBackupsPvc(PAAS_NAMESPACE, BACKUPS_PVC),
      listKustomizations(),
      listHelmReleases(),
    ]);

  const projects = observe("projects", projectsResult, errors) ? projectsResult.data : [];
  if (projectsResult.ok) successes++;
  const deployments = observe(`deployments/${PAAS_NAMESPACE}`, deploymentsResult, errors)
    ? deploymentsResult.data
    : [];
  if (deploymentsResult.ok) successes++;
  const services = observe(`services/${PAAS_NAMESPACE}`, servicesResult, errors) ? servicesResult.data : [];
  if (servicesResult.ok) successes++;
  const pods = observe(`pods/${PAAS_NAMESPACE}`, podsResult, errors) ? podsResult.data : [];
  if (podsResult.ok) successes++;
  const secrets = observe(`secrets/${PAAS_NAMESPACE}`, secretsResult, errors) ? secretsResult.data : [];
  if (secretsResult.ok) successes++;
  const backups = observe(`backups/${PAAS_NAMESPACE}`, backupsResult, errors) ? backupsResult.data : [];
  if (backupsResult.ok) successes++;
  const pvc = observe(`backup-pvc/${PAAS_NAMESPACE}`, pvcResult, errors) ? pvcResult.data : null;
  if (pvcResult.ok) successes++;
  const kustomizations = observe("Flux Kustomizations", kustomizationsResult, errors)
    ? kustomizationsResult.data
    : [];
  if (kustomizationsResult.ok) successes++;
  const helm = observe("Flux HelmReleases", helmResult, errors) ? helmResult.data : [];
  if (helmResult.ok) successes++;

  const readyProjects = projects.filter((project) => project.ready === true).length;
  const desiredReplicas = deployments.reduce((sum, deployment) => sum + deployment.replicasDesired, 0);
  const readyReplicas = deployments.reduce((sum, deployment) => sum + deployment.replicasReady, 0);
  const readyPods = pods.filter((pod) => pod.ready).length;
  const completedBackups = backups.filter((backup) => backup.status === "Complete").length;
  const flux = [...kustomizations, ...helm];
  const readyFlux = flux.filter((resource) => resource.ready === true).length;

  const resources: DashboardResource[] = [
    ...projects.map((project) => ({
      kind: "Project",
      name: project.name,
      namespace: project.namespace,
      state: project.ready === true ? "READY" : project.ready === false ? "DEGRADED" : "UNKNOWN",
      detail: `database=${project.databaseRefName ?? "unreported"}; hostname=${project.hostname ?? "unreported"}; ${project.reason ?? "no Ready reason"}`,
      href: `/projects/${encodeURIComponent(project.name)}`,
    })),
    ...deployments.map((deployment) => ({
      kind: "Deployment",
      name: deployment.name,
      namespace: deployment.namespace,
      state:
        deployment.replicasDesired > 0 && deployment.replicasReady === deployment.replicasDesired
          ? "READY"
          : "DEGRADED",
      detail: `${deployment.replicasReady}/${deployment.replicasDesired} replicas ready`,
    })),
    ...backups.map((backup) => ({
      kind: "BackupJob",
      name: backup.name,
      namespace: backup.namespace,
      state: backup.status,
      detail: `created=${backup.createdAt}; duration=${backup.durationSeconds ?? "unreported"}s`,
      href: "/backups",
    })),
  ];

  if (pvc) {
    resources.push({
      kind: "PersistentVolumeClaim",
      name: pvc.name,
      namespace: pvc.namespace,
      state: pvc.phase ?? "UNKNOWN",
      detail: `capacity=${pvc.capacity ?? "unreported"}; storageClass=${pvc.storageClassName ?? "unreported"}`,
      href: "/backups",
    });
  }

  return {
    layer: "PaaS",
    title: "Platform Capability Plane",
    subtitle:
      "A managed-platform view that composes real project CRDs, workloads, services, secret metadata, database backup jobs and GitOps operators. The page exposes the operational primitives normally split across managed databases, secrets managers, registries, logging, deployment and platform portals.",
    scope: `Supabase operator + Kubernetes namespace ${PAAS_NAMESPACE} + Flux reconciliation`,
    standing: deriveStanding(successes, errors),
    capturedAt: new Date().toISOString(),
    metrics: [
      {
        label: "Managed projects",
        value: ratio(readyProjects, projects.length),
        detail: "Project readiness comes from the operator's live Ready condition.",
        tone: projects.length > 0 && readyProjects === projects.length ? "good" : "warn",
      },
      {
        label: "Platform replicas",
        value: ratio(readyReplicas, desiredReplicas),
        detail: `${deployments.length} deployments; pod readiness ${ratio(readyPods, pods.length)}.`,
        tone: desiredReplicas > 0 && readyReplicas === desiredReplicas ? "good" : "warn",
      },
      {
        label: "Managed primitives",
        value: `${services.length + secrets.length}`,
        detail: `${services.length} Services + ${secrets.length} Opaque Secret metadata records; secret values never leave Kubernetes.`,
        tone: servicesResult.ok && secretsResult.ok ? "good" : "warn",
      },
      {
        label: "Recovery + GitOps",
        value: `${completedBackups} / ${ratio(readyFlux, flux.length)}`,
        detail: `${completedBackups} completed backup Jobs; GitOps value is ready/total reconciler objects.`,
        tone: backupsResult.ok && kustomizationsResult.ok && helmResult.ok ? "good" : "warn",
      },
    ],
    resources,
    capabilities: [
      {
        name: "Projects",
        href: "/projects",
        state: projectsResult.ok ? "LIVE" : "UNKNOWN",
        description: "Create and inspect real operator-backed application projects and paired databases.",
        evidence: "core.supabase.io/v1alpha1 Project + SingleDatabase",
      },
      {
        name: "Secrets Manager",
        href: "/secrets",
        state: secretsResult.ok ? "LIVE" : "UNKNOWN",
        description: "Namespaced secret lifecycle with values kept out of list/readback surfaces.",
        evidence: "Kubernetes Opaque Secret metadata; no value projection",
      },
      {
        name: "Database Backups",
        href: "/backups",
        state: backupsResult.ok ? "LIVE" : "UNKNOWN",
        description: "On-demand pg_dump Jobs writing to a real persistent backup volume.",
        evidence: "batch/v1 Jobs + PersistentVolumeClaim",
      },
      {
        name: "Registry",
        href: "/registry",
        state: deploymentsResult.ok && podsResult.ok ? "LIVE" : "UNKNOWN",
        description: "Image inventory grounded in desired Deployment images and runtime-resolved image IDs.",
        evidence: "apps/v1 Deployments + Pod containerStatuses",
      },
      {
        name: "Logs + Metrics",
        href: "/observability",
        state: podsResult.ok ? "LIVE" : "UNKNOWN",
        description: "Application runtime evidence through pod logs and Prometheus/Grafana telemetry.",
        evidence: "pods/log + Prometheus query API",
      },
      {
        name: "GitOps Delivery",
        href: "/gitops",
        state: kustomizationsResult.ok && helmResult.ok ? "LIVE" : "UNKNOWN",
        description: "Declared-state reconciliation for platform packages and deployment topology.",
        evidence: "Flux Kustomization + HelmRelease Ready conditions",
      },
    ],
    flow: ["Admit capability", "Resolve project graph", "Construct runtime", "Operator reconcile", "Receipt health", "Recover/replay"],
    errors,
  };
}

export async function getSaasDashboard(): Promise<DashboardModel> {
  const errors: string[] = [];
  let successes = 0;
  const [projectsResult, servicesResult, podsResult, backupsResult] = await Promise.all([
    listProjects(),
    listNamespaceServices(PAAS_NAMESPACE),
    listPods(PAAS_NAMESPACE),
    listJobs(PAAS_NAMESPACE, "app=platform-backups"),
  ]);

  const projects = observe("projects", projectsResult, errors) ? projectsResult.data : [];
  if (projectsResult.ok) successes++;
  const services = observe(`services/${PAAS_NAMESPACE}`, servicesResult, errors) ? servicesResult.data : [];
  if (servicesResult.ok) successes++;
  const pods = observe(`pods/${PAAS_NAMESPACE}`, podsResult, errors) ? podsResult.data : [];
  if (podsResult.ok) successes++;
  const backups = observe(`backups/${PAAS_NAMESPACE}`, backupsResult, errors) ? backupsResult.data : [];
  if (backupsResult.ok) successes++;

  const readyProjects = projects.filter((project) => project.ready === true).length;
  const routableProjects = projects.filter((project) => Boolean(project.hostname)).length;
  const readyPods = pods.filter((pod) => pod.ready).length;
  const completedBackups = backups.filter((backup) => backup.status === "Complete").length;
  const primaryProject = projects[0]?.name;
  const projectBase = primaryProject ? `/projects/${encodeURIComponent(primaryProject)}` : "/projects";

  const resources: DashboardResource[] = projects.map((project) => ({
    kind: "TenantProject",
    name: project.name,
    namespace: project.namespace,
    state: project.ready === true ? "READY" : project.ready === false ? "DEGRADED" : "UNKNOWN",
    detail: `hostname=${project.hostname ?? "unreported"}; database=${project.databaseRefName ?? "unreported"}; reason=${project.reason ?? "none"}`,
    href: `/projects/${encodeURIComponent(project.name)}`,
  }));

  for (const service of services) {
    resources.push({
      kind: "ApplicationService",
      name: service.name,
      namespace: service.namespace,
      state: service.clusterIP ? "LIVE" : "UNKNOWN",
      detail: `${service.dns}; ports=${service.ports.map((port) => port.port).join(", ") || "none"}`,
    });
  }

  return {
    layer: "SaaS",
    title: "Application Experience Plane",
    subtitle:
      "A tenant-facing view over provisioned application projects and their auth, data, storage and function capabilities. SaaS here is not a separate pile of hand-owned infrastructure: the application surface is traced back to the same admitted platform/runtime objects and can expose its operational evidence without hiding the lower layers.",
    scope: "Project CRDs + application Services + runtime Pods + recovery evidence",
    standing: deriveStanding(successes, errors),
    capturedAt: new Date().toISOString(),
    metrics: [
      {
        label: "Tenant readiness",
        value: ratio(readyProjects, projects.length),
        detail: "Ready/total managed application projects from the operator status condition.",
        tone: projects.length > 0 && readyProjects === projects.length ? "good" : "warn",
      },
      {
        label: "Routable applications",
        value: ratio(routableProjects, projects.length),
        detail: "Projects with a live hostname reported by their admitted Project specification.",
        tone: projects.length > 0 && routableProjects === projects.length ? "good" : "warn",
      },
      {
        label: "Runtime readiness",
        value: ratio(readyPods, pods.length),
        detail: `${services.length} application-facing Services observed in ${PAAS_NAMESPACE}.`,
        tone: pods.length > 0 && readyPods === pods.length ? "good" : "warn",
      },
      {
        label: "Recovery evidence",
        value: String(completedBackups),
        detail: "Completed real database backup Jobs available underneath the application surface.",
        tone: backupsResult.ok ? "good" : "warn",
      },
    ],
    resources,
    capabilities: [
      {
        name: "Tenant / Project Console",
        href: "/projects",
        state: projectsResult.ok ? "LIVE" : "UNKNOWN",
        description: "Application tenancy, provisioning status and project-level navigation.",
        evidence: "Project CRD name/namespace/Ready/hostname",
      },
      {
        name: "Authentication",
        href: `${projectBase}/auth`,
        state: primaryProject ? "LIVE" : "UNKNOWN",
        description: "Tenant authentication capability projected from the selected live project.",
        evidence: primaryProject ? `project=${primaryProject}` : "no project observed",
      },
      {
        name: "Database",
        href: `${projectBase}/database`,
        state: primaryProject ? "LIVE" : "UNKNOWN",
        description: "Managed application data plane with explicit backing database identity.",
        evidence: primaryProject ? `project=${primaryProject}` : "no project observed",
      },
      {
        name: "Storage",
        href: `${projectBase}/storage`,
        state: primaryProject ? "LIVE" : "UNKNOWN",
        description: "Tenant object/storage capability reached through the project surface.",
        evidence: primaryProject ? `project=${primaryProject}` : "no project observed",
      },
      {
        name: "Functions",
        href: `${projectBase}/functions`,
        state: primaryProject ? "LIVE" : "UNKNOWN",
        description: "Application function capability anchored to the same tenant/project subject.",
        evidence: primaryProject ? `project=${primaryProject}` : "no project observed",
      },
      {
        name: "Compliance + Commercial",
        href: "/compliance",
        state: "LIVE",
        description: "Expose control evidence and service-plan boundaries without disconnecting them from runtime truth.",
        evidence: "existing compliance evidence + pricing surfaces",
      },
    ],
    flow: ["User intent", "Tenant identity", "Capability projection", "Policy/admission", "Runtime service", "Evidence/recovery"],
    errors,
  };
}
