# Platform Engineer's Handbook — E2E Test Suite

Real Playwright end-to-end tests against the live `kind-platform-eng-colima` cluster's
monitoring stack and demo application. No mocked HTTP, no fixture servers — every test
drives a real browser against a real port-forwarded service.

## What this suite tests (5 JTBDs)

1. **Grafana** — log in and view a live dashboard with real data
   (`tests/grafana.spec.ts`)
2. **Prometheus** — run a PromQL query in the web UI and see real results
   (`tests/prometheus.spec.ts`)
3. **Alertmanager** — view active alerts in the web UI
   (`tests/alertmanager-demoapp.spec.ts`)
4. **Demo app `/health`** — responds to a real browser request
   (`tests/alertmanager-demoapp.spec.ts`)
5. **Demo app `/items`** — renders real JSON in a browser
   (`tests/alertmanager-demoapp.spec.ts`)

## Prerequisites

1. The `kind-platform-eng-colima` cluster must be running (see
   [`docs/platform-engineers-handbook-colima-runtime.md`](../../../docs/platform-engineers-handbook-colima-runtime.md)).
2. Docker/kubectl context pointed at it:
   ```bash
   docker context use colima
   kubectl config use-context kind-platform-eng-colima
   ```
3. The four services port-forwarded to the ports `playwright.config.ts` expects
   (run each in the background, one per service):
   ```bash
   kubectl port-forward -n monitoring svc/monitoring-grafana 18300:80 --context kind-platform-eng-colima &
   kubectl port-forward -n monitoring svc/monitoring-kube-prometheus-prometheus 18301:9090 --context kind-platform-eng-colima &
   kubectl port-forward -n monitoring svc/monitoring-kube-prometheus-alertmanager 18302:9093 --context kind-platform-eng-colima &
   kubectl port-forward -n application svc/platform-demo-app 18303:80 --context kind-platform-eng-colima &
   ```
4. `npm install` in this directory (installs `@playwright/test` and its browser binaries).

## Running the suite

```bash
npx playwright test
```

Expected: `5 passed`.
