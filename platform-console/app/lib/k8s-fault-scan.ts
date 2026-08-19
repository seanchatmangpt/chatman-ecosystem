/**
 * K8s Fault Diagnosis via autofde-lab's real, already-tested structural-
 * anomaly scanner (`autofde_lab_planner.scanner.registry.scan` +
 * `.taxonomy.classify`, checked out locally at `AUTOFDE_LAB_PROJECT_DIR`,
 * default `/Users/sac/autofde-lab`).
 *
 * autofde-lab's scanner has NO existing CLI entrypoint or subprocess
 * boundary of its own -- it is exercised exclusively as an in-process
 * Python function call (`scan(cluster_state_dict)`), verified live: 24/24
 * tests in tests/scanner/ pass, zero mocks, real dict-in/dataclass-out. A
 * minimal stdin/stdout CLI shim,
 * `src/autofde_lab_planner/scanner/__main__.py`, was added to that repo
 * alongside this file specifically to give this console a stable
 * process boundary to shell out to -- it adds no new diagnostic logic
 * itself, it is a thin I/O wrapper over the already-tested `scan()` +
 * `classify()`, and is itself covered by a real subprocess test
 * (tests/scanner/test_cli_chicago.py, 4/4 passing).
 *
 * Same "shell out, write a tmp JSON file, parse real stdout JSON, fail
 * closed" bridge discipline lib/mermaid.ts's `renderFlowchart` already
 * established for mmdio, and the same single-fixed-invocation allowlist
 * discipline lib/castle.ts's `ALLOWED_CASTLE_VERBS` established for
 * castle -- there is exactly one real invocation this module will ever
 * make (`.venv/bin/python -m autofde_lab_planner.scanner --state-file
 * <tmpfile>`), no user-supplied text is ever interpolated into that
 * argv, and there is no code path that could construct a different
 * command even if the caller tried.
 *
 * IMPORTANT, stated plainly per this integration's own scope: the
 * underlying scanner DIAGNOSES (produces structured `Anomaly` records
 * plus a best-effort SREGym fault-taxonomy label or `UNCLASSIFIED`) --
 * it does not REMEDIATE. No code in autofde-lab or in this module
 * generates a fix. `filings` below are approval REQUESTS a human must
 * still approve before any actual remediation action is taken by a
 * separate, unrelated system -- this module never actuates anything.
 *
 * Runs on the Node.js runtime only (uses `node:child_process`), same
 * constraint as lib/k8s.ts, lib/container-exec.ts, and lib/mermaid.ts.
 */
import { spawnSync } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { k8sRequest, type K8sResult } from "./k8s";

const AUTOFDE_LAB_PROJECT_DIR =
  process.env.AUTOFDE_LAB_PROJECT_DIR ?? "/Users/sac/autofde-lab";
const AUTOFDE_LAB_PYTHON =
  process.env.AUTOFDE_LAB_PYTHON ?? path.join(AUTOFDE_LAB_PROJECT_DIR, ".venv/bin/python");
const SCAN_TIMEOUT_MS = 15_000;

/** Relation classes the real `Anomaly.relation_class` field can carry --
 * mirrored 1:1 from autofde-lab's `RelationClass` Literal
 * (src/autofde_lab_planner/scanner/models.py), never invented here. */
export type K8sFaultRelationClass =
  | "declared_vs_observed"
  | "dangling_reference"
  | "insufficient_capability"
  | "aggregate_threshold";

/** One structural anomaly, shaped exactly like the real CLI's per-finding
 * JSON object (Anomaly dataclass fields + the `taxonomy` field the CLI
 * shim adds from `classify()`). */
export interface K8sFaultFinding {
  kind: string;
  object_name: string;
  namespace: string;
  relation_class: K8sFaultRelationClass;
  field: string;
  observed: string;
  expected: string | null;
  detail: string;
  /** A real SREGym `inject_*` fault-injector method name, or the literal
   * string `"UNCLASSIFIED"` when autofde-lab's `classify()` could not
   * match a known signature -- never guessed. */
  taxonomy: string;
}

/** ClusterState is a `dict` shaped exactly like one or more
 * `kubectl get <kind> -o json` responses, keyed by lowercase-plural kind
 * name -- mirrors autofde-lab's `ClusterState` TypedDict
 * (src/autofde_lab_planner/scanner/registry.py). Each value may be a
 * `{"items": [...]}` list-response, a raw array, or a single object --
 * the Python side's `_items()` normalizes all three, so this type stays
 * permissive rather than re-encoding that normalization in TS. */
export type K8sFaultClusterState = Record<string, unknown>;

// Real kubectl-`/apis/.../namespaces/<ns>/<kind>` API paths for every kind
// autofde-lab's `ClusterState` TypedDict recognizes -- the same
// `k8sRequest` primitive lib/k8s.ts's own `listDeployments`/`listPods`
// already use, called directly here (rather than through those
// functions) because the scanner needs the RAW kubectl-JSON list
// response (`{"items": [...]}`), not the narrower typed shapes those
// helpers project down to.
const CLUSTER_STATE_PATHS: Record<string, (namespace: string) => string> = {
  deployments: (ns) => `/apis/apps/v1/namespaces/${ns}/deployments`,
  pods: (ns) => `/api/v1/namespaces/${ns}/pods`,
  services: (ns) => `/api/v1/namespaces/${ns}/services`,
  persistentvolumeclaims: (ns) => `/api/v1/namespaces/${ns}/persistentvolumeclaims`,
  configmaps: (ns) => `/api/v1/namespaces/${ns}/configmaps`,
  serviceaccounts: (ns) => `/api/v1/namespaces/${ns}/serviceaccounts`,
  resourcequotas: (ns) => `/api/v1/namespaces/${ns}/resourcequotas`,
  limitranges: (ns) => `/api/v1/namespaces/${ns}/limitranges`,
  cronjobs: (ns) => `/apis/batch/v1/namespaces/${ns}/cronjobs`,
  ingresses: (ns) => `/apis/networking.k8s.io/v1/namespaces/${ns}/ingresses`,
};

