#!/usr/bin/env bash
# Enables real etcd-at-rest encryption for Kubernetes Secrets on
# kind-platform-eng-colima, closing the Secrets-at-rest-encryption
# IaaS gap: base64 in etcd (Opaque Secrets' default) is NOT encryption --
# it round-trips with `base64 -d`, and a plaintext-secrets breach is
# exactly the posture Sony's own 2014 breach was defined by. This script
# is the reproducible record of the live change made directly against
# the running platform-eng-colima-control-plane container (kind clusters
# have no persistent kubeadm config file this repo tracks -- kind-config.yaml
# only covers node/port topology, so this script -- not kind-config.yaml --
# is the reproducibility artifact for this control, same convention
# services/vuln-scanner/load-trivy-scanner-image.sh already establishes for
# a different real, live, node-level mutation).
#
# Uses Kubernetes' own native EncryptionConfiguration
# (apiserver.config.k8s.io/v1, aescbc provider) -- no third-party KMS
# plugin or sealed-secrets controller was installed; aescbc is the
# real, built-in, non-network-dependent envelope-encryption provider
# every kubeadm-based cluster ships support for, and is honestly disclosed
# below as static-key (not a rotating remote KMS) -- see the control's
# evidence-bundle entry for the full honest scope statement.
#
# Idempotent: re-running after the config already exists leaves the
# existing key in place (does not generate or install a fresh key over
# a live cluster's real data, which would make already-encrypted objects
# unreadable) and just re-applies the apiserver flag if missing.
set -euo pipefail

KIND_NODE="${KIND_NODE:-platform-eng-colima-control-plane}"
CONFIG_DIR="/etc/kubernetes/pki/encryption"
CONFIG_PATH="${CONFIG_DIR}/encryption-config.yaml"
MANIFEST_PATH="/etc/kubernetes/manifests/kube-apiserver.yaml"

echo "==> checking for existing EncryptionConfiguration on ${KIND_NODE}"
if docker exec "${KIND_NODE}" test -f "${CONFIG_PATH}"; then
  echo "    already present -- leaving existing key in place (idempotent)"
else
  echo "==> generating a fresh real AES-256 key (openssl rand -base64 32, never logged)"
  KEY="$(openssl rand -base64 32)"
  docker exec "${KIND_NODE}" mkdir -p "${CONFIG_DIR}"
  TMP_CFG="$(mktemp -t encryption-config-XXXXXX.yaml)"
  trap 'rm -f "${TMP_CFG}"' EXIT
  cat > "${TMP_CFG}" <<EOF
apiVersion: apiserver.config.k8s.io/v1
kind: EncryptionConfiguration
resources:
  - resources:
      - secrets
    providers:
      - aescbc:
          keys:
            - name: key1
              secret: ${KEY}
      - identity: {}
EOF
  docker cp "${TMP_CFG}" "${KIND_NODE}:${CONFIG_PATH}"
  docker exec "${KIND_NODE}" chmod 600 "${CONFIG_PATH}"
  echo "    wrote ${CONFIG_PATH} on ${KIND_NODE}, mode 600"
fi

echo "==> checking kube-apiserver static pod manifest for --encryption-provider-config"
if docker exec "${KIND_NODE}" grep -q -- "--encryption-provider-config=${CONFIG_PATH}" "${MANIFEST_PATH}"; then
  echo "    flag already present"
else
  echo "==> patching ${MANIFEST_PATH} to add the flag (kubelet's static-pod controller"
  echo "    picks up the change and restarts kube-apiserver automatically)"
  docker exec "${KIND_NODE}" sed -i \
    "s#- --etcd-servers=https://127.0.0.1:2379#- --encryption-provider-config=${CONFIG_PATH}\n    - --etcd-servers=https://127.0.0.1:2379#" \
    "${MANIFEST_PATH}"
fi

echo "==> waiting for kube-apiserver to come back Running with the new flag"
for _ in $(seq 1 40); do
  PHASE="$(kubectl get pod -n kube-system "kube-apiserver-${KIND_NODE}" -o jsonpath='{.status.phase}' 2>/dev/null || true)"
  if [ "${PHASE}" = "Running" ]; then
    echo "    kube-apiserver Running"
    break
  fi
  sleep 3
done

echo "==> re-writing every existing Secret through the API server so identity-encoded"
echo "    (pre-existing) objects are re-saved as real aescbc ciphertext, not left plaintext"
TMP_SECRETS="$(mktemp -t all-secrets-XXXXXX.json)"
trap 'rm -f "${TMP_SECRETS}"' EXIT
kubectl get secrets --all-namespaces -o json > "${TMP_SECRETS}"
kubectl replace -f "${TMP_SECRETS}"

echo "==> done. Verify with: infra/verify-etcd-encryption.sh <namespace> <secret-name>"
