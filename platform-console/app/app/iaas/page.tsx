import Nav from "@/components/Nav";
import CloudLayerDashboard from "@/components/CloudLayerDashboard";
import { getIaasDashboard } from "@/lib/cloud-dashboards";
import { enforceDashboardPostconditions } from "@/lib/dashboard-standing";

export const dynamic = "force-dynamic";

export default async function IaasPage() {
  const observed = await getIaasDashboard();
  const withGateway = {
    ...observed,
    capabilities: [
      ...observed.capabilities,
      {
        name: "API Gateway",
        href: "/api-gateway",
        state: "AVAILABLE",
        description:
          "Ingress throttling and route isolation enforced by the Istio data plane, surfaced here without duplicating the gateway policy.",
        evidence: "platform-console/k8s/ratelimit.yaml + platform-console/k8s/gateway.yaml",
      },
    ],
  };
  const model = enforceDashboardPostconditions(withGateway, [
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
