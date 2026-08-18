import Nav from "@/components/Nav";
import CloudLayerDashboard from "@/components/CloudLayerDashboard";
import { getIaasDashboard } from "@/lib/cloud-dashboards";
import { enforceDashboardPostconditions } from "@/lib/dashboard-standing";

export const dynamic = "force-dynamic";

export default async function IaasPage() {
  const observed = await getIaasDashboard();
  const model = enforceDashboardPostconditions(observed, [
    { kind: "Deployment", minimum: 1 },
    { kind: "Pod", minimum: 1 },
  ]);

  return (
    <>
      <Nav />
      <CloudLayerDashboard model={model} />
    </>
  );
}
