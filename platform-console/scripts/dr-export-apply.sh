#!/usr/bin/env bash
# dr-export-apply.sh
#
# Cold-standby DR helper: exports the platform-console namespace's live
# resource manifests from the primary kind cluster and applies them to a
# separate, independent kind cluster (the DR target).
#
# This is NOT live replication and does NOT provide HA or automatic failover.
# It is a manual, point-in-time snapshot-and-apply operation you run by hand.
# See platform-console/docs/DR-SECOND-CLUSTER.md for exactly what this does
# and does not provide.
set -euo pipefail

PRIMARY_CONTEXT="${PRIMARY_CONTEXT:-kind-platform-eng-colima}"
DR_CONTEXT="${DR_CONTEXT:-kind-platform-eng-colima-dr}"
NAMESPACE="${NAMESPACE:-platform-console}"
OUT_DIR="${OUT_DIR:-/tmp/platform-console-dr-export}"

echo "== DR export/apply =="
echo "primary context: $PRIMARY_CONTEXT"
echo "dr context:      $DR_CONTEXT"
echo "namespace:        $NAMESPACE"

echo
echo "-- verifying both clusters are reachable --"
kubectl --context "$PRIMARY_CONTEXT" get nodes >/dev/null
echo "primary reachable: OK"
kubectl --context "$DR_CONTEXT" get nodes >/dev/null
echo "dr reachable: OK"

rm -rf "$OUT_DIR"
mkdir -p "$OUT_DIR"

echo
echo "-- exporting live resources from primary namespace '$NAMESPACE' --"
RESOURCE_KINDS="deployment,service,configmap,secret,serviceaccount,role,rolebinding,networkpolicy,horizontalpodautoscaler,poddisruptionbudget"

kubectl --context "$PRIMARY_CONTEXT" get namespace "$NAMESPACE" -o yaml \
  | kubectl neat 2>/dev/null > "$OUT_DIR/00-namespace.yaml" \
  || kubectl --context "$PRIMARY_CONTEXT" get namespace "$NAMESPACE" -o yaml > "$OUT_DIR/00-namespace.yaml"

kubectl --context "$PRIMARY_CONTEXT" get "$RESOURCE_KINDS" -n "$NAMESPACE" -o yaml \
  > "$OUT_DIR/01-resources.yaml.raw"

# kube-root-ca.crt and the "default" serviceaccount are auto-created by
# Kubernetes itself whenever a namespace is created, so the DR cluster
# already has its own copies. Applying the primary's copies over them races
# with the DR cluster's own controller and fails with a resourceVersion
# conflict. Strip those two auto-managed built-ins from the export.
python3 - "$OUT_DIR/01-resources.yaml.raw" "$OUT_DIR/01-resources.yaml" <<'PY'
import sys, yaml
src, dst = sys.argv[1], sys.argv[2]
doc = yaml.safe_load(open(src))
items = doc.get("items", [])
skip = {("ConfigMap", "kube-root-ca.crt"), ("ServiceAccount", "default")}
doc["items"] = [i for i in items if (i.get("kind"), i.get("metadata", {}).get("name")) not in skip]
yaml.safe_dump(doc, open(dst, "w"))
PY
rm -f "$OUT_DIR/01-resources.yaml.raw"

echo "exported to: $OUT_DIR"
ls -la "$OUT_DIR"

echo
echo "-- applying exported manifests to DR cluster --"
kubectl --context "$DR_CONTEXT" apply -f "$OUT_DIR/00-namespace.yaml"
kubectl --context "$DR_CONTEXT" apply -f "$OUT_DIR/01-resources.yaml"

echo
echo "-- verifying DR cluster now has the namespace and resources --"
kubectl --context "$DR_CONTEXT" get all -n "$NAMESPACE"

echo
echo "== DONE =="
echo "This applied a point-in-time COLD-STANDBY copy of $NAMESPACE to $DR_CONTEXT."
echo "It is not live-replicated, not HA, and there is no automatic failover."
