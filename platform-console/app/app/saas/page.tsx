import Nav from "@/components/Nav";
import CloudLayerDashboard from "@/components/CloudLayerDashboard";
import { getSaasDashboard } from "@/lib/cloud-dashboards";

export const dynamic = "force-dynamic";

export default async function SaasPage() {
  const model = await getSaasDashboard();
  return (
    <>
      <Nav />
      <CloudLayerDashboard model={model} />
    </>
  );
}
