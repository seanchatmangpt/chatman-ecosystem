import Nav from "@/components/Nav";
import CloudLayerDashboard from "@/components/CloudLayerDashboard";
import { getPaasDashboard } from "@/lib/cloud-dashboards";

export const dynamic = "force-dynamic";

export default async function PaasPage() {
  const model = await getPaasDashboard();
  return (
    <>
      <Nav />
      <CloudLayerDashboard model={model} />
    </>
  );
}
