#!/usr/bin/env bash
# Dumps the raw etcd bytes for one Secret and confirms it is real aescbc
# ciphertext (the `k8s:enc:aescbc:v1:key1:` envelope prefix, no readable
# key names or values), not base64-only plaintext. Companion to
# enable-etcd-encryption.sh -- this is the check that actually earns the
# claim, not a re-statement of the config.
set -euo pipefail

NAMESPACE="${1:?usage: verify-etcd-encryption.sh <namespace> <secret-name>}"
NAME="${2:?usage: verify-etcd-encryption.sh <namespace> <secret-name>}"
KIND_NODE="${KIND_NODE:-platform-eng-colima-control-plane}"

echo "==> raw etcd bytes for /registry/secrets/${NAMESPACE}/${NAME}"
kubectl exec -n kube-system "etcd-${KIND_NODE}" -- etcdctl \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key \
  --endpoints=https://127.0.0.1:2379 \
  get "/registry/secrets/${NAMESPACE}/${NAME}" | xxd | head -5

echo
echo "==> checking the real decoded key names/values from the k8s API are absent from the raw bytes"
kubectl exec -n kube-system "etcd-${KIND_NODE}" -- etcdctl \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key \
  --endpoints=https://127.0.0.1:2379 \
  get "/registry/secrets/${NAMESPACE}/${NAME}" > /tmp/etcd-raw-dump.$$.bin

kubectl get secret -n "${NAMESPACE}" "${NAME}" -o json > /tmp/secret-decoded.$$.json

python3 <<PYEOF
import json, base64

raw = open("/tmp/etcd-raw-dump.$$.bin", "rb").read()
doc = json.load(open("/tmp/secret-decoded.$$.json"))

prefix_ok = b"k8s:enc:aescbc:v1:" in raw
leaks = []
for key, val in doc.get("data", {}).items():
    if key.encode() in raw:
        leaks.append(("key-name", key))
    decoded = base64.b64decode(val)
    if len(decoded) >= 8 and decoded in raw:
        leaks.append(("value", key))

print(f"envelope prefix present: {prefix_ok}")
print(f"plaintext leaks found:   {leaks if leaks else 'none'}")
print("RESULT:", "CIPHERTEXT CONFIRMED" if prefix_ok and not leaks else "NOT CONFIRMED -- investigate")
PYEOF

rm -f /tmp/etcd-raw-dump.$$.bin /tmp/secret-decoded.$$.json
