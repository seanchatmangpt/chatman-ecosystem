import { defineConfig } from '@playwright/test';

// Base URLs for the four live services on the running kind-platform-eng-colima cluster.
// Establish these port-forwards before running the suite (see README.md):
//   kubectl port-forward -n monitoring svc/monitoring-grafana 18300:80
//   kubectl port-forward -n monitoring svc/monitoring-kube-prometheus-prometheus 18301:9090
//   kubectl port-forward -n monitoring svc/monitoring-kube-prometheus-alertmanager 18302:9093
//   kubectl port-forward -n application svc/platform-demo-app 18303:80
export const GRAFANA_URL = 'http://localhost:18300';
export const PROMETHEUS_URL = 'http://localhost:18301';
export const ALERTMANAGER_URL = 'http://localhost:18302';
export const DEMO_APP_URL = 'http://localhost:18303';

export default defineConfig({
  testDir: './tests',
  fullyParallel: true,
  reporter: 'list',
  use: {
    screenshot: 'only-on-failure',
  },
});
