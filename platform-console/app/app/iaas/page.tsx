import Nav from "@/components/Nav";
import CloudLayerDashboard from "@/components/CloudLayerDashboard";
import { getIaasDashboard } from "@/lib/cloud-dashboards";

export const dynamic = "force-dynamic";

export default async function IaasPage() {
  const model = await getIaasDashboard();
  return (
    <>
      <Nav />
      <CloudLayerDashboard model={model} />
    </>
  );
}
