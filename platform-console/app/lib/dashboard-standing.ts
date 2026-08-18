import type { DashboardModel, DashboardStanding } from "@/components/CloudLayerDashboard";

const HEALTHY_STATES = new Set(["ALIVE", "COMPLETE", "LIVE", "READY", "RUNNING"]);

export interface StandingGuard {
  kind: string;
  minimum: number;
}

/**
 * Applies postcondition evidence after a dashboard has successfully observed
 * its sources. API readability is not health: an observation-only ALIVE view
 * is demoted to PARTIAL_ALIVE when a required resource class is absent or any
 * observed resource in that class reports a non-healthy state.
 *
 * Existing BLOCKED / UNKNOWN / PARTIAL_ALIVE standing is never promoted here.
 */
export function enforceDashboardPostconditions(
  model: DashboardModel,
  guards: StandingGuard[],
): DashboardModel {
  if (model.standing !== "ALIVE") return model;

  const failures: string[] = [];
  for (const guard of guards) {
    const resources = model.resources.filter((resource) => resource.kind === guard.kind);
    if (resources.length < guard.minimum) {
      failures.push(
        `postcondition/${guard.kind}: observed ${resources.length}, require at least ${guard.minimum}`,
      );
      continue;
    }

    const unhealthy = resources.filter(
      (resource) => !HEALTHY_STATES.has(resource.state.toUpperCase()),
    );
    if (unhealthy.length > 0) {
      failures.push(
        `postcondition/${guard.kind}: ${unhealthy.length}/${resources.length} resource(s) are not healthy (${unhealthy
          .slice(0, 4)
          .map((resource) => `${resource.name}=${resource.state}`)
          .join(", ")}${unhealthy.length > 4 ? ", …" : ""})`,
      );
    }
  }

  if (failures.length === 0) return model;

  const standing: DashboardStanding = "PARTIAL_ALIVE";
  return {
    ...model,
    standing,
    errors: [...model.errors, ...failures],
  };
}
