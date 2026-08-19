import Nav from "@/components/Nav";
import CloudLayerDashboard from "@/components/CloudLayerDashboard";
import { getSaasDashboard } from "@/lib/cloud-dashboards";
import { enforceDashboardPostconditions } from "@/lib/dashboard-standing";

export const dynamic = "force-dynamic";

const PROJECT_CAPABILITIES = new Set(["Authentication", "Database", "Storage", "Functions"]);

export default async function SaasPage() {
  const observed = await getSaasDashboard();
  const safeCapabilities = observed.capabilities.map((capability) =>
    capability.state === "UNKNOWN" && PROJECT_CAPABILITIES.has(capability.name)
      ? { ...capability, href: "/projects" }
      : capability,
  );
  const model = enforceDashboardPostconditions(
    { ...observed, capabilities: safeCapabilities },
    [
      { kind: "TenantProject", minimum: 1 },
      { kind: "ApplicationService", minimum: 1 },
    ],
  );

  return (
    <>
      <Nav />
      <CloudLayerDashboard model={model} />
    </>
  );
}
