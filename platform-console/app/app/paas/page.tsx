import Nav from "@/components/Nav";
import CloudLayerDashboard from "@/components/CloudLayerDashboard";
import { getPaasDashboard } from "@/lib/cloud-dashboards";
import { enforceDashboardPostconditions } from "@/lib/dashboard-standing";

export const dynamic = "force-dynamic";

export default async function PaasPage() {
  const observed = await getPaasDashboard();
  const model = enforceDashboardPostconditions(observed, [
    { kind: "Project", minimum: 1 },
    { kind: "Deployment", minimum: 1 },
  ]);

  return (
    <>
      <Nav />
      <CloudLayerDashboard model={model} />
    </>
  );
}