/**
 * Assembles a real `K8sFaultClusterState` for one org's namespace by
 * issuing one real `k8sRequest` GET per recognized kind (same
 * namespace-scoping pattern `security-scan-auto-remediate.ts`'s
 * `listDeployments(org.namespace)` already uses) and keeping only the
 * kinds that actually returned data. A kind whose read fails (RBAC not
 * granted for it, transient API error) is dropped from the resulting
 * state rather than failing the whole collection -- the scanner's own
 * per-kind analyzers already tolerate a missing kind (an absent key
 * yields `[]` via `_items(None)`), so a partial cluster read still
 * produces real, if incomplete, findings instead of none at all.
 * Cluster-scoped kinds the scanner also recognizes
 * (clusterroles/clusterrolebindings/nodes) are intentionally omitted
 * here -- they are not namespace-scoped and this function is
 * deliberately namespace-scoped to match `Org.namespace`.
 */
export async function collectClusterStateForOrg(
  namespace: string,
): Promise<K8sFaultClusterState> {
  const state: K8sFaultClusterState = {};
  await Promise.all(
    Object.entries(CLUSTER_STATE_PATHS).map(async ([kind, pathFor]) => {
      const result = await k8sRequest<unknown>(pathFor(namespace));
      if (result.ok && result.data) {
        state[kind] = result.data;
      }
    }),
  );
  return state;
}

/**
 * True only when `AUTOFDE_LAB_PROJECT_DIR` looks like a real autofde-lab
 * checkout with the scanner CLI shim present -- same fail-closed-before-
 * attempting convention lib/mermaid.ts's `hasMmdio()` established, so
 * callers can report an honest "not configured" state instead of trying
 * and swallowing an ENOENT.
 */
export function hasK8sFaultScanner(): boolean {
  return (
    fs.existsSync(path.join(AUTOFDE_LAB_PROJECT_DIR, "pyproject.toml")) &&
    fs.existsSync(
      path.join(AUTOFDE_LAB_PROJECT_DIR, "src/autofde_lab_planner/scanner/__main__.py"),
    )
  );
}

/**
 * Shells out to the one, fixed, allowlisted invocation:
 * `<AUTOFDE_LAB_PYTHON> -m autofde_lab_planner.scanner --state-file
 * <tmpfile>`, from inside the autofde-lab checkout. `clusterState` is
 * written verbatim to a tmp JSON file (same pattern lib/mermaid.ts's
 * `renderFlowchart` uses for its own input) rather than passed as an
 * argv string, so no request-controlled text is ever interpolated into
 * the subprocess argv itself. Returns the real, parsed findings on
 * success, or the real stderr/parse error as `error` -- never a
 * fabricated finding on any failure path.
 */
export function runK8sFaultScan(
  clusterState: K8sFaultClusterState,
): K8sResult<K8sFaultFinding[]> {
  if (!hasK8sFaultScanner()) {
    return {
      ok: false,
      error: `not configured: no autofde-lab scanner CLI found at ${AUTOFDE_LAB_PROJECT_DIR} (set AUTOFDE_LAB_PROJECT_DIR)`,
    };
  }

  const tmpFile = path.join(
    os.tmpdir(),
    `k8s-fault-scan-${process.pid}-${Date.now()}.json`,
  );
  try {
    fs.writeFileSync(tmpFile, JSON.stringify(clusterState));

    const result = spawnSync(
      AUTOFDE_LAB_PYTHON,
      ["-m", "autofde_lab_planner.scanner", "--state-file", tmpFile],
      {
        cwd: AUTOFDE_LAB_PROJECT_DIR,
        timeout: SCAN_TIMEOUT_MS,
        encoding: "utf8",
      },
    );

    if (result.error) {
      return { ok: false, error: `k8s-fault-scan subprocess failed to start: ${result.error.message}` };
    }
    if (result.status !== 0) {
      const stderr = (result.stderr ?? "").trim();
      return {
        ok: false,
        error: `k8s-fault-scan exited ${result.status}${stderr ? `: ${stderr}` : ""}`,
      };
    }

    let parsed: unknown;
    try {
      parsed = JSON.parse(result.stdout);
    } catch (parseError) {
      return {
        ok: false,
        error: `k8s-fault-scan produced non-JSON stdout: ${(parseError as Error).message}`,
      };
    }

    if (!Array.isArray(parsed)) {
      return { ok: false, error: "k8s-fault-scan stdout was not a JSON array" };
    }

    return { ok: true, data: parsed as K8sFaultFinding[] };
  } catch (err) {
    return { ok: false, error: `k8s-fault-scan failed: ${(err as Error).message}` };
  } finally {
    try {
      fs.unlinkSync(tmpFile);
    } catch {
      // best-effort cleanup only
    }
  }
}
